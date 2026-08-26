from pathlib import Path

import pytest

from ai_cli.config import load_environment, load_settings, resolve_api_key
from ai_cli.exceptions import ConfigurationError, CredentialError


def test_missing_config_uses_safe_defaults(tmp_path: Path) -> None:
    settings = load_settings(tmp_path / "missing.toml")

    assert settings.default_provider == "openai"
    assert settings.default_model is None
    assert settings.timeout == 120
    assert settings.max_retries == 3


def test_loads_documented_toml_settings(tmp_path: Path) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        'default_provider = "gemini"\n'
        'default_model = "model-name"\n'
        "[settings]\n"
        "timeout = 45\n"
        "max_retries = 2\n",
        encoding="utf-8",
    )

    settings = load_settings(config_path)

    assert settings.default_provider == "gemini"
    assert settings.default_model == "model-name"
    assert settings.timeout == 45
    assert settings.max_retries == 2


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        ("[settings]\ntimeout = 0\n", "positive integer"),
        ("[settings]\nmax_retries = -1\n", "non-negative integer"),
        ('default_provider = ""\n', "default_provider"),
    ],
)
def test_invalid_config_is_actionable(
    tmp_path: Path, body: str, expected: str
) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text(body, encoding="utf-8")

    with pytest.raises(ConfigurationError, match=expected):
        load_settings(config_path)


def test_cli_key_takes_precedence_over_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "environment-secret")

    assert resolve_api_key("openai", "cli-secret") == "cli-secret"


def test_environment_takes_precedence_over_dotenv(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dotenv_path = tmp_path / ".env"
    dotenv_path.write_text("OPENAI_API_KEY=dotenv-secret\n", encoding="utf-8")
    monkeypatch.setenv("OPENAI_API_KEY", "environment-secret")

    load_environment(dotenv_path)

    assert resolve_api_key("openai") == "environment-secret"


def test_dotenv_supplies_missing_environment_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dotenv_path = tmp_path / ".env"
    dotenv_path.write_text("GEMINI_API_KEY=dotenv-secret\n", encoding="utf-8")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    load_environment(dotenv_path)

    assert resolve_api_key("gemini") == "dotenv-secret"


def test_missing_key_error_names_safe_remedies(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(CredentialError) as caught:
        resolve_api_key("openai")

    message = str(caught.value)
    assert "OPENAI_API_KEY" in message
    assert "--api-key" in message
    assert "secret" not in message
