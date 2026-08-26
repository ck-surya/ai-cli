# Engineering Guidelines

These repository rules apply to human and AI contributors.

## Scope and simplicity

- Start from an explicit requirement and solve only the actual problem.
- Prefer the smallest correct, understandable change. Optimize for correctness,
  clarity, and a small change surface rather than maximum abstraction.
- An abstraction must remove current duplication, isolate a genuinely unstable
  boundary, represent a real domain concept, or have multiple implementations.
  Possible future needs are not sufficient.
- Do not add dead architecture, placeholder modules, generalized plugin systems,
  or compatibility paths without a current requirement.
- Keep one execution path. Equivalent CLI commands must reach the same runner.
- Delete obsolete helpers and abstractions when requirements change.
- Perform a final simplicity pass on every non-trivial change.

## Architecture

- Provider authentication, SDK setup, input conversion, API calls, timeouts,
  response extraction, and provider error translation belong in `providers/`.
- CLI rendering, configuration parsing, retry orchestration, and output-file
  handling do not belong in provider adapters.
- Resolve providers explicitly through the registry. Do not use reflection,
  metaclass registration, import-time side effects, or dependency-injection
  frameworks.
- Keep application request and response contracts small. Do not add fields until
  an implemented use case needs them.
- Preserve model-generated content. Technical access may be normalized, but the
  content must not be rewritten unless the user explicitly requests it.

## Dependencies and decisions

- Check the standard library and existing dependencies before adding another
  dependency. Provider SDKs are appropriate unstable external boundaries.
- Add or update a lightweight record in `docs/decisions/` when changing
  architecture, provider boundaries, public CLI behavior, configuration
  precedence, dependencies, security, persistence, output semantics, extension
  mechanisms, or major package structure.
- Comments and documentation should explain constraints and reasons, not narrate
  obvious code.

## Errors, security, and logging

- Errors must say what happened and how the user can fix it.
- Never print, log, persist, or include API keys or authorization headers in
  errors, output, request dataclasses, or debugging metadata.
- Do not log prompt text, file contents, or full provider request payloads.
- Prefer explicit application-level exception categories. Avoid broad exception
  handling except at a justified unstable external boundary.

## Tests and completion

- Test user-visible behavior and contracts rather than internal implementation.
- Unit tests must mock external APIs and must not spend credits, require real
  credentials, depend on internet access, or produce nondeterministic output.
- Cover provider selection, unchanged prompt/output, missing credentials, file
  handling, timeout propagation, retries, and actionable errors as applicable.
- A change is done only when requirements are implemented, tests pass, user docs
  are current, required decisions are recorded, secrets remain protected, and
  unnecessary complexity has been removed.

Before coding, record: requirement, reason, minimal implementation, affected
contracts, tests needed, and whether documentation or a decision record changes.
Before finishing, check for duplicate logic, unclear names, provider leakage,
secret exposure, missing tests, public behavior changes, and removable code.
