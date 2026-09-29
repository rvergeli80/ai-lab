from gateway_manager.pricing import PricingService


def test_local_model_cost_is_zero():

    service = PricingService()

    cost = service.calculate_cost_eur(
        model_name="laguna-xs-2.1",
        prompt_tokens=1000,
        completion_tokens=500,
    )

    assert cost == 0.0


def test_unknown_model_cost_is_none():

    service = PricingService()

    cost = service.calculate_cost_eur(
        model_name="unknown-model",
        prompt_tokens=1000,
        completion_tokens=500,
    )

    assert cost is None
