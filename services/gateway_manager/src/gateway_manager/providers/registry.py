from gateway_manager.providers.provider import Provider


PROVIDERS = {
    "openai": Provider(
        name="openai",
        env="OPENAI_API_KEY",
        prefix="openai",
    ),
    "anthropic": Provider(
        name="anthropic",
        env="ANTHROPIC_API_KEY",
        prefix="anthropic",
    ),
    "google": Provider(
        name="google",
        env="GEMINI_API_KEY",
        prefix="gemini",
    ),
    "openrouter": Provider(
        name="openrouter",
        env="OPENROUTER_API_KEY",
        prefix="openrouter",
    ),
    "groq": Provider(
        name="groq",
        env="GROQ_API_KEY",
        prefix="groq",
    ),
    "mistral": Provider(
        name="mistral",
        env="MISTRAL_API_KEY",
        prefix="mistral",
    ),
    "deepseek": Provider(
        name="deepseek",
        env="DEEPSEEK_API_KEY",
        prefix="deepseek",
    ),
    "together": Provider(
        name="together",
        env="TOGETHER_API_KEY",
        prefix="together_ai",
    ),
    "xai": Provider(
        name="xai",
        env="XAI_API_KEY",
        prefix="xai",
    ),
    "ollama": Provider(
        name="ollama",
        env="OLLAMA_HOST",
        prefix="ollama",
    ),
    "lmstudio": Provider(
        name="lmstudio",
        env="LMSTUDIO_HOST",
        prefix="openai",
    ),
}


def get(name: str) -> Provider | None:
    return PROVIDERS.get(name)