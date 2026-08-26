from pathlib import Path

from ai_cli.output import write_output


def test_writes_file_content_exactly(tmp_path: Path) -> None:
    destination = tmp_path / "result.txt"
    content = "first line\nsecond line without a final newline"

    write_output(content, destination)

    assert destination.read_text(encoding="utf-8") == content


def test_writes_stdout_content_exactly(capsys: object) -> None:
    content = "native output without added label or newline"

    write_output(content)

    captured = capsys.readouterr()  # type: ignore[attr-defined]
    assert captured.out == content
    assert captured.err == ""
