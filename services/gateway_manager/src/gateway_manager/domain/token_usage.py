from dataclasses import dataclass


@dataclass(slots=True)
class TokenUsage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int