# Nevermine LLM Gateway — Architecture Overview

> Status: LAB baseline candidate — `gateway-lab-v1`
> Repository: `rvergeli80/ai-lab`
> Component: `services/gateway_manager`
> Role: Vendor-neutral LLM access layer for Nevermine Platform

---

## 1. Purpose

The Nevermine LLM Gateway provides a unified, vendor-neutral access layer to multiple Large Language Model providers.

Its purpose is to prevent Nevermine agents, services and applications from depending directly on a specific LLM vendor, model host or deployment mode.

Consumers should request a capability or, when necessary, an explicit model. The Gateway owns policy enforcement, routing, execution, fallback, normalization and usage accounting.

The long-term Nevermine architecture supports three execution modes:

1. Nevermine Managed AI.
2. Bring Your Own Key (BYOK).
3. Local / Private inference.

The current implementation is developed and validated inside the AI LAB repository.

The LAB implementation is experimental infrastructure. It is not, by itself, canonical Nevermine Platform implementation.

---

## 2. Core Principle

Consumers should not need to know:

- which provider hosts a model;
- whether execution is local or remote;
- whether a provider is temporarily unavailable;
- whether a paid model is allowed by budget policy;
- whether fallback is required;
- how provider-specific responses are normalized;
- how cost and usage are persisted.

Conceptually:

```python
response = gateway.complete(
    Request(
        capability="coding",
        prompt="Implement this endpoint.",
    )
)
```

The Gateway owns model resolution, policy enforcement, routing and execution.

---

## 3. Current Architecture

```text
Application / Agent / Service
            |
            v
        LLM Gateway
            |
      +-----+------+
      |            |
      v            v
 Capability    Explicit Model
 Routing           |
      |            |
      +-----+------+
            |
            v
       Budget Policy
            |
            v
 Provider Availability
            |
            v
      Fallback Chain
            |
      +-----+------+
      |            |
      v            v
 Remote Providers  Local
      |            |
 LiteLLM Adapter   Ollama Adapter
      |            |
 OpenRouter/...    Ollama
                    |
                Local models
            |
            v
     Normalized Response
            |
            v
        Usage Ledger
```

The current Gateway separates:

- model definition;
- provider definition;
- provider availability;
- model selection;
- capability routing;
- budget enforcement;
- retry classification;
- fallback;
- provider execution;
- pricing;
- usage accounting;
- configuration validation;
- diagnostics;
- normalized responses.

---

## 4. Repository and Configuration

Repository:

```text
rvergeli80/ai-lab
```

Local working copy:

```text
~/lab
```

Gateway service:

```text
services/gateway_manager/
```

Important configuration locations:

```text
config/models/
config/routing/
config/budget/
config/pricing/
```

Runtime state:

```text
runtime/gateway/
```

Architecture documentation:

```text
docs/architecture/GATEWAY_OVERVIEW.md
```

---

## 5. Model Catalog

The model catalog lives under:

```text
config/models/
```

Provider-specific definitions live under:

```text
config/models/providers/
```

Current provider configuration files include:

```text
anthropic.yaml
deepseek.yaml
google.yaml
groq.yaml
lmstudio.yaml
mistral.yaml
ollama.yaml
openai.yaml
openrouter.yaml
together.yaml
xai.yaml
```

A model definition includes:

- provider;
- provider model identifier;
- status;
- capabilities;
- context window;
- priority;
- tags.

Example:

```yaml
laguna-xs-2.1:
  provider: ollama
  model: laguna-xs-2.1:latest
  status: enabled

  capabilities:
    - chat
    - coding
    - reasoning
    - tools

  context_window: 262144
  priority: 260

  tags:
    - local
    - coding
    - agentic
    - reasoning
```

Downloaded model weights are runtime assets and must never be committed to Git.

---

## 6. Model Registry

`ModelRegistry` provides programmatic access to the consolidated model catalog.

Responsibilities include:

- model lookup;
- alias resolution;
- enabled-model discovery;
- capability filtering;
- tag filtering.

Conceptually:

```text
CatalogLoader
     |
     v
ModelRegistry
     |
     v
Gateway components
```

---

## 7. Provider Registry

