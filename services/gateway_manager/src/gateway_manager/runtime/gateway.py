from dataclasses import replace

import httpx

from gateway_manager.adapters import (
    LiteLLMAdapter,
    OllamaAdapter,
)
from gateway_manager.availability import ProviderAvailability
from gateway_manager.domain import (
    Model,
    Request,
    Response,
    TokenUsage,
)
from gateway_manager.providers import get as get_provider
from gateway_manager.registry.model_registry import ModelRegistry
from gateway_manager.routing import FallbackRouter


class Gateway:

    def __init__(self):
        self.registry = ModelRegistry.load()
        self.availability = ProviderAvailability()

        self.router = FallbackRouter(
            registry=self.registry,
            availability=self.availability,
        )

        self.litellm_adapter = LiteLLMAdapter()
        self.ollama_adapter = OllamaAdapter()

    def complete(
        self,
        request: Request,
    ) -> Response:

        # Modelo solicitado explícitamente: no hacemos routing.
        if request.model is not None:
            model = self.registry.get(request.model)

            if model is None:
                raise RuntimeError(
                    f"Unknown model: {request.model}"
                )

            return self._execute(
                model=model,
                request=request,
            )

        capability = request.capability or "chat"

        candidates = self.router.route(capability)

        if not candidates:
            raise RuntimeError(
                f"No available models for capability: {capability}"
            )

        max_attempts = self.router.max_attempts()

        errors: list[str] = []

        for model in candidates[:max_attempts]:

            try:
                return self._execute(
                    model=model,
                    request=request,
                )

            except Exception as exc:
                if not self._is_retryable(exc):
                    raise

                errors.append(
                    f"{model.name}: {type(exc).__name__}: {exc}"
                )

        attempted = ", ".join(
            model.name
            for model in candidates[:max_attempts]
        )

        raise RuntimeError(
            "All fallback models failed. "
            f"Attempted: {attempted}. "
            f"Errors: {' | '.join(errors)}"
        )

    def _execute(
        self,
        model: Model,
        request: Request,
    ) -> Response:

        provider = get_provider(model.provider)

        if provider is None:
            raise RuntimeError(
                f"Unknown provider: {model.provider}"
            )

        execution_request = request

        # Los modelos Ollama de fallback deben ser rápidos
        # salvo que el caller solicite thinking explícitamente.
        if (
            model.provider == "ollama"
            and request.think is None
        ):
            execution_request = replace(
                request,
                think=False,
            )

        if model.provider == "ollama":
            provider_response = self.ollama_adapter.complete(
                model.provider_model,
                execution_request,
            )
        else:
            provider_response = self.litellm_adapter.complete(
                provider.build_model_name(
                    model.provider_model
                ),
                execution_request,
            )

        usage = None

        if provider_response.total_tokens is not None:
            usage = TokenUsage(
                prompt_tokens=provider_response.prompt_tokens or 0,
                completion_tokens=provider_response.completion_tokens or 0,
                total_tokens=provider_response.total_tokens,
            )

        return Response(
            model=model.name,
            provider=model.provider,
            content=provider_response.content,
            usage=usage,
            finish_reason=provider_response.finish_reason,
        )

    @staticmethod
    def _is_retryable(exc: Exception) -> bool:

        if isinstance(
            exc,
            (
                httpx.TimeoutException,
                httpx.ConnectError,
            ),
        ):
            return True

        if isinstance(exc, httpx.HTTPStatusError):
            status = exc.response.status_code

            return (
                status in {
                    401,
                    402,
                    403,
                    408,
                    409,
                    425,
                    429,
                }
                or status >= 500
            )

        status = getattr(exc, "status_code", None)

        if isinstance(status, int):
            if (
                status in {
                    401,
                    402,
                    403,
                    408,
                    409,
                    425,
                    429,
                }
                or status >= 500
            ):
                return True

        message = str(exc).lower()

        retryable_markers = (
            "rate limit",
            "quota",
            "timeout",
            "timed out",
            "service unavailable",
            "provider unavailable",
            "model unavailable",
            "connection error",
            "connection refused",
            "insufficient credits",
        )

        return any(
            marker in message
            for marker in retryable_markers
        )
