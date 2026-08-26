# AI CLI

## 1. Product Name

**AI CLI**

### Repository

```text
ai-cli
```

### Proposed CLI command

```text
ai
```

---

# 2. Product Definition

AI CLI is a local command-line tool that provides a simple, unified interface for interacting with different Large Language Model providers through their APIs.

The tool should allow a user to provide:

* text;
* prompts;
* files;
* documents;
* images;
* provider-specific inputs;

and send them to a selected AI provider/model.

The application standardizes how users interact with different LLM APIs.

It does **not** attempt to make different models produce identical answers.

---

# 3. Product Vision

The goal is to make calling an AI model from a local machine extremely simple.

```text
                  User
                    │
        ┌───────────┼───────────┐
        │           │           │
      Prompt      File       Options
        │           │           │
        └───────────┼───────────┘
                    │
                    ▼
                ┌──────┐
                │  ai  │
                └───┬──┘
                    │
           Provider + Model
                    │
       ┌────────────┼────────────┐
       ▼            ▼            ▼
    OpenAI       Gemini       Future
       │            │
       ▼            ▼
    Model          Model
       │            │
       └──────┬─────┘
              ▼
         Native Output
```

The user should not need to understand the implementation differences between provider SDKs.

---

# 4. Core Product Principle

AI CLI standardizes:

* CLI usage;
* provider selection;
* model selection;
* authentication;
* configuration;
* file handling;
* retries;
* timeouts;
* output handling;
* application-level errors.

The selected model controls:

* generated content;
* response style;
* response structure;
* reasoning behavior;
* provider-specific capabilities.

AI CLI must avoid semantic rewriting of model output unless explicitly requested by the user.

---

# 5. Primary Goal

The simplest workflow should look like:

```bash
ai run "Explain recursion simply"
```

or:

```bash
ai run \
  --provider openai \
  --model <model> \
  "Explain recursion simply"
```

A file may also be supplied:

```bash
ai run report.pdf
```

or:

```bash
ai run image.png
```

The architecture must allow new input types without redesigning the entire CLI.

---

# 6. Problem Statement

Each LLM provider exposes a different interface.

Differences include:

* SDK;
* authentication;
* endpoint structure;
* model names;
* file APIs;
* multimodal input formats;
* request structures;
* response structures;
* errors;
* retries;
* timeout behaviour;
* token or usage reporting.

Without AI CLI, users and developers repeatedly write provider-specific scripts.

AI CLI should provide one interface over these APIs.

---

# 7. MVP Scope

## P0

The first useful version must:

* run locally;
* use Python 3.11+;
* expose a CLI;
* support OpenAI;
* support Gemini;
* support explicit provider selection;
* support explicit model selection;
* support default provider;
* support default model;
* support environment-variable API credentials;
* support `.env`;
* support `--api-key`;
* accept text input;
* accept at least PDF/file input;
* send user input to the selected model;
* return model-generated output without semantic modification;
* support stdout;
* support writing output to a file;
* provide useful errors;
* support retries;
* support configurable timeout;
* never expose API secrets.

---

# 8. Non-Goals for MVP

The MVP should **not** contain:

* autonomous agents;
* RAG;
* vector databases;
* prompt databases;
* prompt optimization;
* prompt marketplaces;
* workflow builders;
* web UI;
* desktop UI;
* model fine-tuning;
* automatic provider fallback;
* automatic response merging;
* complex plugin architecture;
* distributed services;
* unnecessary background services.

A feature must not be added simply because it may be useful someday.

---

# 9. CLI Design

Initial commands:

```text
ai
├── run
├── providers
├── models
├── config
└── version
```

---

# 10. Run Command

Simple text:

```bash
ai run "Summarize how DNS works"
```

File:

```bash
ai run report.pdf
```

Explicit provider:

```bash
ai run report.pdf --provider openai
```

Explicit provider and model:

```bash
ai run report.pdf \
  --provider openai \
  --model <model>
```

Output file:

```bash
ai run report.pdf --output result.txt
```

Timeout:

```bash
ai run report.pdf --timeout 300
```

Dry run:

```bash
ai run report.pdf --dry-run
```

Verbose:

```bash
ai run report.pdf --verbose
```

---

# 11. Input Architecture