The Provider Registry represents the providers understood by the Gateway.

Current provider definitions include:

- OpenAI;
- Anthropic;
- Google;
- OpenRouter;
- Groq;
- Mistral;
- DeepSeek;
- Together;
- xAI;
- Ollama;
- LM Studio.

Credentials are supplied through environment variables and must never be stored in the repository.

Examples:

```text
OPENAI_API_KEY
ANTHROPIC_API_KEY
OPENROUTER_API_KEY
```

---

## 8. Provider Availability

`ProviderAvailability` determines which providers can currently be used.

Remote providers depend on the corresponding runtime credential being present.

Ollama availability is checked against the local Ollama service.

Example:

```text
http://localhost:11434/api/version
```

A runtime environment may report:

```python
{"openrouter", "ollama"}
```

Unavailable providers are excluded from normal capability routing.

Availability and authorization are separate concerns:

- availability determines whether a provider can currently be used;
- policy determines whether a model is allowed.

---

## 9. Routing Policies

Routing configuration lives at:

```text
config/routing/policies.yaml
```

Current capability policies include:

- coding;
- reasoning;
- chat;
- vision.

Current routing strategy:

```text
fallback
```

Example:

```yaml
coding:
  strategy: fallback
  candidates:
    - tier: premium
    - tier: paid
    - tier: free
    - tier: local
```

Preferred abstraction:

```text
Agent -> capability -> Gateway
```

Avoid:

```text
Agent -> hardcoded vendor/model
```

---

## 10. Model Tiers

The current routing model uses four logical tiers.

### premium

Higher-value paid models.

### paid

Standard paid remote models.

### free

Remote models explicitly classified/tagged as free.

### local

Models executed through local infrastructure.

Ollama models are treated as local.

An open-weight model is not automatically free when hosted remotely.

---

## 11. Budget Policy

Budget configuration lives at:

```text
config/budget/budgets.yaml
```

Current LAB baseline:

```yaml
budget:
  enabled: true
  currency: USD

  default:
    daily: 2.00
    monthly: 30.00
```

Paid and premium tiers can enforce monetary limits.

Free and local tiers can remain available without monetary enforcement.

`BudgetPolicy` reads persisted usage from the Usage Ledger and calculates spend for:

- the current UTC day;
- the current UTC month.

If accumulated spend reaches a configured limit, paid/premium candidates are excluded and normal routing can continue through free/local tiers.

Current behavior is intentionally reactive:

```text
accumulated spend >= limit
            |
            v
       model blocked
```

The Gateway does not yet estimate the cost of the next inference before execution.

Costs in different currencies are never silently combined.

---

## 12. Explicit Model Requests

An explicit model request bypasses capability selection but does not bypass Gateway policy.

Example:

```python
Request(
    model="gpt-5",
    prompt="...",
)
```

Flow:

```text
explicit model
      |
      v
model lookup
      |
      v
budget policy
      |
      v
execution
```

A paid model cannot be used explicitly to bypass spending limits.

---

## 13. Fallback Router

`FallbackRouter` builds an ordered candidate chain.

Decision inputs:

```text
requested capability
        +
provider availability
        +
budget permission
        +
model tier
        +
priority
```

The router determines candidate order. It does not execute inference.

The CLI capability-selection path uses the same routing logic to avoid CLI/runtime inconsistencies.

---

## 14. Gateway Runtime

Primary runtime API:

```python
Gateway.complete(Request)
```

High-level flow:

1. resolve an explicit model when requested;
2. enforce budget policy for explicit models;
3. otherwise obtain candidates from `FallbackRouter`;
4. execute candidates sequentially;
5. classify failures through `RetryPolicy`;
6. fall back only when policy allows;
7. normalize the provider response;
8. calculate usage cost when possible;
9. persist usage;
10. return a provider-independent `Response`.

---

## 15. Automatic Fallback

Automatic fallback is implemented and covered by automated tests.

Conceptually:

```text
preferred candidate
       |
       v
   execution
       |
    failure
       |
       v
  RetryPolicy
       |
  retryable?
    /     \
   no     yes
   |       |
 raise     v
       next candidate
             |
             v
          success
```

