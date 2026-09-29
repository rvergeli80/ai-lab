from gateway_manager.providers import PROVIDERS


def test_provider_registry():

    assert "openai" in PROVIDERS
    assert "anthropic" in PROVIDERS
    assert "google" in PROVIDERS
    assert "openrouter" in PROVIDERS

    assert PROVIDERS["openai"].env == "OPENAI_API_KEY"

    assert (
        PROVIDERS["openai"].build_model_name("gpt-5")
        == "openai/gpt-5"
    )