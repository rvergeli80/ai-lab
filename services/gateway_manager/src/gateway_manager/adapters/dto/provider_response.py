from dataclasses import dataclass


@dataclass(slots=True)
class ProviderResponse:
    content: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    finish_reason: str | None = None