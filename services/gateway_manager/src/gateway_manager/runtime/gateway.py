from dataclasses import replace
from pathlib import Path
from time import perf_counter

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
from gateway_manager.pricing import PricingService
from gateway_manager.providers import get as get_provider
from gateway_manager.registry.model_registry import ModelRegistry
from gateway_manager.routing import FallbackRouter
from gateway_manager.usage import (
    SQLiteUsageRepository,
    UsageRecord,
    UsageRepository,
)


def find_lab_root(start: Path) -> Path:
    current = start.resolve()

    while current != current.parent:
        if (current / "lab.yaml").exists():
            return current

        current = current.parent

    raise RuntimeError(
        "No se encontró la raíz del LAB (lab.yaml)"
    )


LAB_ROOT = find_lab_root(Path(__file__))

DEFAULT_USAGE_DB = (
    LAB_ROOT
    / "runtime"
    / "gateway"
    / "usage.db"
)


class Gateway:

    def __init__(
        self,
        usage_repository: UsageRepository | None = None,
        pricing_service: PricingService | None = None,
    ):
        self.registry = ModelRegistry.load()
        self.availability = ProviderAvailability()

        self.router = FallbackRouter(
            registry=self.registry,
            availability=self.availability,
        )

        self.litellm_adapter = LiteLLMAdapter()
        self.ollama_adapter = OllamaAdapter()

        self.usage_repository = (
            usage_repository
            or SQLiteUsageRepository(
                DEFAULT_USAGE_DB
            )
        )

        self.pricing_service = (
            pricing_service
            or PricingService()
        )

    def complete(
        self,
        request: Request,
    ) -> Response:

        if request.model is not None:
            model = self.registry.get(
                request.model
            )

            if model is None:
                raise RuntimeError(
                    f"Unknown model: {request.model}"
                )

            return self._execute(
                model=model,
                request=request,
                fallback=False,
            )

        capability = (
            request.capability
            or "chat"
        )

        candidates = self.router.route(
            capability
        )

        if not candidates:
            raise RuntimeError(
                "No available models for "
                f"capability: {capability}"
            )

        max_attempts = (
            self.router.max_attempts()
        )

        errors: list[str] = []

        for index, model in enumerate(
            candidates[:max_attempts]
        ):
            fallback = index > 0

            try:
                return self._execute(
                    model=model,
                    request=request,
                    fallback=fallback,
                )

            except Exception as exc:
                if not self._is_retryable(
                    exc
                ):
                    raise

                errors.append(
                    f"{model.name}: "
                    f"{type(exc).__name__}: "
                    f"{exc}"
                )

        attempted = ", ".join(
            model.name
            for model
            in candidates[:max_attempts]
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
        fallback: bool,
    ) -> Response:

        started = perf_counter()

        try:
            provider = get_provider(
                model.provider
            )

            if provider is None:
                raise RuntimeError(
                    "Unknown provider: "
                    f"{model.provider}"
                )

            execution_request = request

            if (
                model.provider == "ollama"
                and request.think is None
            ):
                execution_request = replace(
                    request,
                    think=False,
                )

            if model.provider == "ollama":
                provider_response = (
                    self.ollama_adapter.complete(
                        model.provider_model,
                        execution_request,
                    )
                )

            else:
                provider_response = (
                    self.litellm_adapter.complete(
                        provider.build_model_name(
                            model.provider_model
                        ),
                        execution_request,
                    )
                )

        except Exception as exc:
            latency_ms = int(
                (
                    perf_counter()
                    - started
                )
                * 1000
            )

            self._record_failure(
                model=model,
                request=request,
                fallback=fallback,
                latency_ms=latency_ms,
                exc=exc,
            )

            raise

        latency_ms = int(
            (
                perf_counter()
                - started
            )
            * 1000
        )

        usage = None

        if (
            provider_response.total_tokens
            is not None
        ):
            usage = TokenUsage(
                prompt_tokens=(
                    provider_response
                    .prompt_tokens
                    or 0
                ),
                completion_tokens=(
                    provider_response
                    .completion_tokens
                    or 0
                ),
                total_tokens=(
                    provider_response
                    .total_tokens
                ),
            )

        response = Response(
            model=model.name,
            provider=model.provider,
            content=(
                provider_response.content
            ),
            usage=usage,
            finish_reason=(
                provider_response
                .finish_reason
            ),
            latency_ms=latency_ms,
        )

        self._record_success(
            model=model,
            request=request,
            response=response,
            fallback=fallback,
        )

        return response

    def _record_success(
        self,
        model: Model,
        request: Request,
        response: Response,
        fallback: bool,
    ) -> None:

        prompt_tokens = 0
        completion_tokens = 0
        total_tokens = 0

        if response.usage is not None:
            prompt_tokens = (
                response.usage.prompt_tokens
            )

            completion_tokens = (
                response
                .usage
                .completion_tokens
            )

            total_tokens = (
                response.usage.total_tokens
            )

        cost_eur = (
            self.pricing_service
            .calculate_cost_eur(
                model_name=model.name,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
            )
        )

        record = UsageRecord.create(
            provider=model.provider,
            model=model.name,
            prompt_tokens=prompt_tokens,
            completion_tokens=(
                completion_tokens
            ),
            total_tokens=total_tokens,
            cost_eur=cost_eur,
            latency_ms=(
                response.latency_ms
            ),
            capability=(
                request.capability
                or "chat"
            ),
            project=request.project,
            tenant=request.tenant,
            success=True,
            fallback=fallback,
        )

        self.usage_repository.add(
            record
        )

    def _record_failure(
        self,
        model: Model,
        request: Request,
        fallback: bool,
        latency_ms: int,
        exc: Exception,
    ) -> None:

        record = UsageRecord.create(
            provider=model.provider,
            model=model.name,
            latency_ms=latency_ms,
            capability=(
                request.capability
                or "chat"
            ),
            project=request.project,
            tenant=request.tenant,
            success=False,
            fallback=fallback,
            error_type=(
                type(exc).__name__
            ),
        )

        self.usage_repository.add(
            record
        )

    @staticmethod
    def _is_retryable(
        exc: Exception,
    ) -> bool:

        if isinstance(
            exc,
            (
                httpx.TimeoutException,
                httpx.ConnectError,
            ),
        ):
            return True

        if isinstance(
            exc,
            httpx.HTTPStatusError,
        ):
            status = (
                exc.response.status_code
            )

            return (
                status
                in {
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

        status = getattr(
            exc,
            "status_code",
            None,
        )

        if isinstance(status, int):
            if (
                status
                in {
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
            for marker
            in retryable_markers
        )