The CLI should support a small common input object.

Example:

```python
@dataclass
class AIRequest:
    provider: str
    model: str
    prompt: str | None
    files: list[Path]
    timeout: int
```

Do not add fields before they are needed by an implemented use case.

Provider-specific request objects must remain inside provider adapters.

---

# 12. Provider Architecture

Each provider implements one small common interface.

Example:

```python
class AIProvider(ABC):

    @abstractmethod
    def run(self, request: AIRequest) -> AIResponse:
        ...
```

Providers:

```text
OpenAIProvider
GeminiProvider
```

The core application should not know how individual provider APIs upload documents, images, or other files.

---

# 13. Provider Responsibilities

A provider adapter owns only provider-specific behaviour.

This includes:

* authentication;
* SDK initialization;
* model selection;
* input conversion;
* file upload where needed;
* API request;
* timeout behaviour;
* response extraction;
* provider error translation.

It should not contain:

* CLI rendering;
* application configuration parsing;
* output-file management;
* unrelated business logic.

---

# 14. Provider Registry

Keep the registry simple.

Example:

```python
PROVIDERS = {
    "openai": OpenAIProvider,
    "gemini": GeminiProvider,
}
```

Do not introduce dependency injection frameworks or plugin systems for two providers.

A more advanced registry should only be created if the simple dictionary becomes an actual limitation.

---

# 15. Response Architecture

The application may normalize technical access to the generated output.

Example:

```python
@dataclass
class AIResponse:
    content: str
    provider: str
    model: str
```

This is acceptable technical normalization.

The following is not acceptable unless explicitly requested:

```text
OpenAI output
     ↓
rewrite
     ↓
standard AI CLI style
```

The generated content should stay untouched.

---

# 16. Credentials

Recommended environment variables:

```text
OPENAI_API_KEY
GEMINI_API_KEY
```

Priority:

```text
--api-key
   ↓
environment variable
   ↓
.env
   ↓
configuration error
```

Secrets must never be:

* printed;
* logged;
* committed;
* placed into error messages;
* stored in generated output;
* included in debugging metadata.

---

# 17. Configuration

Recommended location:

```text
~/.config/ai-cli/config.toml
```

Example:

```toml
default_provider = "openai"
default_model = "<model>"

[settings]
timeout = 120
max_retries = 3
```

Do not build a complex configuration hierarchy for values that do not exist yet.

---

# 18. Project Structure

Initial structure:

```text
ai-cli/
│
├── README.md
├── AGENTS.md
├── CHANGELOG.md
├── LICENSE
├── pyproject.toml
├── .env.example
├── .gitignore
│
├── docs/
│   ├── product/
│   │   └── PRD.md
│   │
│   └── decisions/
│       └── README.md
│
├── src/
│   └── ai_cli/
│       ├── __init__.py
│       ├── cli.py
│       ├── runner.py
│       ├── config.py
│       ├── models.py
│       ├── registry.py
│       ├── exceptions.py
│       │
│       ├── providers/
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── openai.py
│       │   └── gemini.py
│       │
│       └── output.py
│
└── tests/
    ├── test_cli.py
    ├── test_config.py
    ├── test_runner.py
    └── providers/
        ├── test_openai.py
        └── test_gemini.py
```

This structure is a starting point, not a requirement to create empty files.

Only create modules when they contain real code.

---

# 19. Agent Engineering Guidelines

These rules apply to any AI coding agent making changes to this repository.

They should also be placed in:

```text
AGENTS.md
```

---

# 20. Rule 1 — Solve the Actual Problem

Before modifying code, identify:

```text
What exact problem is being solved?
```

Do not implement adjacent ideas unless required to solve that problem.

Bad:

```text
User asks for timeout support
→ build a generalized execution policy engine
```

Good:

```text
User asks for timeout support
→ add timeout configuration and pass it to provider calls
```

---

# 21. Rule 2 — Prefer the Smallest Correct Change

The default implementation should be the smallest understandable solution that correctly meets the requirement.

Agents must not optimize for:

* maximum abstraction;
* maximum extensibility;
* maximum number of classes;
* cleverness;
* design-pattern usage.

Optimize for:

```text
correctness
+
clarity
+
small change surface
```

---

# 22. Rule 3 — Do Not Inflate Simple Code

