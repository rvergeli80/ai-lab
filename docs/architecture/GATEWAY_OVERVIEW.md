# Nevermine LLM Gateway — Architecture Overview

> Status: Active development  
> Repository: `rvergeli80/ai-lab`  
> Component: `services/gateway_manager`  
> Role: Vendor-neutral LLM access layer for Nevermine Platform

---

## 1. Purpose

The Nevermine LLM Gateway is the abstraction layer responsible for providing unified access to multiple Large Language Model providers.

Its purpose is to prevent Nevermine agents, services and applications from depending directly on a specific LLM vendor.

Consumers should request a capability or, when necessary, an explicit model. The Gateway is responsible for deciding how and where that request is executed.

The long-term architecture supports three execution modes:

1. Nevermine Managed AI.
2. Bring Your Own Key (BYOK).
3. Local / Private inference.

The current implementation is developed and validated inside the AI LAB repository.

---

## 2. Core principle

Consumers should not need to know:

- which provider hosts a model;
- whether a model is local or remote;
- whether a provider is temporarily unavailable;
- whether a paid model is allowed by budget policy;
- whether fallback is required.

Conceptually:

```python
response = gateway.complete(
    Request(
        capability="coding",
        prompt="Implement this endpoint."
    )
)
```

The Gateway owns model resolution, routing and execution.

---

## 3. Current architecture

```text
Application / Agent / Service
            |
            v
        LLM Gateway
            |
     +------+------+
     |             |
     v             v
 Routing       Explicit Model
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
 +---+----------------+
 |                    |
 v                    v
Remote Providers     Local
 |                    |
LiteLLM Adapter      Ollama Adapter
 |                    |
OpenRouter/...       Ollama
                      |
                  Local models
```

The current Gateway separates:

- model definition;
- provider definition;
- provider availability;
- model selection;
- routing;
- budget permissions;
- provider execution;
- fallback;
- normalized responses.

---

## 4. Model Catalog

Location:

```text
config/models/
```

The catalog describes the models known by the Gateway.

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

A model can define information such as:

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

Downloaded model weights are runtime assets and must not be stored in Git.

---

## 5. Model Registry

The `ModelRegistry` provides programmatic access to the consolidated model catalog.

Its responsibilities include model discovery and filtering using the information contained in the catalog.

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

The catalog and registry provide the model inventory used by routing and selection components.

---

## 6. Provider Registry

The Provider Registry represents the LLM providers understood by the Gateway.

Provider definitions currently include:

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

Provider credentials must never be stored in the repository.

Credentials are supplied through environment variables.

Examples:

```text
OPENAI_API_KEY
ANTHROPIC_API_KEY
OPENROUTER_API_KEY
```

Secrets remain outside Git.

---

## 7. Provider Availability

`ProviderAvailability` determines which providers are usable at runtime.

For remote API providers, availability currently depends on the corresponding credentials being present in the environment.

For Ollama, availability is checked against the local Ollama service.

Example:

```text
http://localhost:11434/api/version
```

A runtime environment could therefore report:

```python
{"openrouter", "ollama"}
```

Unavailable providers are excluded from normal routing.

---

## 8. Routing Policies

Routing configuration lives at:

```text
config/routing/policies.yaml
```

Routing is capability-driven.

Current policy capabilities include:

- coding;
- reasoning;
- chat;
- vision.

For example:

```yaml
coding:
  strategy: fallback
  candidates:
    - tier: premium
    - tier: paid
    - tier: free
    - tier: local
```

The desired abstraction is:

```text
Agent -> capability -> Gateway
```

instead of:

```text
Agent -> hardcoded vendor/model
```

For example, an application should be able to request:

```text
coding
```

without having to decide whether that capability will ultimately be provided by OpenRouter, OpenAI, Ollama or another provider.

---

## 9. Model Tiers

The current routing model uses four logical tiers:

### premium
Higher-value paid models intended for workloads where the routing policy prioritizes maximum model capability.

### paid
Standard paid remote models.

### free
Remote models explicitly classified/tagged as free.

### local
Models executed through local infrastructure.

Ollama models are treated as local models.

A model being open-weight does not automatically mean that its inference is free when hosted by an external provider.

---

## 10. Budget Policy

Budget configuration lives at:

```text
config/budget/budgets.yaml
```

`BudgetPolicy` currently controls whether a model tier is permitted to participate in routing.

For example:

```yaml
tiers:
  premium:
    enabled: false

  paid:
    enabled: false

  free:
    enabled: true

  local:
    enabled: true
```

With this configuration, premium and paid models are removed from the candidate chain before execution.

Budget configuration also currently contains monetary values such as:

```yaml
daily_eur: 2.00
monthly_eur: 30.00
```

IMPORTANT: these monetary limits are configuration only at the current implementation stage. They are NOT yet enforced against accumulated real usage.

---

## 11. FallbackRouter

`FallbackRouter` builds an ordered candidate chain.

Its decision process currently combines:

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

The router determines candidates. It does not itself execute inference.

---

## 12. Gateway Runtime

The main runtime abstraction is:

```python
Gateway.complete(Request)
```

Example:

```python
response = gateway.complete(
    Request(
        capability="coding",
        prompt="Create a Python API."
    )
)
```

At a high level, the runtime:

1. uses an explicit model when one is requested;
2. otherwise obtains candidates from `FallbackRouter`;
3. attempts candidates sequentially;
4. detects failures eligible for fallback;
5. tries the next candidate when appropriate;
6. returns a provider-independent `Response`.

