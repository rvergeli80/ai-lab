from dataclasses import dataclass
from pathlib import Path

import yaml

from gateway_manager.catalog import CatalogLoader
from gateway_manager.providers import PROVIDERS
from gateway_manager.registry.model_registry import ModelRegistry
from gateway_manager.routing import PolicyLoader


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


ROOT = find_lab_root(
    Path(__file__)
)

PRICING_FILE = (
    ROOT
    / "config"
    / "pricing"
    / "models.yaml"
)

BUDGET_FILE = (
    ROOT
    / "config"
    / "budget"
    / "budgets.yaml"
)


KNOWN_TIERS = {
    "premium",
    "paid",
    "free",
    "local",
}

KNOWN_RETRYABLE_ERRORS = {
    "rate_limit",
    "quota_exceeded",
    "provider_unavailable",
    "timeout",
    "model_unavailable",
}


@dataclass(
    frozen=True,
    slots=True,
)
class ValidationIssue:

    severity: str
    code: str
    message: str


@dataclass(
    frozen=True,
    slots=True,
)
class ValidationResult:

    issues: tuple[
        ValidationIssue,
        ...
    ]

    @property
    def errors(
        self,
    ) -> tuple[
        ValidationIssue,
        ...
    ]:

        return tuple(
            issue
            for issue in self.issues
            if issue.severity == "ERROR"
        )

    @property
    def warnings(
        self,
    ) -> tuple[
        ValidationIssue,
        ...
    ]:

        return tuple(
            issue
            for issue in self.issues
            if issue.severity == "WARNING"
        )

    @property
    def valid(
        self,
    ) -> bool:

        return not self.errors


