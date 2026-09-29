from litellm import completion

from gateway_manager.adapters.dto import ProviderResponse
from gateway_manager.domain import Request

from .base import LLMAdapter


class LiteLLMAdapter(LLMAdapter):

    def complete(
        self,
        model_name: str,
        request: Request,
    ) -> ProviderResponse:

        kwargs = {
            "model": model_name,
            "messages": [
                {
                    "role": "user",
                    "content": request.prompt,
                }
            ],
        }

        if request.temperature is not None:
            kwargs["temperature"] = request.temperature

        if request.max_tokens is not None:
            kwargs["max_tokens"] = request.max_tokens

        result = completion(**kwargs)

        usage = getattr(result, "usage", None)

        return ProviderResponse(
            content=result.choices[0].message.content,
            prompt_tokens=getattr(usage, "prompt_tokens", None),
            completion_tokens=getattr(
                usage,
                "completion_tokens",
                None,
            ),
            total_tokens=getattr(
                usage,
                "total_tokens",
                None,
            ),
            finish_reason=result.choices[0].finish_reason,
        )