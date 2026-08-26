"""Small application-level request and response contracts."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AIRequest:
    provider: str
    model: str
    prompt: str | None
    files: list[Path]
    timeout: int


@dataclass(frozen=True)
class AIResponse:
    content: str
    provider: str
    model: str