If something can clearly be expressed in a few lines, do not turn it into a large abstraction.

Bad:

```python
class ProviderNameResolutionStrategy:
    def resolve(self, provider):
        ...
```

when this is enough:

```python
provider = PROVIDERS.get(name)
```

Do not create:

* wrapper classes with one call;
* one-function service classes;
* interfaces with one implementation and no extension need;
* builders for trivial objects;
* factories around dictionaries;
* utility modules for one tiny function.

---

# 23. Rule 4 — Abstractions Must Earn Their Existence

Before creating an abstraction, an agent must be able to answer:

```text
What duplication, instability, or complexity does this abstraction remove today?
```

"Maybe needed later" is not sufficient.

A good abstraction normally has at least one of:

* multiple real implementations;
* repeated logic;
* a clearly unstable external boundary;
* independently testable behaviour;
* a genuine domain concept.

---

# 24. Rule 5 — Do Not Prematurely Generalize

Do not design for:

```text
20 providers
100 input types
distributed execution
future web UI
future plugins
```

while only OpenAI and Gemini are implemented.

Design the simplest system that allows the **next likely addition** without requiring a rewrite.

---

# 25. Rule 6 — Explain Why, Not What

Code already shows what the program does.

Documentation should explain:

* why a decision was made;
* what alternatives were considered;
* what constraint caused the decision;
* when the decision should be revisited.

Bad comment:

```python
# Loop through providers
for provider in providers:
```

Good comment:

```python
# Provider model discovery is intentionally best-effort because
# some APIs do not expose a reliable model-list endpoint.
```

---

# 26. Rule 7 — Decision Records

Meaningful technical decisions must be documented under:

```text
docs/decisions/
```

Use a lightweight decision record.

Example filename:

```text
0001-provider-adapter-boundary.md
```

Template:

```markdown
# Decision

## Context

What problem required a decision?

## Decision

What did we decide?

## Why

Why is this the simplest appropriate choice?

## Alternatives Considered

What realistic alternatives were rejected?

## Consequences

What becomes easier or harder because of this choice?

## Revisit When

What future condition would justify changing this decision?
```

Do not create decision records for trivial code changes.

---

# 27. When a Decision Record Is Required

Create or update a decision record when changing:

* architecture;
* provider boundaries;
* public CLI behaviour;
* persistence/storage approach;
* configuration precedence;
* dependency strategy;
* security model;
* output semantics;
* extension mechanism;
* major package structure.

Do not create one for:

* typo fixes;
* test additions;
* simple bug fixes;
* formatting;
* tiny refactors with no design impact.

---

# 28. Rule 8 — Dependencies Must Be Justified

Before adding a dependency, check whether the Python standard library or an existing dependency already solves the requirement simply.

Every new runtime dependency should have a concrete purpose.

Agents should not add dependencies for:

* trivial string formatting;
* simple retries that existing libraries already handle;
* tiny configuration helpers;
* simple file operations;
* one small utility.

Provider SDKs are acceptable because they represent unstable external API boundaries.

---

# 29. Rule 9 — Avoid Duplicate Paths

There should be one main execution path.

For example:

```text
ai run --provider openai
```

and any future shortcut:

```text
ai openai
```

must eventually call the same runner.

Do not maintain separate implementations for equivalent commands.

---

# 30. Rule 10 — Keep Provider Logic Isolated

Provider-specific behaviour belongs inside:

```text
providers/
```

The runner must not contain code such as:

```python
if provider == "openai":
    ...
elif provider == "gemini":
    ...
```

beyond simple registry resolution.

This avoids provider behaviour leaking across the application.

---

# 31. Rule 11 — Explicit Is Better Than Magical

Prefer:

```python
provider = get_provider(name)
```

over implicit global registration systems.

Prefer:

```python
timeout=120
```

over hidden dynamic behaviour.

Avoid:

* metaclass registration;
* import-time side effects;
* reflection-based provider discovery;
* hidden environment mutation;
* magical configuration merging.

Unless there is a demonstrated need.

---

# 32. Rule 12 — Error Messages Must Be Actionable

Bad:

```text
Configuration error
```

Good:

```text
OpenAI API key is not configured.

Set:
  OPENAI_API_KEY

or pass:
  --api-key
```

