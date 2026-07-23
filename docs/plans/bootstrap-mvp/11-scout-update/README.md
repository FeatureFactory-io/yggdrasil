# Package 11 — Scout + Update + Config

`ratatosk update` incremental path: bounded scout loop, CI stdin fixtures, config merge for scout bounds and tool allowlists.

> **DEFER (Tier 4 package)** — Implement after W0–W9 green.

**Wave:** W10+
**Features:** `ratatosk-scout.feature`, `ratatosk-update.feature`, `ratatosk-config.feature` (CFG-01,03,04,05)

| Group | Files |
|-------|-------|
| Scout | ACT-1-SCOUT-01..05 |
| CI/CD update | ACT-6-CICD-01..19 |
| Config | ACT-1-CFG-01,03,04,05 |

**Policy (locked):** Update **never wipes** graph (CICD-19). Stdin triggers scout; evidence from `--repo`, Yggdrasil MCP, optional connector MCPs (SAO A4).

**Bounds (defaults):** 10 scout rounds, 1000 file reads, 50 MCP calls — overridable via ratatosk.yaml (CFG-01).

Gate (package): `pytest ratatosk/tests/test_update_cli.py src/yggdrasil/ratatosk/tests/test_scout_loop.py -x`
