# AI CLI

AI CLI is a small local command-line interface for sending prompts and files to
OpenAI or Gemini. It gives both providers the same CLI workflow while preserving
the text each model returns.

## Requirements

- Python 3.11+
- An OpenAI or Gemini API key

## Install

From this repository:

```bash
python -m pip install -e .
```

For development and tests:

```bash
python -m pip install -e '.[dev]'
```

## Configure

API keys can be set in the process environment:

```bash
export OPENAI_API_KEY="..."
export GEMINI_API_KEY="..."
```

Alternatively, copy `.env.example` to `.env`. A key passed with `--api-key`
takes precedence over the process environment, and the process environment
takes precedence over `.env`. Keys are never printed by the CLI.

Create `~/.config/ai-cli/config.toml` to configure defaults:

```toml
default_provider = "openai"
default_model = "<model>"

[settings]
timeout = 120
max_retries = 3
```

Model names are provider-owned and change over time, so AI CLI does not hardcode
a model catalog. Pass `--model` or configure `default_model`.

## Use

Send text with configured defaults:

```bash
ai run "Explain recursion simply"
```

Select a provider and model explicitly:

```bash
ai run "Explain recursion simply" --provider openai --model <model>
```

Send a file. With no `--prompt`, AI CLI uses the minimal instruction
`Analyze the attached file.`:

```bash
ai run report.pdf --provider gemini --model <model>
ai run image.png --prompt "Describe this diagram" --model <model>
```

Write the model output without adding a heading or rewriting it:

```bash
ai run report.pdf --output result.txt
ai run "Summarize DNS" > result.txt
```

Validate provider, model, input, and credentials without making a request:

```bash
ai run report.pdf --dry-run
```

Set a timeout or show safe operational details on stderr:

```bash
ai run report.pdf --timeout 300 --verbose
```

Other commands:

```bash
ai providers
ai models
ai config
ai version
```

`ai models` shows the configured model selection; it does not call a provider's
model-list endpoint. Normal output contains only model-generated content, making
it safe to use in shell pipelines. Verbose output never includes API keys,
prompts, file contents, or provider request payloads.

## Development

```bash
pytest
```

Unit tests use fake provider clients and do not require credentials or network
access. Product requirements are recorded in [PRD.md](PRD.md), and meaningful
technical decisions are under `docs/decisions/`.