class GatewayConfigValidator:

    @classmethod
    def validate(
        cls,
    ) -> ValidationResult:

        issues: list[
            ValidationIssue
        ] = []

        try:
            catalog = CatalogLoader.load()
            registry = ModelRegistry.load()

        except Exception as exc:

            return ValidationResult(
                issues=(
                    ValidationIssue(
                        severity="ERROR",
                        code="catalog.load",
                        message=str(exc),
                    ),
                )
            )

        models = catalog.get(
            "models",
            {},
        )

        aliases = catalog.get(
            "aliases",
            {},
        )

        enabled_models = (
            registry.list_enabled()
        )

        cls._validate_models(
            models=models,
            issues=issues,
        )

        cls._validate_aliases(
            aliases=aliases,
            models=models,
            issues=issues,
        )

        cls._validate_routing(
            enabled_models=enabled_models,
            issues=issues,
        )

        cls._validate_pricing(
            models=models,
            enabled_models=enabled_models,
            issues=issues,
        )

        cls._validate_budget(
            enabled_models=enabled_models,
            issues=issues,
        )

        return ValidationResult(
            issues=tuple(issues)
        )

    @staticmethod
    def _validate_models(
        *,
        models: dict,
        issues: list[
            ValidationIssue
        ],
    ) -> None:

        for name, config in models.items():

            provider = config.get(
                "provider"
            )

            if provider not in PROVIDERS:

                issues.append(
                    ValidationIssue(
                        severity="ERROR",
                        code="model.provider",
                        message=(
                            f"Model '{name}' references "
                            f"unknown provider '{provider}'."
                        ),
                    )
                )

            status = config.get(
                "status"
            )

            if status not in {
                "enabled",
                "disabled",
            }:

                issues.append(
                    ValidationIssue(
                        severity="ERROR",
                        code="model.status",
                        message=(
                            f"Model '{name}' has invalid "
                            f"status '{status}'."
                        ),
                    )
                )

            provider_model = config.get(
                "model"
            )

            if not provider_model:

                issues.append(
                    ValidationIssue(
                        severity="ERROR",
                        code="model.provider_model",
                        message=(
                            f"Model '{name}' has no "
                            "provider model identifier."
                        ),
                    )
                )

            capabilities = config.get(
                "capabilities",
                [],
            )

            if (
                status == "enabled"
                and not capabilities
            ):

                issues.append(
                    ValidationIssue(
                        severity="ERROR",
                        code="model.capabilities",
                        message=(
                            f"Enabled model '{name}' "
                            "has no capabilities."
                        ),
                    )
                )

            context_window = config.get(
                "context_window"
            )

            if (
                not isinstance(
                    context_window,
                    int,
                )
                or context_window <= 0
            ):

                issues.append(
                    ValidationIssue(
                        severity="ERROR",
                        code="model.context_window",
                        message=(
                            f"Model '{name}' has invalid "
                            "context_window."
                        ),
                    )
                )

            priority = config.get(
                "priority"
            )

            if not isinstance(
                priority,
                int,
            ):

                issues.append(
                    ValidationIssue(
                        severity="ERROR",
                        code="model.priority",
                        message=(
                            f"Model '{name}' has invalid "
                            "priority."
                        ),
                    )
                )

    @staticmethod
    def _validate_aliases(
        *,
        aliases: dict,
        models: dict,
        issues: list[
            ValidationIssue
        ],
    ) -> None:

        for alias, target in aliases.items():

            if target not in models:

                issues.append(
                    ValidationIssue(
                        severity="ERROR",
                        code="alias.target",
                        message=(
                            f"Alias '{alias}' references "
                            f"unknown model '{target}'."
                        ),
                    )
                )

            if alias in models:

                issues.append(
                    ValidationIssue(
                        severity="ERROR",
                        code="alias.collision",
                        message=(
                            f"Alias '{alias}' collides "
                            "with a model name."
                        ),
                    )
                )

    @staticmethod
    def _validate_routing(
        *,
        enabled_models: dict,
        issues: list[
            ValidationIssue
        ],
    ) -> None:

        try:
            config = PolicyLoader.load()

        except Exception as exc:

            issues.append(
                ValidationIssue(
                    severity="ERROR",
                    code="routing.load",
                    message=str(exc),
                )
            )

            return

        policies = config.get(
            "policies",
            {},
        )

        if not policies:

            issues.append(
                ValidationIssue(
                    severity="ERROR",
                    code="routing.empty",
                    message=(
                        "No routing policies defined."
                    ),
                )
            )

        for capability, policy in (
            policies.items()
        ):

            strategy = policy.get(
                "strategy"
            )

            if strategy != "fallback":

                issues.append(
                    ValidationIssue(
                        severity="ERROR",
                        code="routing.strategy",
                        message=(
                            f"Capability '{capability}' "
                            f"uses unsupported strategy "
                            f"'{strategy}'."
                        ),
                    )
                )

            candidates = policy.get(
                "candidates",
                [],
            )

            if not candidates:

                issues.append(
                    ValidationIssue(
                        severity="ERROR",
                        code="routing.candidates",
                        message=(
                            f"Capability '{capability}' "
                            "has no routing candidates."
                        ),
                    )
                )

            for candidate in candidates:

                tier = candidate.get(
                    "tier"
                )

                if tier not in KNOWN_TIERS:

                    issues.append(
                        ValidationIssue(
                            severity="ERROR",
                            code="routing.tier",
                            message=(
                                f"Capability '{capability}' "
                                f"references unknown tier "
                                f"'{tier}'."
                            ),
                        )
                    )

            supporting_models = [
                model
                for model
                in enabled_models.values()
                if model.has_capability(
                    capability
                )
            ]

            if not supporting_models:

                issues.append(
                    ValidationIssue(
                        severity="WARNING",
                        code="routing.no_model",
                        message=(
                            f"Capability '{capability}' "
                            "has no enabled model."
                        ),
                    )
                )

        fallback = config.get(
            "fallback",
            {},
        )

        max_attempts = fallback.get(
            "max_attempts"
        )

        if (
            not isinstance(
                max_attempts,
                int,
            )
            or max_attempts <= 0
        ):

            issues.append(
                ValidationIssue(
                    severity="ERROR",
                    code="fallback.max_attempts",
                    message=(
                        "fallback.max_attempts must "
                        "be a positive integer."
                    ),
                )
            )

        configured_errors = set(
            fallback.get(
                "retryable_errors",
                [],
            )
        )

        unknown_errors = (
            configured_errors
            - KNOWN_RETRYABLE_ERRORS
        )

        for error_name in sorted(
            unknown_errors
        ):

            issues.append(
                ValidationIssue(
                    severity="ERROR",
                    code="fallback.retryable_error",
                    message=(
                        "Unknown retryable error "
                        f"'{error_name}'."
                    ),
                )
            )

    @staticmethod
    def _validate_pricing(
        *,
        models: dict,
        enabled_models: dict,
        issues: list[
            ValidationIssue
        ],
    ) -> None:

        try:

            with PRICING_FILE.open(
                "r",
                encoding="utf-8",
            ) as file:

                pricing = (
                    yaml.safe_load(file)
                    or {}
                )

        except Exception as exc:

            issues.append(
                ValidationIssue(
                    severity="ERROR",
                    code="pricing.load",
                    message=str(exc),
                )
            )

            return

        default_currency = pricing.get(
            "currency"
        )

        if not isinstance(
            default_currency,
            str,
        ):

            issues.append(
                ValidationIssue(
                    severity="ERROR",
                    code="pricing.currency",
                    message=(
                        "Pricing currency must "
                        "be defined."
                    ),
                )
            )

        pricing_models = pricing.get(
            "models",
            {},
        )

        for name, config in (
            pricing_models.items()
        ):

            if name not in models:

                issues.append(
                    ValidationIssue(
                        severity="ERROR",
                        code="pricing.model",
                        message=(
                            f"Pricing references unknown "
                            f"model '{name}'."
                        ),
                    )
                )

                continue

            expected_provider = (
                models[name].get(
                    "provider"
                )
            )

            pricing_provider = (
                config.get(
                    "provider"
                )
            )

            if (
                pricing_provider
                != expected_provider
            ):

                issues.append(
                    ValidationIssue(
                        severity="ERROR",
                        code="pricing.provider",
                        message=(
                            f"Pricing provider for "
                            f"'{name}' is "
                            f"'{pricing_provider}', "
                            f"expected "
                            f"'{expected_provider}'."
                        ),
                    )
                )

            input_price = config.get(
                "input_per_million"
            )

            output_price = config.get(
                "output_per_million"
            )

            for field, value in (
                (
                    "input_per_million",
                    input_price,
                ),
                (
                    "output_per_million",
                    output_price,
                ),
            ):

                if (
                    value is not None
                    and (
                        not isinstance(
                            value,
                            (
                                int,
                                float,
                            ),
                        )
                        or value < 0
                    )
                ):

                    issues.append(
                        ValidationIssue(
                            severity="ERROR",
                            code="pricing.value",
                            message=(
                                f"Pricing '{field}' "
                                f"for '{name}' is invalid."
                            ),
                        )
                    )

        for name in enabled_models:

            if name not in pricing_models:

                issues.append(
                    ValidationIssue(
                        severity="WARNING",
                        code="pricing.missing",
                        message=(
                            f"Enabled model '{name}' "
                            "has no explicit pricing "
                            "configuration."
                        ),
                    )
                )

    @staticmethod
    def _validate_budget(
        *,
        enabled_models: dict,
        issues: list[
            ValidationIssue
        ],
    ) -> None:

        try:

            with BUDGET_FILE.open(
                "r",
                encoding="utf-8",
            ) as file:

                data = (
                    yaml.safe_load(file)
                    or {}
                )

        except Exception as exc:

            issues.append(
                ValidationIssue(
                    severity="ERROR",
                    code="budget.load",
                    message=str(exc),
                )
            )

            return

        budget = data.get(
            "budget",
            {},
        )

        currency = budget.get(
            "currency"
        )

        if not isinstance(
            currency,
            str,
        ):

            issues.append(
                ValidationIssue(
                    severity="ERROR",
                    code="budget.currency",
                    message=(
                        "Budget currency must "
                        "be defined."
                    ),
                )
            )

        defaults = budget.get(
            "default",
            {},
        )

        for field in (
            "daily",
            "monthly",
        ):

            value = defaults.get(
                field
            )

            if (
                not isinstance(
                    value,
                    (
                        int,
                        float,
                    ),
                )
                or value < 0
            ):

                issues.append(
                    ValidationIssue(
                        severity="ERROR",
                        code="budget.limit",
                        message=(
                            f"Budget '{field}' "
                            "must be a non-negative "
                            "number."
                        ),
                    )
                )

        tiers = budget.get(
            "tiers",
            {},
        )

        for tier in KNOWN_TIERS:

            if tier not in tiers:

                issues.append(
                    ValidationIssue(
                        severity="ERROR",
                        code="budget.tier",
                        message=(
                            f"Budget configuration "
                            f"is missing tier '{tier}'."
                        ),
                    )
                )

        unknown_tiers = (
            set(tiers)
            - KNOWN_TIERS
        )

        for tier in sorted(
            unknown_tiers
        ):

            issues.append(
                ValidationIssue(
                    severity="ERROR",
                    code="budget.unknown_tier",
                    message=(
                        f"Budget contains unknown "
                        f"tier '{tier}'."
                    ),
                )
            )

        behavior = budget.get(
            "behavior",
            {},
        )

        if (
            behavior.get(
                "on_budget_exceeded"
            )
            != "fallback"
        ):

            issues.append(
                ValidationIssue(
                    severity="ERROR",
                    code="budget.behavior",
                    message=(
                        "Unsupported budget exceeded "
                        "behavior."
                    ),
                )
            )

        # Detect explicit remote prices whose
        # currency would not be counted by budget.
        try:

            with PRICING_FILE.open(
                "r",
                encoding="utf-8",
            ) as file:

                pricing = (
                    yaml.safe_load(file)
                    or {}
                )

        except Exception:
            return

        pricing_currency = pricing.get(
            "currency"
        )

        pricing_models = pricing.get(
            "models",
            {},
        )

        for name, model in (
            enabled_models.items()
        ):

            if (
                model.provider
                == "ollama"
                or model.has_tag(
                    "local"
                )
            ):
                continue

            config = pricing_models.get(
                name
            )

            if config is None:
                continue

            input_price = config.get(
                "input_per_million"
            )

            output_price = config.get(
                "output_per_million"
            )

            has_explicit_price = (
                input_price is not None
                and output_price is not None
            )

            model_currency = (
                config.get(
                    "currency",
                    pricing_currency,
                )
            )

            if (
                has_explicit_price
                and model_currency
                != currency
            ):

                issues.append(
                    ValidationIssue(
                        severity="ERROR",
                        code="budget.currency_mismatch",
                        message=(
                            f"Remote model '{name}' "
                            f"has explicit pricing in "
                            f"{model_currency}, but "
                            f"budget is enforced in "
                            f"{currency}."
                        ),
                    )
                )