Errors should tell the user what happened and how to fix it.

---

# 33. Rule 13 — Security Before Convenience

Agents must verify that changes do not expose:

* API keys;
* prompts unintentionally;
* private file contents;
* provider response internals;
* authorization headers.

Logging must default to safe operational information.

---

# 34. Rule 14 — Test Behaviour, Not Implementation Details

Tests should verify user-visible or contract-level behaviour.

Good:

```text
Correct provider is selected.
Prompt is passed unchanged.
Missing credentials fail.
Output is written exactly.
Retry occurs for temporary failures.
```

Avoid tests that make harmless internal refactoring unnecessarily difficult.

---

# 35. Rule 15 — External APIs Must Be Mocked in Unit Tests

Normal tests must not:

* spend API credits;
* depend on internet availability;
* require real credentials;
* generate non-deterministic model responses.

Real-provider integration tests must be explicitly opted into.

---

# 36. Rule 16 — No Dead Architecture

Do not add:

* unused base classes;
* empty directories;
* placeholder managers;
* future feature interfaces;
* configuration keys with no implementation;
* TODO modules that are never called.

Repository structure should reflect software that actually exists.

---

# 37. Rule 17 — Delete Complexity When Requirements Change

Agents are allowed and encouraged to remove:

* obsolete abstractions;
* unused helpers;
* old compatibility code;
* duplicate implementations;
* dead configuration.

Backward compatibility should only be maintained when it is an actual product requirement.

---

# 38. Rule 18 — Keep Functions Focused

A function should usually perform one understandable operation.

Do not split a five-line readable function into five one-line helper functions.

Likewise, do not place unrelated provider, configuration, output, and validation logic into one giant function.

The goal is readability, not arbitrary function size.

---

# 39. Rule 19 — Comments Are Not a Substitute for Clear Code

Prefer:

```python
retryable = status_code in RETRYABLE_STATUS_CODES
```

instead of:

```python
x = status_code in codes  # check if error should retry
```

Comments should document reasoning or constraints that cannot be understood directly from the code.

---

# 40. Rule 20 — Every Feature Starts With a Requirement

Before implementing a meaningful feature, the agent should record in its work:

```text
Requirement:
Why:
Minimal implementation:
Affected contracts:
Tests needed:
Documentation/decision update needed:
```

This may be written in the PR description rather than committed into the repository.

---

# 41. Agent Pre-Change Checklist

Before writing code, an AI agent must ask:

```text
1. What exact behaviour is requested?
2. Does this behaviour already exist?
3. What is the smallest place to implement it?
4. Can an existing function/module handle it?
5. Am I creating an abstraction only for hypothetical future use?
6. Am I adding a dependency unnecessarily?
7. Does this change affect a documented architectural decision?
8. What behaviour should be tested?
```

---

# 42. Agent Post-Change Checklist

Before considering work complete:

```text
1. Does the implementation satisfy only the requested scope?
2. Can any newly added code be removed without losing behaviour?
3. Is there duplicate logic?
4. Are names understandable?
5. Are provider-specific details isolated?
6. Are secrets protected?
7. Do tests cover the behaviour?
8. Did public behaviour change?
9. If architecture changed, was the decision documented?
10. Does README/user documentation need updating?
```

---

# 43. Simplicity Review

For every non-trivial pull request, the agent should perform one final pass specifically asking:

```text
Could this implementation be substantially simpler?
```

Look for:

* unnecessary classes;
* unnecessary helpers;
* repeated validation;
* duplicated configuration;
* wrappers around one function;
* premature extensibility;
* redundant comments;
* excessive exception types;
* unnecessary dependency additions.

Simplify before requesting review.

---

# 44. Pull Request Requirements

Each meaningful PR should explain:

```markdown
## Problem

What user/developer problem does this solve?

## Change

What was changed?

## Why This Approach

Why is this the simplest suitable implementation?

## Tests

What verifies the behaviour?

## Decisions

Decision record added/updated, or "Not required".

## Out of Scope

What related work was intentionally not implemented?
```

This makes the reasoning behind changes visible without filling source code with unnecessary comments.

---

# 45. Coding Style

Use:

