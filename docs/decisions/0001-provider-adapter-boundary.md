# Decision: Use explicit provider adapters and one shared runner

## Context

OpenAI and Gemini use different SDKs, multimodal payloads, error types, and
timeout configuration. The CLI still needs one predictable execution path.

## Decision

Each provider implements the small `AIProvider.run(AIRequest) -> AIResponse`
boundary. An explicit dictionary maps provider names to adapter classes. One
runner resolves the adapter and owns application-level retry attempts.

## Why

Two adapters are enough to justify a shared contract, while a dictionary and a
single retry loop are the smallest mechanisms that isolate provider behavior.
Keeping retries above adapters also gives both SDKs the same configured meaning.

## Alternatives Considered

- Provider conditionals in the runner would leak SDK behavior into core code.
- Automatic discovery or a plugin framework would add machinery for hypothetical
  providers.
- SDK-owned retries would give the same CLI setting different semantics between
  providers and could cause nested retries.

## Consequences

Adding a provider requires an adapter and one registry entry. Adapters translate
provider failures into safe application errors. The shared runner can retry only
failures explicitly marked temporary.

## Revisit When

Revisit if the registry becomes a real extension bottleneck or providers require
substantially different execution policies that cannot remain isolated.
