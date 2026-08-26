"""Command-line interface for AI CLI."""

import logging
from pathlib import Path
import sys
import time
from typing import Annotated

import typer

from ai_cli import __version__
from ai_cli.config import (
    DEFAULT_CONFIG_PATH,
    Settings,
    load_environment,
    load_settings,
    resolve_api_key,
)
from ai_cli.exceptions import AICLIError, ConfigurationError, InputError, OutputError
from ai_cli.models import AIRequest
from ai_cli.output import write_output
from ai_cli.registry import PROVIDERS
from ai_cli.runner import run_request

app = typer.Typer(
    name="ai",
    help="Call OpenAI or Gemini through one local command-line interface.",
    no_args_is_help=True,
    add_completion=False,
)
logger = logging.getLogger("ai_cli")
DEFAULT_FILE_PROMPT = "Analyze the attached file."


@app.command()
def run(
    input_value: Annotated[
        str,
        typer.Argument(
            metavar="INPUT",
            help="Prompt text or the path to a local file.",
        ),
    ],
    provider: Annotated[
        str | None,
        typer.Option("--provider", "-p", help="Provider name."),
    ] = None,
    model: Annotated[
        str | None,
        typer.Option("--model", "-m", help="Provider model name."),
    ] = None,
    prompt: Annotated[
        str | None,
        typer.Option(help="Instruction to use when INPUT is a file."),
    ] = None,
    api_key: Annotated[
        str | None,
        typer.Option("--api-key", help="API key for this invocation."),
    ] = None,
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Write generated content to this file."),
    ] = None,
    timeout: Annotated[
        int | None,
        typer.Option(min=1, help="Request timeout in seconds."),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Validate without making an API request."),
    ] = False,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Print safe operational details."),
    ] = False,
) -> None:
    """Send prompt text or a local file to an AI provider."""
    try:
        load_environment()
        settings = load_settings()
        request = _build_request(
            input_value=input_value,
            file_prompt=prompt,
            provider=provider,
            model=model,
            timeout=timeout,
            settings=settings,
        )
        resolved_api_key = resolve_api_key(request.provider, api_key)
        _validate_output_path(output, request.files)

        if dry_run:
            _print_dry_run(request)
            return

        _configure_verbose_logging(verbose)
        start = time.monotonic()
        logger.info("Provider: %s", request.provider)
        logger.info("Model: %s", request.model)
        logger.info("Sending request")
        response = run_request(request, resolved_api_key, settings.max_retries)
        logger.info("Response received")
        logger.info("Duration: %.2fs", time.monotonic() - start)
        write_output(response.content, output)
    except AICLIError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from None


@app.command("providers")
def list_providers() -> None:
    """List supported providers."""
    for name in PROVIDERS:
        typer.echo(name)


@app.command("models")
def show_models(
    provider: Annotated[
        str | None,
        typer.Option("--provider", "-p", help="Show selection for this provider."),
    ] = None,
) -> None:
    """Show the configured default model selection."""
    try:
        settings = load_settings()
        selected_provider = (provider or settings.default_provider).lower()
        if selected_provider not in PROVIDERS:
            raise ConfigurationError(
                f"Unsupported provider '{selected_provider}'. "
                "Run 'ai providers' to see supported providers."
            )
        if (
            settings.default_model is not None
            and selected_provider == settings.default_provider
        ):
            typer.echo(f"{selected_provider}: {settings.default_model} (configured default)")
        else:
            typer.echo(
                f"{selected_provider}: no default model configured; "
                "pass --model when running a request"
            )
    except AICLIError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from None


@app.command("config")
def show_config() -> None:
    """Show resolved non-secret configuration."""
    try:
        settings = load_settings()
    except AICLIError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from None

    typer.echo(f"Config file: {DEFAULT_CONFIG_PATH}")
    typer.echo(f"Default provider: {settings.default_provider}")
    typer.echo(f"Default model: {settings.default_model or '<not configured>'}")
    typer.echo(f"Timeout: {settings.timeout} seconds")
    typer.echo(f"Max retries: {settings.max_retries}")


@app.command("version")
def show_version() -> None:
    """Show the installed AI CLI version."""
    typer.echo(__version__)


def _build_request(
    *,
    input_value: str,
    file_prompt: str | None,
    provider: str | None,
    model: str | None,
    timeout: int | None,
    settings: Settings,
) -> AIRequest:
    provider_name = (provider or settings.default_provider).strip().lower()
    if provider_name not in PROVIDERS:
        raise ConfigurationError(
            f"Unsupported provider '{provider_name}'. "
            "Run 'ai providers' to see supported providers."
        )

    model_name = (model or settings.default_model or "").strip()
    if not model_name:
        raise ConfigurationError(
            "No model is configured.\n\n"
            "Pass --model MODEL or set default_model in "
            f"{DEFAULT_CONFIG_PATH}."
        )

    candidate = Path(input_value).expanduser()
    files: list[Path] = []
    resolved_prompt: str | None
    if candidate.is_file():
        files = [candidate]
        resolved_prompt = file_prompt or DEFAULT_FILE_PROMPT
    elif candidate.exists():
        raise InputError(f"Input path is not a file: {candidate}")
    elif file_prompt is not None or _looks_like_file_path(input_value):
        raise InputError(f"Input file does not exist: {candidate}")
    else:
        resolved_prompt = input_value

    if not resolved_prompt:
        raise InputError("Prompt text cannot be empty.")

    return AIRequest(
        provider=provider_name,
        model=model_name,
        prompt=resolved_prompt,
        files=files,
        timeout=timeout or settings.timeout,
    )


def _looks_like_file_path(value: str) -> bool:
    if "\n" in value or "\r" in value:
        return False
    path = Path(value)
    return "/" in value or "\\" in value or (" " not in value and bool(path.suffix))


def _validate_output_path(output: Path | None, inputs: list[Path]) -> None:
    if output is None:
        return
    output_path = output.expanduser().resolve()
    if any(output_path == input_path.resolve() for input_path in inputs):
        raise OutputError("Output path must not overwrite the input file.")
    if not output_path.parent.exists():
        raise OutputError(f"Output directory does not exist: {output_path.parent}")
    if not output_path.parent.is_dir():
        raise OutputError(f"Output parent is not a directory: {output_path.parent}")
    if output_path.is_dir():
        raise OutputError(f"Output path is a directory: {output_path}")


def _print_dry_run(request: AIRequest) -> None:
    typer.echo(f"Provider: {request.provider}")
    typer.echo(f"Model: {request.model}")
    if request.files:
        typer.echo(f"Input: {request.files[0]}")
    else:
        typer.echo("Input: text prompt")
    typer.echo("Credentials: configured")
    typer.echo("\nNo API request was sent.")


def _configure_verbose_logging(verbose: bool) -> None:
    logger.handlers.clear()
    logger.propagate = False
    if not verbose:
        logger.disabled = True
        return

    logger.disabled = False
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)


if __name__ == "__main__":
    app()
