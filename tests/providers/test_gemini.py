from pathlib import Path

from google import genai

from ai_cli.models import AIRequest
from ai_cli.providers.gemini import GeminiProvider


class FakeModels:
    def __init__(self, output: str) -> None:
        self.output = output
        self.calls = []

    def generate_content(self, **kwargs):  # type: ignore[no-untyped-def]
        self.calls.append(kwargs)
        return type("Response", (), {"text": self.output})()


class FakeClient:
    def __init__(self, output: str = "provider-native") -> None:
        self.models = FakeModels(output)


def test_passes_text_and_returns_output_unchanged() -> None:
    client = FakeClient("  exact output\n")
    request = AIRequest("gemini", "test-model", "exact prompt", [], 30)

    response = GeminiProvider("secret", client=client).run(request)

    assert client.models.calls == [
        {"model": "test-model", "contents": "exact prompt"}
    ]
    assert response.content == "  exact output\n"


def test_encodes_pdf_as_inline_part(tmp_path: Path) -> None:
    pdf = tmp_path / "report.pdf"
    pdf.write_bytes(b"%PDF-test")
    client = FakeClient()
    request = AIRequest(
        "gemini", "test-model", "Summarize this", [pdf], 30
    )

    GeminiProvider("secret", client=client).run(request)

    contents = client.models.calls[0]["contents"]
    assert contents[0].inline_data.mime_type == "application/pdf"
    assert contents[0].inline_data.data == b"%PDF-test"
    assert contents[1] == "Summarize this"


def test_configures_timeout_in_sdk_milliseconds(
    monkeypatch,
) -> None:  # type: ignore[no-untyped-def]
    constructor_calls = []
    client = FakeClient()

    def fake_constructor(**kwargs):  # type: ignore[no-untyped-def]
        constructor_calls.append(kwargs)
        return client

    monkeypatch.setattr(genai, "Client", fake_constructor)
    request = AIRequest("gemini", "test-model", "prompt", [], 37)

    GeminiProvider("secret").run(request)

    assert constructor_calls[0]["api_key"] == "secret"
    assert constructor_calls[0]["http_options"].timeout == 37_000
