from dataclasses import dataclass


@dataclass(slots=True)
class Request:
    prompt: str
    capability: str | None = None
    tag: str | None = None
    model: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    think: bool | None = None
