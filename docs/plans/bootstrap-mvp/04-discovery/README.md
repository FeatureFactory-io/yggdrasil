# Package 04 — Discovery

In-process and subprocess discovery against `sample_webapp` — blackboard, manifest match, ChangeSet orphan invariant, MCP handoff spy.

**Wave:** W4 (after W2 handoff + W3 Ollama optional)
**Gate:** `pytest src/yggdrasil/ratatosk/tests/test_discovery_agent.py -x`

| File | Tier | Focus |
|------|------|-------|
| [ACT-1-DISC-02.md](ACT-1-DISC-02.md) | 1 | Tree blackboard before extract |
| [ACT-1-DISC-15.md](ACT-1-DISC-15.md) | 1 | ModelSummary token budget key |
| [ACT-1-DISC-16.md](ACT-1-DISC-16.md) | 1 | Metamodel guidance on blackboard |
| [ACT-1-DISC-01.md](ACT-1-DISC-01.md) | 1 | Manifest 4/4 elements + ChangeSet |
| [ACT-1-DISC-06.md](ACT-1-DISC-06.md) | 1 | No orphan Elements |
| [ACT-1-DISC-21.md](ACT-1-DISC-21.md) | 1 | Subprocess MCP tool spy |
| [ACT-1-DISC-04.md](ACT-1-DISC-04.md) | 3 | Unknown stereotype cleanup |
| [ACT-1-DISC-05.md](ACT-1-DISC-05.md) | 3 | LLM invoked — no hardcoded Payment API |
| [ACT-1-DISC-07.md](ACT-1-DISC-07.md) | 3 | Missing token |
| [ACT-1-DISC-08.md](ACT-1-DISC-08.md) | 3 | Read-only token |
| [ACT-1-DISC-11.md](ACT-1-DISC-11.md) | 3 | Missing repo path |
| [ACT-1-DISC-13.md](ACT-1-DISC-13.md) | 3 | MCP snapshot failure |
| [ACT-1-DISC-14.md](ACT-1-DISC-14.md) | 3 | Non-JSON LLM → empty plan |
| [ACT-1-DISC-03.md](ACT-1-DISC-03.md) | 4 DEFER | Re-bootstrap wipe messaging |
| [ACT-1-DISC-09.md](ACT-1-DISC-09.md) | 4 DEFER | Unknown metamodel slug |
| [ACT-1-DISC-10.md](ACT-1-DISC-10.md) | 4 DEFER | Metamodel mismatch |
| [ACT-1-DISC-12.md](ACT-1-DISC-12.md) | 4 DEFER | Empty repo after ignores |

Skipped: DISC-17..20 (not in feature files).

**AT vs subprocess:** DISC-01..16 use in-process `bootstrap_repository` + `LocalOrmHandoffPort`; DISC-21 uses subprocess + HTTP MCP per SHARED-CONTRACT.

Tier 3 scenarios indexed in [09-error-hygiene](../09-error-hygiene/README.md).
