from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class UsageRecord:
    id: str
    timestamp: datetime
    provider: str
    model: str

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

    cost_amount: float | None = None
    cost_currency: str | None = None

    latency_ms: int | None = None

    capability: str | None = None
    project: str | None = None
    tenant: str | None = None

    success: bool = True
    fallback: bool = False
    error_type: str | None = None

    @classmethod
    def create(
        cls,
        *,
        provider: str,
        model: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_tokens: int = 0,
        cost_amount: float | None = None,
        cost_currency: str | None = None,
        latency_ms: int | None = None,
        capability: str | None = None,
        project: str | None = None,
        tenant: str | None = None,
        success: bool = True,
        fallback: bool = False,
        error_type: str | None = None,
    ) -> "UsageRecord":
        return cls(
            id=str(uuid4()),
            timestamp=datetime.now(timezone.utc),
            provider=provider,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost_amount=cost_amount,
            cost_currency=cost_currency,
            latency_ms=latency_ms,
            capability=capability,
            project=project,
            tenant=tenant,
            success=success,
            fallback=fallback,
            error_type=error_type,
        )
