"""Google Gemini adapter."""

import mimetypes
from typing import Any

import httpx

from ai_cli.exceptions import CredentialError, InputError, ProviderError
from ai_cli.models import AIRequest, AIResponse
from ai_cli.providers.base import AIProvider


class GeminiProvider(AIProvider):
    def __init__(self, api_key: str, client: Any | None = None) -> None:
        self.api_key = api_key
        self._client = client

    def run(self, request: AIRequest) -> AIResponse:
        try:
            from google import genai
            from google.genai import errors, types
        except ImportError:
            raise ProviderError(
                "Gemini support is not installed. Install ai-cli with its runtime dependencies."
            ) from None

        try:
            client = self._client or genai.Client(
                api_key=self.api_key,
                http_options=types.HttpOptions(timeout=request.timeout * 1000),
            )
            response = client.models.generate_content(
                model=request.model,
                contents=self._build_contents(request, types),
            )
        except errors.ClientError as exc:
            if exc.code in {401, 403}:
                raise CredentialError(
                    "Gemini rejected the API credentials. Check GEMINI_API_KEY or --api-key."
                ) from None
            retryable = exc.code in {408, 409, 429}
            message = (
                "Gemini returned a temporary service error."
                if retryable
                else "Gemini rejected the request. Check the model name and input."
            )
            raise ProviderError(message, retryable=retryable) from None
        except errors.ServerError:
            raise ProviderError(
                "Gemini returned a temporary service error.", retryable=True
            ) from None
        except errors.APIError as exc:
            retryable = exc.code in {408, 409, 429} or exc.code >= 500
            raise ProviderError(
                "Gemini could not process the request.", retryable=retryable
            ) from None
        except errors.UnknownApiResponseError:
            raise ProviderError("Gemini returned an unreadable response.") from None
        except (httpx.ConnectError, httpx.TimeoutException, ConnectionError, TimeoutError):
            raise ProviderError(
                "Gemini is temporarily unreachable or the request timed out.",
                retryable=True,
            ) from None

        try:
            content = response.text
        except ValueError:
            raise ProviderError("Gemini returned no text output.") from None
        if content is None:
            raise ProviderError("Gemini returned no text output.")
        return AIResponse(content=content, provider=request.provider, model=request.model)

    @staticmethod
    def _build_contents(request: AIRequest, types: Any) -> list[Any] | str:
        if not request.files:
            return request.prompt or ""

        contents: list[Any] = []
        for path in request.files:
            mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            try:
                data = path.read_bytes()
            except OSError as exc:
                raise InputError(f"Could not read input file '{path}': {exc}") from None
            contents.append(types.Part.from_bytes(data=data, mime_type=mime_type))
        if request.prompt:
            contents.append(request.prompt)
        return contents
