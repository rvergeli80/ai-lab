from datetime import (
    datetime,
    timezone,
)
from pathlib import Path

from gateway_manager.usage import (
    SQLiteUsageRepository,
    UsageRepository,
)


def find_lab_root(
    start: Path,
) -> Path:

    current = start.resolve()

    while current != current.parent:
        if (current / "lab.yaml").exists():
            return current

        current = current.parent

    raise RuntimeError(
        "No se encontró la raíz del LAB (lab.yaml)"
    )


LAB_ROOT = find_lab_root(
    Path(__file__)
)

DEFAULT_USAGE_DB = (
    LAB_ROOT
    / "runtime"
    / "gateway"
    / "usage.db"
)


def _period_start(
    period: str,
    now: datetime,
) -> datetime:

    if period == "today":
        return now.replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

    if period == "month":
        return now.replace(
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

    raise ValueError(
        f"Unknown period: {period}"
    )


def _print_summary(
    *,
    title: str,
    repository: UsageRepository,
    start: datetime,
    end: datetime,
) -> None:

    records = repository.list_between(
        start,
        end,
    )

    requests = len(records)

    successful = sum(
        1
        for record in records
        if record.success
    )

    failed = requests - successful

    fallbacks = sum(
        1
        for record in records
        if record.fallback
    )

    prompt_tokens = sum(
        record.prompt_tokens
        for record in records
    )

    completion_tokens = sum(
        record.completion_tokens
        for record in records
    )

    total_tokens = sum(
        record.total_tokens
        for record in records
    )

    costs: dict[str, float] = {}

    unknown_costs = 0

    for record in records:

        if record.cost_amount is None:
            if record.success:
                unknown_costs += 1
            continue

        if record.cost_currency is None:
            unknown_costs += 1
            continue

        costs.setdefault(
            record.cost_currency,
            0.0,
        )

        costs[
            record.cost_currency
        ] += record.cost_amount

    print()
    print(title)
    print("-" * 40)

    print(
        f"{'requests':<20} {requests}"
    )
    print(
        f"{'successful':<20} {successful}"
    )
    print(
        f"{'failed':<20} {failed}"
    )
    print(
        f"{'fallbacks':<20} {fallbacks}"
    )

    print(
        f"{'prompt tokens':<20} "
        f"{prompt_tokens}"
    )

    print(
        f"{'completion tokens':<20} "
        f"{completion_tokens}"
    )

    print(
        f"{'total tokens':<20} "
        f"{total_tokens}"
    )

    if costs:
        for currency, amount in sorted(
            costs.items()
        ):
            print(
                f"{'cost ' + currency:<20} "
                f"{amount:.6f}"
            )
    else:
        print(
            f"{'cost':<20} 0"
        )

    if unknown_costs:
        print(
            f"{'unknown costs':<20} "
            f"{unknown_costs}"
        )


def run(
    repository: UsageRepository | None = None,
) -> None:

    repository = (
        repository
        or SQLiteUsageRepository(
            DEFAULT_USAGE_DB
        )
    )

    now = datetime.now(
        timezone.utc
    )

    print()
    print("Gateway Usage")
    print("=" * 60)

    _print_summary(
        title="Today",
        repository=repository,
        start=_period_start(
            "today",
            now,
        ),
        end=now,
    )

    _print_summary(
        title="Month",
        repository=repository,
        start=_period_start(
            "month",
            now,
        ),
        end=now,
    )

    print()
