import os

import httpx

from gateway_manager.adapters.dto import ProviderResponse
from gateway_manager.domain import Request

from .base import LLMAdapter


class OllamaAdapter(LLMAdapter):

    def __init__(self) -> None:
        self.base_url = os.getenv(
            "OLLAMA_HOST",
            "http://localhost:11434",
        ).rstrip("/")

    def complete(
        self,
        model_name: str,
        request: Request,
    ) -> ProviderResponse:

        payload = {
            "model": model_name,
            "messages": [
                {
                    "role": "user",
                    "content": request.prompt,
                }
            ],
            "stream": False,
            "keep_alive": "30m",
        }

        if request.think is not None:
            payload["think"] = request.think

        options = {}

        if request.temperature is not None:
            options["temperature"] = request.temperature

        if request.max_tokens is not None:
            options["num_predict"] = request.max_tokens

        if options:
            payload["options"] = options

        response = httpx.post(
            f"{self.base_url}/api/chat",
            json=payload,
            timeout=600,
        )

        response.raise_for_status()

        data = response.json()

        prompt_tokens = data.get("prompt_eval_count")
        completion_tokens = data.get("eval_count")

        total_tokens = None

        if (
            prompt_tokens is not None
            and completion_tokens is not None
        ):
            total_tokens = prompt_tokens + completion_tokens

        return ProviderResponse(
            content=data["message"]["content"],
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            finish_reason=data.get("done_reason"),
        )
