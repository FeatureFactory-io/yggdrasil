# Package 02 — Ollama / LLM

Real LLM path for bootstrap when `LLM_PROVIDER=ollama`.

**Wave:** W3
**Gate:** `pytest src/yggdrasil/llm/tests/test_ollama_client.py -x` (+ optional `@ollama` behave)

| File | Tier |
|------|------|
| [ACT-1-LLM-01.md](ACT-1-LLM-01.md) | 1 — implement `OllamaClient.complete()` |
| [ACT-1-LLM-03.md](ACT-1-LLM-03.md) | 1 — 4/4 manifest via real model |
| [ACT-1-LLM-02.md](ACT-1-LLM-02.md) | 3 — model not pulled error |
| [ACT-1-LLM-04.md](ACT-1-LLM-04.md) | 3 — fenced JSON + stereotype filter |

Also indexed in [09-error-hygiene](../09-error-hygiene/README.md).
