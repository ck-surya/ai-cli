"""Single provider execution path with application-level retries."""

import time
from collections.abc import Callable

from ai_cli.exceptions import ProviderError
from ai_cli.models import AIRequest, AIResponse
from ai_cli.registry import get_provider


def run_request(
    request: AIRequest,
    api_key: str,
    max_retries: int,
    *,
    sleep: Callable[[float], None] = time.sleep,
) -> AIResponse:
    provider = get_provider(request.provider, api_key)

    for attempt in range(max_retries + 1):
        try:
            return provider.run(request)
        except ProviderError as exc:
            if not exc.retryable or attempt == max_retries:
                raise
            sleep(min(0.5 * (2**attempt), 4.0))

    raise AssertionError("retry loop must return or raise")
