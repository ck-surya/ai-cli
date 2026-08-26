"""Explicit registry for supported providers."""

from ai_cli.exceptions import ConfigurationError
from ai_cli.providers.base import AIProvider
from ai_cli.providers.gemini import GeminiProvider
from ai_cli.providers.openai import OpenAIProvider

PROVIDERS: dict[str, type[AIProvider]] = {
    "openai": OpenAIProvider,
    "gemini": GeminiProvider,
}


def get_provider(name: str, api_key: str) -> AIProvider:
    provider_class = PROVIDERS.get(name)
    if provider_class is None:
        raise ConfigurationError(
            f"Unsupported provider '{name}'. Run 'ai providers' to see supported providers."
        )
    return provider_class(api_key)
