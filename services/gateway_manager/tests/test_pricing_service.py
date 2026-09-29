from gateway_manager.pricing import (
    PricingService,
)


def test_local_model_cost_is_zero():

    service = PricingService()

    quote = service.calculate_cost(
        canonical_model_name=(
            "laguna-xs-2.1"
        ),
        provider="ollama",
        litellm_model_name=(
            "laguna-xs-2.1:latest"
        ),
        prompt_tokens=1000,
        completion_tokens=500,
    )

    assert quote is not None
    assert quote.amount == 0.0
    assert quote.currency == "EUR"
    assert quote.source == "nevermine-config"


def test_openrouter_uses_litellm_pricing():

    service = PricingService()

    quote = service.calculate_cost(
        canonical_model_name=(
            "openrouter-gemma"
        ),
        provider="openrouter",
        litellm_model_name=(
            "openrouter/"
            "google/gemma-3-27b-it"
        ),
        prompt_tokens=1_000_000,
        completion_tokens=1_000_000,
    )

    assert quote is not None
    assert quote.amount > 0.0
    assert quote.currency == "USD"
    assert quote.source == "litellm"


def test_unknown_remote_model_returns_none():

    service = PricingService()

    quote = service.calculate_cost(
        canonical_model_name=(
            "unknown-model"
        ),
        provider="unknown-provider",
        litellm_model_name=(
            "unknown-provider/"
            "unknown-model"
        ),
        prompt_tokens=1000,
        completion_tokens=500,
    )

    assert quote is None

