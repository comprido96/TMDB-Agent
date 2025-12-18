# TMDB AI Movie Agent – Technical Assessment
## Overview
This project implements a small AI agent that interprets natural language user requests, queries the public **TMDB API,** and combines the retrieved data with a **Large Language Model (LLM)** to generate **structured, reliable answers.**

The focus of the implementation is not only functional correctness, but also **clear separation of concerns, robustness around LLM usage, and production-oriented design choices.**

## Architecture
The system follows an **agent-based, orchestrated pipeline:**
```
User Query -> Router Agent (LLM) -> Parameter Extraction Agent (LLM + deterministic logic) -> Entity Resolution (orchestrator, deterministic) -> TMDB API Client -> Response Normalization -> Answer Generator (LLM, structured output)
```

## Main Components
- **RouterAgent**
Uses an LLM to determine which TMDB endpoint best matches the user intent.
- **ParameterExtractor**
Extracts structured parameters (query, year, genres, people names) from the user request using endpoint-specific LLM prompts, with regex-based fallback.
- **Orchestrator (TMDBMovieAgent)**
Coordinates the full flow, handles multi-step logic (e.g. resolving actor names to IDs), and enforces deterministic success/failure boundaries via typed results.
- **TMDBClient**
Thin HTTP client responsible only for executing TMDB API calls with API-ready parameters.
- **ResponseParser**
Normalizes raw TMDB responses into compact, LLM-friendly schemas to reduce noise and token usage.
- **AnswerGenerator**
Combines normalized data with an LLM to generate a strictly structured response validated via Pydantic.

## Technical Choices
- **Python + Requests** for simplicity and clarity
- **OpenAI API** for LLM reasoning (router, extractor, answer generation)
- **Pydantic** for strict schema validation and failure isolation
- **TMDB API** as a realistic, multi-endpoint public data source
- **Explicit orchestration layer** to manage probabilistic components safely

Key design principle: 
> *LLMs are probabilistic; the orchestrator must remain deterministic.*

## Agentic Flow
1. The user submits a natural language query.
2. The Router Agent selects the most appropriate TMDB endpoint.
3. The Parameter Extractor derives structured parameters from the query.
4. Actor names (if present) are resolved to TMDB person IDs.
5. The TMDB API is queried with validated parameters.
6. Raw API responses are normalized into compact schemas.
7. The Answer Generator produces a structured, grounded response.
8. All steps are guarded with explicit success/failure contracts.

## Deployment Strategy (AWS) - AWS Lambda + API Gateway
- Stateless orchestration fits Lambda execution model
- Low operational overhead
- Auto-scaling by default
- Environment variables for API keys (OpenAI, TMDB)

### Flow
```
API Gateway → Lambda (TMDBMovieAgent) → OpenAI + TMDB APIs

```
**N.B.:** **SageMaker** is not needed because
- No model training or hosting required for this PoC
- LLM is consumed via API, not self-hosted

## Fine-tuning/Model Adaptation Strategy
Fine-tuning is **not performed by default** and would be introduced incrementally:
1. **Prompt engineering first**
  Adjust router and extractor prompts based on observed failures.
2. **Task-specific fine-tuning (if needed)**
  - Router: intent classification fine-tuning
  - Parameter extraction: structured NER-style fine-tuning
  - Use lightweight approaches (LoRA / adapters)
3. **When to fine-tune**
  - Only after collecting sufficient real traffic
  - Only if prompt tuning and validation are insufficient
4. **Alternative**
  - Swap proprietary LLM with an open-source model if required
  - Keep the same orchestration and validation layers

## Scaling to Hundreds of API Endpoints
To scale this approach:
- **Endpoint Registry**

Central metadata describing each API’s capabilities and parameters.
- **Capability-based routing**

Router selects APIs based on declared capabilities rather than hardcoded names.
- **Planner–Executor pattern**

Replace single-step routing with multi-step planning for complex queries.
- **OpenAPI-driven adapters**

Auto-generate parameter schemas and clients from OpenAPI specs.
- **Caching and rate limiting**
  - Cache metadata and frequent responses
  - Enforce per-endpoint quotas centrally

The current architecture already supports this evolution without major refactoring.

## Limits of This PoC
- No caching or retries implemented
- No authentication / user management
- LLM confidence score is heuristic
- Best-effort entity resolution (actor name → ID)
- CLI-based interface (no HTTP server)

These limits are intentional to keep the scope focused on **core AI system design.**

## Conclusion
This project demonstrates how to safely integrate LLM reasoning with external APIs using:
- Clear agent boundaries
- Deterministic orchestration
- Strict schema validation
- Production-oriented design choices

The same approach can be extended to larger, real-world AI systems with minimal architectural changes.