Failed attempts and successful fallback attempts are persisted in the Usage Ledger.

---

## 16. Retry Policy

Retry classification is centralized through `RetryPolicy`.

Configured retryable categories live in:

```text
config/routing/policies.yaml
```

Current categories:

```text
rate_limit
quota_exceeded
provider_unavailable
timeout
model_unavailable
```

Examples include:

- HTTP 429 -> `rate_limit`;
- HTTP 402 -> `quota_exceeded`;
- timeout exceptions -> `timeout`;
- connection failures -> `provider_unavailable`;
- model-not-found conditions -> `model_unavailable`;
- selected 5xx responses -> `provider_unavailable`.

Unknown application errors are not automatically retried.

This prevents programming errors from silently causing execution against another model.

---

## 17. Provider Adapters

Current adapters:

```text
LiteLLMAdapter
OllamaAdapter
```

### LiteLLMAdapter

Used for remote providers.

The currently validated remote path is OpenRouter.

LiteLLM also provides installed pricing metadata used by `PricingService` when no explicit LAB price is configured.

### OllamaAdapter

Executes local inference through Ollama:

```text
Gateway
   |
OllamaAdapter
   |
localhost:11434
   |
local model
```

The adapter uses:

```text
keep_alive = 30m
```

to reduce unnecessary model reloads.

---

## 18. Local Models

The currently integrated local model is:

```text
laguna-xs-2.1
```

Downloading a model into Ollama does not automatically register it as a Gateway candidate.

For Ollama requests, when `think` is not explicitly supplied, the Gateway defaults to:

```text
think = false
```

This is an execution default, not a statement about model capability.

---

## 19. Normalized Domain Objects

Provider-independent domain objects include:

```text
Model
Request
Response
TokenUsage
UsageRecord
```

`Request` currently supports:

```text
prompt
capability
tag
model
temperature
max_tokens
think
project
tenant
```

Example response:

```python
Response(
    model="laguna-xs-2.1",
    provider="ollama",
    content="...",
    usage=TokenUsage(
        prompt_tokens=54,
        completion_tokens=6,
        total_tokens=60,
    ),
    finish_reason="stop",
    latency_ms=310,
)
```

---

## 20. Usage Ledger

The Usage Ledger is implemented.

Default runtime database:

```text
runtime/gateway/usage.db
```

Current abstractions:

```text
UsageRecord
UsageRepository
SQLiteUsageRepository
```

Persisted fields include:

```text
id
timestamp
provider
model
prompt_tokens
completion_tokens
total_tokens
cost_amount
cost_currency
latency_ms
capability
project
tenant
success
fallback
error_type
```

Architecture:

```text
Gateway
   |
   +-- Routing
   |
   +-- BudgetPolicy
   |
   +-- PricingService
   |
   +-- Usage
        |
        +-- UsageRecord
        +-- UsageRepository
        +-- SQLiteUsageRepository
```

The repository abstraction prevents Gateway behavior from depending directly on SQLite.

The repository can:

- add usage records;
- list records between timestamps;
- calculate successful cost totals for a time range and currency.

Failed inference attempts do not contribute to successful cost totals.

---

## 21. Usage Ledger Resilience

Usage persistence is intentionally non-blocking for successful inference.

If the model returns a valid response but the Ledger write fails:

```text
LLM inference succeeds
        |
        v
ledger write attempted
        |
      failure
        |
        v
warning logged
        |
        v
response still returned
```

The accounting layer therefore does not become a single point of failure for valid inference.

---

## 22. Pricing

Pricing configuration lives at:

```text
config/pricing/models.yaml
```

`PricingService` supports:

1. explicit LAB pricing;
2. LiteLLM model-cost metadata.

Remote LiteLLM-derived prices are treated as:

```text
USD
```

Local Ollama execution can be explicitly configured at zero monetary cost.

Usage records store:

```text
cost_amount
cost_currency
```

No universal currency is assumed.

The repository never silently combines different currencies.

No FX conversion layer exists in the LAB baseline.

---

## 23. Configuration Validation

`GatewayConfigValidator` performs cross-configuration validation.

Current validation includes:

