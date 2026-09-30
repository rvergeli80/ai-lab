from datetime import (
    datetime,
    timezone,
)
from pathlib import Path

from gateway_manager.availability import (
    ProviderAvailability,
)
from gateway_manager.budget import BudgetPolicy
from gateway_manager.catalog import CatalogLoader
from gateway_manager.pricing import PricingCatalog
from gateway_manager.providers import PROVIDERS
from gateway_manager.registry.model_registry import (
    ModelRegistry,
)
from gateway_manager.routing import PolicyLoader
from gateway_manager.usage import (
    SQLiteUsageRepository,
)
from gateway_manager.validation import (
    GatewayConfigValidator,
)


def find_lab_root(
    start: Path,
) -> Path:

    current = start.resolve()

    while current != current.parent:

        if (
            current
            / "lab.yaml"
        ).exists():
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


class GatewayDoctor:

    @classmethod
    def run(
        cls,
    ) -> int:

        print()
        print("Nevermine Gateway Doctor")
        print("=" * 60)

        checks: list[
            tuple[str, bool, str]
        ] = []

        registry = None
        budget = None
        repository = None

        try:
            CatalogLoader.load()

            checks.append(
                (
                    "model catalog",
                    True,
                    "OK",
                )
            )

        except Exception as exc:

            checks.append(
                (
                    "model catalog",
                    False,
                    str(exc),
                )
            )

        try:
            registry = ModelRegistry.load()

            checks.append(
                (
                    "model registry",
                    True,
                    (
                        f"{len(registry.list_enabled())} "
                        "enabled models"
                    ),
                )
            )

        except Exception as exc:

            checks.append(
                (
                    "model registry",
                    False,
                    str(exc),
                )
            )

        try:
            policies = PolicyLoader.load()

            policy_count = len(
                policies.get(
                    "policies",
                    {},
                )
            )

            checks.append(
                (
                    "routing policies",
                    True,
                    f"{policy_count} capabilities",
                )
            )

        except Exception as exc:

            checks.append(
                (
                    "routing policies",
                    False,
                    str(exc),
                )
            )

        try:
            PricingCatalog()

            checks.append(
                (
                    "pricing catalog",
                    True,
                    "OK",
                )
            )

        except Exception as exc:

            checks.append(
                (
                    "pricing catalog",
                    False,
                    str(exc),
                )
            )

        try:
            repository = (
                SQLiteUsageRepository(
                    DEFAULT_USAGE_DB
                )
            )

            now = datetime.now(
                timezone.utc
            )

            repository.list_between(
                now,
                now,
            )

            checks.append(
                (
                    "usage ledger",
                    True,
                    str(DEFAULT_USAGE_DB),
                )
            )

        except Exception as exc:

            repository = None

            checks.append(
                (
                    "usage ledger",
                    False,
                    str(exc),
                )
            )

        try:
            budget = BudgetPolicy(
                usage_repository=(
                    repository
                )
                if repository
                is not None
                else None
            )

            currency = (
                budget.config
                .get("budget", {})
                .get(
                    "currency",
                    "USD",
                )
            )

            checks.append(
                (
                    "budget policy",
                    True,
                    currency,
                )
            )

        except Exception as exc:

            checks.append(
                (
                    "budget policy",
                    False,
                    str(exc),
                )
            )

        print()
        print("Components")
        print("-" * 60)

        for (
            name,
            success,
            detail,
        ) in checks:

            status = (
                "OK"
                if success
                else "ERROR"
            )

            print(
                f"{name:<20} "
                f"{status:<10} "
                f"{detail}"
            )

        print()
        print(
            "Configuration validation"
        )
        print("-" * 60)

        try:

            validation = (
                GatewayConfigValidator
                .validate()
            )

            print(
                f"{'errors':<20} "
                f"{len(validation.errors)}"
            )

            print(
                f"{'warnings':<20} "
                f"{len(validation.warnings)}"
            )

            for issue in (
                validation.issues
            ):

                print(
                    f"{issue.severity:<10} "
                    f"{issue.code:<28} "
                    f"{issue.message}"
                )

            if validation.valid:
                print(
                    f"{'status':<20} VALID"
                )

            else:
                print(
                    f"{'status':<20} INVALID"
                )

        except Exception as exc:

            validation = None

            print(
                f"{'status':<20} ERROR"
            )

            print(
                f"{'detail':<20} {exc}"
            )

        availability = (
            ProviderAvailability()
        )

        try:
            available = (
                availability.available()
            )

        except Exception:
            available = set()

        print()
        print("Providers")
        print("-" * 60)

        for name in PROVIDERS:

            if name in available:
                status = "AVAILABLE"

            elif name == "ollama":
                status = "UNAVAILABLE"

            else:
                status = "NO CREDENTIALS"

            print(
                f"{name:<20} {status}"
            )

        if registry is not None:

            print()
            print("Models")
            print("-" * 60)

            for model in (
                registry
                .list_enabled()
                .values()
            ):

                provider_status = (
                    "AVAILABLE"
                    if model.provider
                    in available
                    else "UNAVAILABLE"
                )

                print(
                    f"{model.name:<25} "
                    f"{model.provider:<15} "
                    f"{provider_status}"
                )

        if budget is not None:

            budget_config = (
                budget.config.get(
                    "budget",
                    {},
                )
            )

            defaults = (
                budget_config.get(
                    "default",
                    {},
                )
            )

            currency = (
                budget_config.get(
                    "currency",
                    "USD",
                )
            )

            print()
            print("Budget")
            print("-" * 60)

            print(
                f"{'currency':<20} "
                f"{currency}"
            )

            print(
                f"{'daily limit':<20} "
                f"{defaults.get('daily', 0)}"
            )

            print(
                f"{'monthly limit':<20} "
                f"{defaults.get('monthly', 0)}"
            )

        components_ok = all(
            success
            for _, success, _ in checks
        )

        configuration_ok = (
            validation is not None
            and validation.valid
        )

        runtime_ok = bool(
            available
        )

        print()
        print("Result")
        print("-" * 60)

        if (
            components_ok
            and configuration_ok
            and runtime_ok
        ):

            print("HEALTHY")
            print()

            return 0

        if (
            components_ok
            and configuration_ok
        ):

            print(
                "DEGRADED "
                "(configuration valid, "
                "no provider available)"
            )

            print()

            return 1

        print("UNHEALTHY")
        print()

        return 2