* Python type hints;
* clear descriptive names;
* small public interfaces;
* standard Python conventions;
* `pathlib.Path` for filesystem paths;
* dataclasses or Pydantic only when their benefits are real;
* explicit exceptions for meaningful application failure categories.

Avoid:

* clever metaprogramming;
* broad `except Exception`;
* global mutable state;
* wildcard imports;
* hidden side effects;
* over-engineered class hierarchies.

---

# 46. Technology Stack

Recommended MVP:

```text
Python          3.11+
CLI             Typer
Configuration   TOML
Environment     python-dotenv
Testing         pytest
Packaging       pyproject.toml
Providers       Official SDKs
```

Pydantic should only be added if configuration/data validation becomes complex enough to justify it.

Do not add it automatically just because it is common.

---

# 47. Retry Policy

Default:

```text
3 retries
```

Retry:

* temporary network failures;
* temporary provider errors;
* supported rate-limit responses.

Do not retry:

* invalid credentials;
* invalid model;
* invalid input;
* missing file;
* invalid configuration;
* unsupported provider.

Retry behaviour should live in one clear execution layer.

---

# 48. Timeout

Default:

```text
120 seconds
```

Example:

```bash
ai run report.pdf --timeout 300
```

Provider adapters should respect the resolved timeout where their SDK supports it.

---

# 49. Logging

Default logging should be minimal.

Allowed:

```text
Provider: openai
Model: ...
Sending request
Response received
Duration: ...
```

Do not log:

* API key;
* Authorization header;
* prompt contents;
* file contents;
* full provider request payloads.

---

# 50. Dry Run

Example:

```bash
ai run report.pdf --dry-run
```

Possible output:

```text
Provider: openai
Model: <model>
Input: report.pdf
Credentials: configured

No API request was sent.
```

---

# 51. Output

Default:

```text
model-generated content
```

Do not automatically print:

```text
AI Response:
```

Normal output should be usable directly in shell pipelines.

Example:

```bash
ai run report.pdf > result.txt
```

---

# 52. Extensibility

A future provider should require approximately:

```text
1. Add provider adapter.
2. Register provider.
3. Add credential configuration.
4. Add tests.
5. Update supported-provider docs.
```

If adding a provider requires major CLI changes, provider boundaries should be reconsidered.

---

# 53. Future Capabilities

Possible future additions:

* Anthropic;
* OpenRouter;
* Ollama;
* Azure OpenAI;
* Vertex AI;
* Bedrock;
* multiple files;
* images;
* audio;
* stdin;
* structured output;
* batch execution;
* provider comparison;
* profiles.

These are possibilities, not current requirements.

Do not implement architectural machinery for them until one becomes real work.

---

# 54. MVP Acceptance Criteria

The MVP is complete when:

```bash
ai run "Hello"
```

can successfully call the configured default model.

The following also works:

```bash
ai run \
  --provider openai \
  --model <model> \
  "Explain this"
```

And:

```bash
ai run document.pdf \
  --provider gemini \
  --model <model>
```

Additionally:

* environment credentials work;
* `.env` works;
* `--api-key` works;
* output file works;
* timeout works;
* retries work;
* invalid provider errors are actionable;
* missing credentials errors are actionable;
* secrets never appear in logs;
* providers are isolated behind adapters;
* normal unit tests do not call external APIs.

---

# 55. Definition of Done for Any Feature

A feature is complete only when:

```text
Requirement implemented
+
tests passing
+
no unnecessary architecture introduced
+
user-facing docs updated if needed
+
decision documented if architectural
+
simplicity review completed
```

---

# 56. Repository Philosophy

The repository should remain boring in a good way.

A new engineer or AI agent should be able to open the project and quickly understand:

```text
where CLI input enters
→ where configuration resolves
→ where provider is selected
→ where API request happens
→ where response leaves
```

There should be very little hidden behaviour.

---

# 57. Guiding Principle

When choosing between:

```text
clever and flexible
```

and:

```text
simple and sufficient
```

choose:

```text
simple and sufficient
```

until the real requirements demonstrate that more complexity is necessary.

---

# 58. Product Definition in One Sentence

> **AI CLI is a local command-line interface for accessing multiple LLM providers through a common API-facing workflow while preserving provider-native behaviour and keeping the implementation intentionally simple, explicit, secure, and easy to extend.**
