from collections.abc import Iterator

import pytest

from ai_cli.exceptions import ProviderError
from ai_cli.models import AIRequest, AIResponse
from ai_cli.runner import run_request


def request() -> AIRequest:
    return AIRequest(
        provider="openai",
        model="test-model",
        prompt="unchanged prompt",
        files=[],
        timeout=12,
    )


class FakeProvider:
    def __init__(self, outcomes: Iterator[AIResponse | ProviderError]) -> None:
        self.outcomes = outcomes
        self.requests: list[AIRequest] = []

    def run(self, ai_request: AIRequest) -> AIResponse:
        self.requests.append(ai_request)
        outcome = next(self.outcomes)
        if isinstance(outcome, ProviderError):
            raise outcome
        return outcome


def test_retries_temporary_failures_and_preserves_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = AIResponse("native output", "openai", "test-model")
    provider = FakeProvider(
        iter(
            [
                ProviderError("temporary", retryable=True),
                ProviderError("temporary", retryable=True),
                expected,
            ]
        )
    )
    sleeps: list[float] = []
    monkeypatch.setattr("ai_cli.runner.get_provider", lambda name, key: provider)

    actual = run_request(request(), "api-secret", 3, sleep=sleeps.append)

    assert actual == expected
    assert provider.requests == [request(), request(), request()]
    assert sleeps == [0.5, 1.0]


def test_does_not_retry_permanent_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = FakeProvider(iter([ProviderError("permanent")]))
    monkeypatch.setattr("ai_cli.runner.get_provider", lambda name, key: provider)

    with pytest.raises(ProviderError, match="permanent"):
        run_request(request(), "api-secret", 3, sleep=lambda _: None)

    assert len(provider.requests) == 1


def test_stops_after_configured_number_of_retries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = FakeProvider(
        iter([ProviderError("temporary", retryable=True) for _ in range(3)])
    )
    monkeypatch.setattr("ai_cli.runner.get_provider", lambda name, key: provider)

    with pytest.raises(ProviderError, match="temporary"):
        run_request(request(), "api-secret", 2, sleep=lambda _: None)

    assert len(provider.requests) == 3
