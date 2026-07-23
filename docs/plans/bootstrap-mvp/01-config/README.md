# Package 01 — Config

Ratatosk CLI configuration merge: flags → env → repo `ratatosk.yaml` → `~/.ratatosk/config.yaml`.

**Wave:** W1 (after W0 foundation)
**Gate:** `pytest ratatosk/tests/test_config_loader.py -x`

| File | Tier | Scenario |
|------|------|----------|
| [ACT-1-CFG-06.md](ACT-1-CFG-06.md) | 1 | LLM_PROVIDER ollama |
| [ACT-1-CFG-07.md](ACT-1-CFG-07.md) | 1 | OLLAMA_BASE_URL |
| [ACT-1-CFG-08.md](ACT-1-CFG-08.md) | 1 | Default qwen3:14b |
| [ACT-1-CFG-09.md](ACT-1-CFG-09.md) | 1 | YGGDRASIL_SERVER_URL |
| [ACT-1-CFG-02.md](ACT-1-CFG-02.md) | 4 | model_summary_token_budget flag override |

Tier 4 scout/update config scenarios live in [11-scout-update](../11-scout-update/) (CFG-01,03,04,05).