```text
models -> registered providers
model status
provider model identifiers
enabled model capabilities
context windows
priorities

aliases -> valid targets
alias/model collisions

routing strategies
routing candidates
known tiers
capability/model coverage
fallback max attempts
retryable error vocabulary

pricing -> known models
pricing/provider consistency
pricing values

budget currency
daily/monthly limits
known budget tiers
budget behavior
remote explicit-price currency compatibility
```

Validation distinguishes:

```text
ERROR
WARNING
```

Current validated configuration:

```text
errors   0
warnings 0
status   VALID
```

---

## 24. Gateway CLI

Available commands:

```text
gateway doctor
gateway usage
gateway models
gateway model <name>
gateway select
```

Examples:

```bash
gateway select --capability coding
gateway select --capability chat
gateway usage
gateway doctor
```

`gateway select` uses provider availability, routing policy and budget policy for capability-based selection.

This keeps CLI diagnostics aligned with runtime behavior.

---

## 25. Gateway Doctor

`gateway doctor` provides operational health diagnostics.

It checks:

- model catalog;
- model registry;
- routing policies;
- pricing catalog;
- Usage Ledger;
- budget policy;
- integral configuration validation;
- provider availability;
- enabled-model availability;
- budget limits.

Validated current result:

```text
Configuration validation
------------------------------------------------------------
errors               0
warnings             0
status               VALID

Result
------------------------------------------------------------
HEALTHY
```

Exit codes:

```text
0 = HEALTHY
1 = DEGRADED
2 = UNHEALTHY
```

This supports shell automation and future CI/operational checks.

---

## 26. Gateway Usage CLI

`gateway usage` exposes persisted accounting without requiring direct SQLite access.

Current summaries cover:

```text
Today
Month
```

Metrics include:

```text
requests
successful
failed
fallbacks
prompt tokens
completion tokens
total tokens
cost by currency
unknown costs
```

Costs remain separated by currency.

---

## 27. Security Rules

Secrets must NEVER be committed to Git.

Ignored secret/runtime locations include:

```text
credentials/.env
config/env/.env.local
runtime/
```

The repository also excludes:

- downloaded model weights;
- Docker volumes;
- backups;
- virtual environments;
- caches;
- runtime logs.

Credentials and runtime databases are not repository content.

---

## 28. Current Validated Runtime

At the `gateway-lab-v1` baseline candidate, four catalog models are enabled:

```text
gpt-5
gpt-5-mini
openrouter-gemma
laguna-xs-2.1
```

Current pre-baseline environment validation:

```text
OpenAI       unavailable / no credentials
OpenRouter   available
Ollama       available
```

Observed policy selection:

```text
coding -> openrouter-gemma
chat   -> laguna-xs-2.1
```

Current doctor result:

```text
errors   0
warnings 0
status   VALID

Result
HEALTHY
```

---

## 29. Automated Validation

Current suite:

```text
25 passing tests
```

Coverage includes:

- budget policy;
- catalog loading;
- CLI/runtime routing consistency;
- CLI usage reporting;
- integral configuration validation;
- doctor exit codes;
- explicit-model budget enforcement;
- automatic fallback;
- Gateway usage accounting;
- Usage Ledger failure resilience;
- model registry;
- pricing service;
- provider registry;
- retry policy;
- selection engine;
- SQLite usage repository.

The baseline is not ready if the test suite is failing.

---

## 30. Nevermine Execution Modes — Target Direction

### Nevermine Managed AI

Nevermine manages provider access and can meter customer usage.

Commercial customer billing is not implemented by the LAB baseline.

### BYOK — Bring Your Own Key

The customer supplies provider credentials.

The full customer credential lifecycle is not implemented by the LAB baseline.

### Local / Private

Nevermine can target private/customer inference infrastructure.

Possible future backends include:

```text
Ollama
vLLM
LM Studio
private cloud GPU
on-premise inference
```

The current LAB validates the Ollama local pattern.

---

## 31. Deferred by Design

The following capabilities are intentionally outside `gateway-lab-v1`.

They are not forgotten defects.

### Commercial capabilities

```text
customer billing
Nevermine Managed AI commercial metering
full BYOK credential lifecycle
```

