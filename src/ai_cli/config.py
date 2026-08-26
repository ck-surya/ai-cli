"""Configuration and credential resolution."""

from dataclasses import dataclass
import os
from pathlib import Path
import tomllib

from dotenv import load_dotenv

from ai_cli.exceptions import ConfigurationError, CredentialError

DEFAULT_CONFIG_PATH = Path.home() / ".config" / "ai-cli" / "config.toml"
API_KEY_ENV_VARS = {
    "openai": "OPENAI_API_KEY",
    "gemini": "GEMINI_API_KEY",
}


@dataclass(frozen=True)
class Settings:
    default_provider: str = "openai"
    default_model: str | None = None
    timeout: int = 120
    max_retries: int = 3


def load_environment(path: Path | None = None) -> None:
    """Load a local .env without overriding process environment values."""
    load_dotenv(dotenv_path=path or Path.cwd() / ".env", override=False)


def load_settings(path: Path = DEFAULT_CONFIG_PATH) -> Settings:
    if not path.exists():
        return Settings()

    try:
        with path.open("rb") as config_file:
            data = tomllib.load(config_file)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise ConfigurationError(
            f"Could not read configuration from {path}: {exc}"
        ) from None

    settings_data = data.get("settings", {})
    if not isinstance(settings_data, dict):
        raise ConfigurationError(
            f"Invalid configuration in {path}: [settings] must be a table."
        )

    provider = data.get("default_provider", "openai")
    model = data.get("default_model")
    timeout = settings_data.get("timeout", 120)
    max_retries = settings_data.get("max_retries", 3)

    if not isinstance(provider, str) or not provider.strip():
        raise ConfigurationError(
            f"Invalid configuration in {path}: default_provider must be a string."
        )
    if model is not None and (not isinstance(model, str) or not model.strip()):
        raise ConfigurationError(
            f"Invalid configuration in {path}: default_model must be a string."
        )
    if not isinstance(timeout, int) or isinstance(timeout, bool) or timeout <= 0:
        raise ConfigurationError(
            f"Invalid configuration in {path}: settings.timeout must be a positive integer."
        )
    if (
        not isinstance(max_retries, int)
        or isinstance(max_retries, bool)
        or max_retries < 0
    ):
        raise ConfigurationError(
            f"Invalid configuration in {path}: settings.max_retries must be a non-negative integer."
        )

    return Settings(
        default_provider=provider.strip().lower(),
        default_model=model.strip() if model else None,
        timeout=timeout,
        max_retries=max_retries,
    )


def resolve_api_key(provider: str, cli_api_key: str | None = None) -> str:
    env_var = API_KEY_ENV_VARS.get(provider)
    if env_var is None:
        raise ConfigurationError(
            f"Unsupported provider '{provider}'. Run 'ai providers' to see supported providers."
        )

    api_key = cli_api_key or os.environ.get(env_var)
    if api_key and api_key.strip():
        return api_key.strip()

    display_name = "OpenAI" if provider == "openai" else "Gemini"
    raise CredentialError(
        f"{display_name} API key is not configured.\n\n"
        f"Set {env_var}, add it to .env, or pass --api-key."
    )