---

## 13. Automatic Fallback

Automatic fallback has been validated with a real execution test.

The tested flow was:

```text
OpenRouter
    |
invalid test credential
    |
    v
remote execution failure
    |
    v
Gateway
    |
    v
next candidate
    |
    v
Ollama
    |
    v
Laguna XS 2.1
```

The final successful response was produced by:

```text
provider = ollama
model = laguna-xs-2.1
```

---

## 14. Retryable Failures

The current Gateway runtime recognizes several categories of failure that can trigger fallback, including:

- rate limiting;
- quota or credit problems;
- timeout;
- connection failure;
- provider unavailable;
- model unavailable;
- selected HTTP client errors;
- HTTP server errors.

The runtime implementation remains authoritative.

---

## 15. Adapters

Provider-specific execution is isolated behind adapters.

Current adapters:

```text
LiteLLMAdapter
OllamaAdapter
```

### LiteLLMAdapter

Used for remote providers, including the current OpenRouter path.

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

---

## 16. Local Models

Local models are executed through Ollama.

The currently integrated local catalog includes Laguna XS 2.1.

Other models may exist locally, but downloading a model does not automatically register it as a Gateway candidate.

For current Ollama fallback requests, the Gateway defaults to:

```text
think = false
```

when the request does not explicitly define `think`.

The Ollama adapter also uses:

```text
keep_alive = 30m
```

to reduce unnecessary model reloads.

---

## 17. Normalized Domain Objects

The Gateway exposes provider-independent domain objects:

```text
Model
Request
Response
TokenUsage
```

Example:

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
)
```

---

## 18. Security Rules

Secrets must NEVER be committed to Git.

Current ignored secret/runtime locations include:

```text
credentials/.env
config/env/.env.local
```

The repository also excludes runtime/local assets such as:

- downloaded LLM weights;
- Docker volumes;
- backups;
- virtual environments;
- caches;
- runtime logs.

---

## 19. Repository Structure

Development repository:

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
```

The Git repository is the versioned source of truth.

---

## 20. Validated Behaviors

Automated test suite:

- catalog loading;
- model registry;
- provider registry;
- selection engine.

Manual runtime validation:

- OpenRouter availability detection;
- Ollama availability detection;
- direct Ollama inference;
- remote-to-local fallback;
- budget tier filtering.

Budget routing was tested with paid and premium tiers disabled and selected Ollama for coding, reasoning and chat.

---

## 21. Planned: Usage Ledger

The Usage Ledger is the next planned Gateway capability.

It is NOT implemented yet.

Planned persisted information includes:

```text
timestamp
request
provider
model
input tokens
output tokens
total tokens
cost
project
tenant
latency
fallback information
```

Intended architecture:

```text
Gateway
   |
   +-- Routing
   |
   +-- BudgetPolicy
   |
   +-- Usage
        |
        +-- UsageRecord
        +-- UsageRepository
        +-- SQLiteUsageRepository
```

The repository abstraction should prevent the Gateway domain from depending directly on SQLite.

---

## 22. Planned: Real Budget and Cost Control

Once Usage Ledger exists, BudgetPolicy should evolve into actual usage-aware budget enforcement.

Planned capabilities include:

```text
daily budget
monthly budget
project budget
tenant budget
user budget
```

Future routing may consider:

```text
CAPABILITY
QUALITY
COST
PRIVACY
LATENCY
```

Potential user-facing profiles:

```text
Fast
Economy
Maximum Quality
Private
Balanced
```

These are architectural direction, not current functionality.

---

## 23. Target Nevermine Execution Modes

### Nevermine Managed AI

Nevermine manages provider access and can meter customer usage.

### BYOK — Bring Your Own Key

The customer supplies its own provider credentials. Provider consumption is associated with the customer's provider account.

### Local / Private

Nevermine can target customer/private inference infrastructure for privacy or offline use.

Possible future backends include:

```text
Ollama
vLLM
LM Studio
private cloud GPU
on-premise inference
```

The current LAB validates the Ollama pattern locally.

---

## 24. Target Nevermine Architecture and Golden Rule

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

### Golden Rule

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

Provider selection is infrastructure. Agent behavior is domain logic.

The LLM Gateway is intended to remain the vendor-neutral LLM access layer for Nevermine Platform.

---

## Implementation Status Summary

### Implemented

- model catalog;
- model registry;
- provider registry;
- provider availability;
- capability-based routing;
- tier-based routing;
- budget tier permissions;
- LiteLLM adapter;
- Ollama adapter;
- normalized Request/Response objects;
- automatic fallback;
- local Ollama execution;
- remote OpenRouter execution.

### Validated

- automated core tests: 5 passing;
- OpenRouter execution;
- Ollama execution;
- OpenRouter failure -> Ollama fallback;
- budget tier filtering -> local routing.

### Not Yet Implemented

- Usage Ledger;
- persistent usage accounting;
- real daily/monthly cost enforcement;
- tenant accounting;
- customer billing;
- full BYOK credential lifecycle;
- Nevermine Managed AI commercial metering;
- policy-based quality/cost/privacy/latency optimization.

---

## Source of Truth

This document describes the Gateway architecture at a high level.

When there is a discrepancy between this document and executable behavior, the implementation and automated tests determine the current technical behavior.

When Gateway behavior changes, this document must be updated in the same development cycle.