### Advanced budget scopes

```text
project budget
tenant budget
user budget
```

`project` and `tenant` are already persisted so future policy can build on real usage without redesigning the Ledger.

### Advanced routing optimization

Future routing may consider:

```text
CAPABILITY
QUALITY
COST
PRIVACY
LATENCY
```

Potential future profiles:

```text
Fast
Economy
Maximum Quality
Private
Balanced
```

### Predictive cost control

Pre-flight estimation or reservation of the next inference cost is deferred.

### Foreign Exchange

No FX conversion is performed.

Different currencies remain isolated.

---

## 32. Target Nevermine Architecture

```text
                 Nevermine Platform
                         |
                    Agent Engine
                         |
                  LLM Orchestrator
                         |
                    LLM Gateway
                         |
          +--------------+--------------+
          |              |              |
          v              v              v
    Managed AI          BYOK        Local/Private
          |              |              |
   Nevermine infra   customer keys   private infra
          |
      LLM providers
```

The LAB Gateway validates infrastructure patterns intended to inform Nevermine Platform.

It must not become a second canonical Nevermine Platform.

---

## 33. Golden Rule

Never add a direct provider dependency to a Nevermine agent when the operation can be expressed through the LLM Gateway.

Prefer:

```text
Agent
  |
Capability
  |
Gateway
```

Avoid:

```text
Agent
  |
Hardcoded provider/model
```

Provider selection is infrastructure.

Agent behavior is domain logic.

---

## 34. `gateway-lab-v1` Closure Criteria

The LAB baseline can be frozen as `gateway-lab-v1` when all of the following are true:

```text
[ ] integral configuration validation passes
[ ] gateway doctor reports HEALTHY
[ ] gateway doctor exits with code 0
[ ] automated test suite passes
[ ] real local Ollama smoke succeeds
[ ] real remote OpenRouter smoke succeeds
[ ] successful smoke usage is persisted
[ ] gateway usage can read persisted accounting
[ ] architecture documentation matches implementation
[ ] Git working tree is clean after baseline commit
[ ] gateway-lab-v1 Git tag is created
```

No new feature should be added merely to postpone closure once these criteria are satisfied.

Future functionality should start a new development cycle.

---

## 35. Implementation Status Summary

### Implemented

- model catalog;
- aliases;
- model registry;
- provider registry;
- provider availability;
- capability-based routing;
- tier-based routing;
- availability-aware routing;
- budget-aware routing;
- real daily/monthly accumulated-spend enforcement;
- explicit-model budget enforcement;
- LiteLLM adapter;
- Ollama adapter;
- normalized Request/Response objects;
- normalized token usage;
- centralized retry policy;
- automatic fallback;
- local Ollama execution;
- remote OpenRouter execution;
- Usage Ledger;
- SQLite persistence;
- project/tenant usage metadata;
- pricing service;
- currency-aware cost storage;
- non-blocking usage persistence;
- integral configuration validation;
- operational doctor CLI;
- usage CLI;
- routing-aware select CLI;
- diagnostic exit codes.

### Validated

- 25 automated tests passing;
- catalog and registry behavior;
- provider registry;
- routing policy;
- budget policy;
- accumulated cost enforcement;
- explicit-model budget enforcement;
- retry classification;
- fallback behavior;
- usage persistence;
- usage persistence resilience;
- pricing behavior;
- CLI/runtime routing consistency;
- configuration validation;
- doctor health status and exit codes;
- OpenRouter availability;
- Ollama availability.

### Deferred by Design

- customer billing;
- full BYOK credential lifecycle;
- Nevermine Managed AI commercial metering;
- project/tenant/user budget enforcement;
- predictive per-request cost reservation;
- FX conversion;
- policy optimization across quality/cost/privacy/latency;
- user-facing routing profiles.

---

## 36. Source of Truth

This document describes the Gateway architecture at a high level.

When there is a discrepancy between this document and executable behavior, the implementation and automated tests determine current LAB technical behavior.

When Gateway behavior changes, this document must be updated in the same development cycle.

Nevermine Platform canonical architecture remains governed by Nevermine's Engineering Source of Truth, ADRs, Blueprint and official project documentation.
