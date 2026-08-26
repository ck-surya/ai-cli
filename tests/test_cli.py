from pathlib import Path

import pytest
from typer.testing import CliRunner

from ai_cli.cli import app
from ai_cli.config import Settings
from ai_cli.models import AIResponse

runner = CliRunner()


@pytest.fixture
def configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-secret")
    monkeypatch.setattr(
        "ai_cli.cli.load_settings",
        lambda: Settings(default_provider="openai", default_model="test-model"),
    )


def test_run_prints_only_native_provider_output(
    configured: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured_requests = []

    def fake_run(request, api_key, retries):  # type: ignore[no-untyped-def]
        captured_requests.append((request, api_key, retries))
        return AIResponse("native output", request.provider, request.model)

    monkeypatch.setattr("ai_cli.cli.run_request", fake_run)

    result = runner.invoke(app, ["run", "unchanged prompt"])

    assert result.exit_code == 0
    assert result.stdout == "native output"
    request, api_key, retries = captured_requests[0]
    assert request.prompt == "unchanged prompt"
    assert request.timeout == 120
    assert api_key == "test-secret"
    assert retries == 3


def test_file_uses_explicit_prompt_and_timeout(
    tmp_path: Path, configured: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    document = tmp_path / "report.pdf"
    document.write_bytes(b"%PDF-test")
    captured_requests = []

    def fake_run(request, api_key, retries):  # type: ignore[no-untyped-def]
        captured_requests.append(request)
        return AIResponse("summary", request.provider, request.model)

    monkeypatch.setattr("ai_cli.cli.run_request", fake_run)

    result = runner.invoke(
        app,
        [
            "run",
            str(document),
            "--prompt",
            "Summarize exactly",
            "--timeout",
            "9",
        ],
    )

    assert result.exit_code == 0
    assert result.stdout == "summary"
    assert captured_requests[0].files == [document]
    assert captured_requests[0].prompt == "Summarize exactly"
    assert captured_requests[0].timeout == 9


def test_dry_run_makes_no_request(
    configured: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    def unexpected_request(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("dry-run made a provider request")

    monkeypatch.setattr("ai_cli.cli.run_request", unexpected_request)

    result = runner.invoke(app, ["run", "Hello", "--dry-run"])

    assert result.exit_code == 0
    assert "Provider: openai" in result.stdout
    assert "Model: test-model" in result.stdout
    assert "Credentials: configured" in result.stdout
    assert "No API request was sent." in result.stdout
    assert "test-secret" not in result.stdout


def test_verbose_output_contains_no_prompt_or_key(
    configured: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "ai_cli.cli.run_request",
        lambda request, api_key, retries: AIResponse(
            "native output", request.provider, request.model
        ),
    )

    result = runner.invoke(app, ["run", "private prompt", "--verbose"])

    assert result.exit_code == 0
    assert result.stdout == "native output"
    assert "Provider: openai" in result.stderr
    assert "private prompt" not in result.stderr
    assert "test-secret" not in result.stderr


def test_unknown_provider_error_is_actionable(configured: None) -> None:
    result = runner.invoke(app, ["run", "Hello", "--provider", "other"])

    assert result.exit_code == 1
    assert "Unsupported provider 'other'" in result.stderr
    assert "ai providers" in result.stderr


def test_missing_model_error_explains_both_remedies(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("ai_cli.cli.load_settings", lambda: Settings())

    result = runner.invoke(app, ["run", "Hello"])

    assert result.exit_code == 1
    assert "--model" in result.stderr
    assert "default_model" in result.stderr


def test_missing_pdf_is_reported_as_a_file(configured: None) -> None:
    result = runner.invoke(app, ["run", "missing.pdf"])

    assert result.exit_code == 1
    assert "Input file does not exist" in result.stderr


def test_refuses_to_overwrite_input_file(
    tmp_path: Path, configured: None
) -> None:
    document = tmp_path / "report.pdf"
    document.write_bytes(b"%PDF-test")

    result = runner.invoke(
        app, ["run", str(document), "--output", str(document)]
    )

    assert result.exit_code == 1
    assert "must not overwrite" in result.stderr
    assert document.read_bytes() == b"%PDF-test"


def test_rejects_missing_output_directory_before_request(
    tmp_path: Path, configured: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    def unexpected_request(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("request was sent before output validation")

    monkeypatch.setattr("ai_cli.cli.run_request", unexpected_request)
    output = tmp_path / "missing" / "result.txt"

    result = runner.invoke(app, ["run", "Hello", "--output", str(output)])

    assert result.exit_code == 1
    assert "Output directory does not exist" in result.stderr


def test_providers_lists_both_adapters() -> None:
    result = runner.invoke(app, ["providers"])

    assert result.exit_code == 0
    assert result.stdout.splitlines() == ["openai", "gemini"]
