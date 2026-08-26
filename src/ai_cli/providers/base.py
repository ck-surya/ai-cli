"""Common provider boundary."""

from abc import ABC, abstractmethod

from ai_cli.models import AIRequest, AIResponse


class AIProvider(ABC):
    @abstractmethod
    def run(self, request: AIRequest) -> AIResponse:
        """Send one request and return its generated text."""
