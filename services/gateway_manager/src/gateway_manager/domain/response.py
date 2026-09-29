from dataclasses import dataclass

from .token_usage import TokenUsage


@dataclass(slots=True)
class Response:
    model: str
    provider: str
    content: str
    usage: TokenUsage | None = None
    finish_reason: str | None = None
    latency_ms: int | None = None