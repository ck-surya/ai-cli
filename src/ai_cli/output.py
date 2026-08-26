"""Output handling that preserves provider-generated content."""

from pathlib import Path
import sys

from ai_cli.exceptions import OutputError


def write_output(content: str, path: Path | None = None) -> None:
    try:
        if path is None:
            sys.stdout.write(content)
            sys.stdout.flush()
        else:
            path.write_text(content, encoding="utf-8")
    except OSError as exc:
        destination = "stdout" if path is None else str(path)
        raise OutputError(f"Could not write output to {destination}: {exc}") from None
