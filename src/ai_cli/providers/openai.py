"""OpenAI Responses API adapter."""

import base64
import mimetypes
from pathlib import Path
from typing import Any

from ai_cli.exceptions import CredentialError, InputError, ProviderError
from ai_cli.models import AIRequest, AIResponse
from ai_cli.providers.base import AIProvider


class OpenAIProvider(AIProvider):
    def __init__(self, api_key: str, client: Any | None = None) -> None:
        self.api_key = api_key
        self._client = client

    def run(self, request: AIRequest) -> AIResponse:
        try:
            import openai
        except ImportError:
            raise ProviderError(
                "OpenAI support is not installed. Install ai-cli with its runtime dependencies."
            ) from None

        try:
            client = self._client or openai.OpenAI(
                api_key=self.api_key,
                timeout=float(request.timeout),
                max_retries=0,
            )
            response = client.responses.create(
                model=request.model,
                input=self._build_input(request),
            )
        except (openai.AuthenticationError, openai.PermissionDeniedError):
            raise CredentialError(
                "OpenAI rejected the API credentials. Check OPENAI_API_KEY or --api-key."
            ) from None
        except (openai.APITimeoutError, openai.APIConnectionError):
            raise ProviderError(
                "OpenAI is temporarily unreachable or the request timed out.",
                retryable=True,
            ) from None
        except openai.RateLimitError:
            raise ProviderError(
                "OpenAI rate-limited the request. Try again later.", retryable=True
            ) from None
        except openai.APIStatusError as exc:
            retryable = exc.status_code in {408, 409, 429} or exc.status_code >= 500
            message = (
                "OpenAI returned a temporary service error."
                if retryable
                else "OpenAI rejected the request. Check the model name and input."
            )
            raise ProviderError(message, retryable=retryable) from None
        except openai.OpenAIError:
            raise ProviderError(
                "OpenAI could not process the request. Check the model name and input."
            ) from None

        content = response.output_text
        if content is None:
            raise ProviderError("OpenAI returned no text output.")
        return AIResponse(content=content, provider=request.provider, model=request.model)

    @staticmethod
    def _build_input(request: AIRequest) -> str | list[dict[str, Any]]:
        if not request.files:
            return request.prompt or ""

        content: list[dict[str, Any]] = []
        for path in request.files:
            mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            data_url = _read_data_url(path, mime_type)
            if mime_type.startswith("image/"):
                content.append({"type": "input_image", "image_url": data_url})
            else:
                content.append(
                    {
                        "type": "input_file",
                        "filename": path.name,
                        "file_data": data_url,
                    }
                )
        if request.prompt:
            content.append({"type": "input_text", "text": request.prompt})
        return [{"role": "user", "content": content}]


def _read_data_url(path: Path, mime_type: str) -> str:
    try:
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    except OSError as exc:
        raise InputError(f"Could not read input file '{path}': {exc}") from None
    return f"data:{mime_type};base64,{encoded}"
