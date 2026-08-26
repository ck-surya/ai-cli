import base64
from pathlib import Path

import openai

from ai_cli.models import AIRequest
from ai_cli.providers.openai import OpenAIProvider


class FakeResponses:
    def __init__(self, output: str) -> None:
        self.output = output
        self.calls = []

    def create(self, **kwargs):  # type: ignore[no-untyped-def]
        self.calls.append(kwargs)
        return type("Response", (), {"output_text": self.output})()


class FakeClient:
    def __init__(self, output: str = "provider-native") -> None:
        self.responses = FakeResponses(output)


def test_passes_text_and_returns_output_unchanged() -> None:
    client = FakeClient("  exact output\n")
    request = AIRequest("openai", "test-model", "exact prompt", [], 30)

    response = OpenAIProvider("secret", client=client).run(request)

    assert client.responses.calls == [
        {"model": "test-model", "input": "exact prompt"}
    ]
    assert response.content == "  exact output\n"


def test_encodes_pdf_as_responses_file_input(tmp_path: Path) -> None:
    pdf = tmp_path / "report.pdf"
    pdf.write_bytes(b"%PDF-test")
    client = FakeClient()
    request = AIRequest(
        "openai", "test-model", "Summarize this", [pdf], 30
    )

    OpenAIProvider("secret", client=client).run(request)

    request_input = client.responses.calls[0]["input"]
    content = request_input[0]["content"]
    assert content[0] == {
        "type": "input_file",
        "filename": "report.pdf",
        "file_data": (
            "data:application/pdf;base64,"
            + base64.b64encode(b"%PDF-test").decode("ascii")
        ),
    }
    assert content[1] == {"type": "input_text", "text": "Summarize this"}


def test_encodes_image_as_responses_image_input(tmp_path: Path) -> None:
    image = tmp_path / "image.png"
    image.write_bytes(b"png")
    client = FakeClient()
    request = AIRequest("openai", "test-model", "Describe", [image], 30)

    OpenAIProvider("secret", client=client).run(request)

    content = client.responses.calls[0]["input"][0]["content"]
    assert content[0]["type"] == "input_image"
    assert content[0]["image_url"].startswith("data:image/png;base64,")


def test_configures_timeout_and_disables_sdk_retries(
    monkeypatch,
) -> None:  # type: ignore[no-untyped-def]
    constructor_calls = []
    client = FakeClient()

    def fake_constructor(**kwargs):  # type: ignore[no-untyped-def]
        constructor_calls.append(kwargs)
        return client

    monkeypatch.setattr(openai, "OpenAI", fake_constructor)
    request = AIRequest("openai", "test-model", "prompt", [], 37)

    OpenAIProvider("secret").run(request)

    assert constructor_calls == [
        {"api_key": "secret", "timeout": 37.0, "max_retries": 0}
    ]
