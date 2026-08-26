# Decision: Use small TOML settings and explicit credential precedence

## Context

The CLI needs provider/model defaults, timeout and retry settings, local `.env`
support, environment credentials, and a one-run key override without exposing
secrets.

## Decision

Non-secret defaults live in `~/.config/ai-cli/config.toml`. Credentials resolve
in this order: `--api-key`, the provider environment variable, then the current
directory's `.env`. API keys are passed directly to provider constructors and do
not enter application request or response objects.

## Why

One TOML file and two provider-specific environment names implement every current
configuration use case with standard, visible precedence. Keeping keys separate
from dataclasses makes accidental logging and serialization less likely.

## Alternatives Considered

- Storing API keys in TOML would make long-lived secret files the normal path.
- A layered configuration framework would duplicate behavior available in the
  standard library and `python-dotenv`.
- Hidden provider or model defaults would become stale and make requests less
  predictable.

## Consequences

Users must configure a default model or pass `--model`. The CLI can safely show
resolved settings without redaction logic because settings contain no secrets.

## Revisit When

Revisit if profiles, OS credential stores, or provider-specific default models
become explicit product requirements.
