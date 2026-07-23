# Package 10 — Re-bootstrap

Second-pass bootstrap on **populated** graph — bulk wipe, instructions, add-heavy buckets. Deferred until W0–W9 green.

> **DEFER (Tier 4 package)** — All scenarios below implement after bootstrap MVP certification.

**Wave:** W10+
**Gate:** Combined checkpoints for CLI-02, CLI-03, DISC-03

| File | Canonical implementation detail |
|------|--------------------------------|
| [ACT-1-CLI-02.md](ACT-1-CLI-02.md) | Wipe 31/44 + instructions stdout |
| [ACT-1-CLI-03.md](ACT-1-CLI-03.md) | Post-wipe bucket semantics |
| [ACT-1-DISC-03.md](ACT-1-DISC-03.md) | In-process discovery wipe path |

Also indexed in [03-cli-bootstrap](../03-cli-bootstrap/) and [04-discovery](../04-discovery/) — this package is the **wave entry point** for re-bootstrap work.

**Policy (locked):** Re-bootstrap = bulk wipe Elements + Relationships, then full filesystem rescan. Not incremental update. No `unchanged:` bucket (RATATOSK-SPEC-REALIGNMENT-PLAN A3).
