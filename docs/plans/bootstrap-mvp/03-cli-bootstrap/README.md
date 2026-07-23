# Package 03 — CLI Bootstrap

Subprocess `ratatosk bootstrap` against `sample_webapp` — production packaging, stdout contract, token/server wiring.

**Wave:** W5 (after W4 discovery in-process paths green)
**Gate:** `pytest ratatosk/tests/test_cli_click.py -x`

| File | Tier | Scenario |
|------|------|----------|
| [ACT-1-CLI-08.md](ACT-1-CLI-08.md) | 1 | Empty-model wipe no-op then scan |
| [ACT-1-CLI-01.md](ACT-1-CLI-01.md) | 1 | Full bootstrap stdout + ChangeSet link |
| [ACT-1-CLI-09.md](ACT-1-CLI-09.md) | 1 | `YGGDRASIL_SERVER_URL` / `--server` |
| [ACT-1-CLI-07.md](ACT-1-CLI-07.md) | 1 | C4 metamodel stereotypes/packages on graph |
| [ACT-1-CLI-06.md](ACT-1-CLI-06.md) | 3 | Missing token — clear error |
| [ACT-1-CLI-02.md](ACT-1-CLI-02.md) | 4 DEFER | Re-bootstrap wipe + instructions |
| [ACT-1-CLI-03.md](ACT-1-CLI-03.md) | 4 DEFER | Post-wipe add-heavy buckets |
| [ACT-1-CLI-05.md](ACT-1-CLI-05.md) | 4 DEFER | Auto-apply vs pending threshold |

**Not in this package:** ACT-1-CLI-04 (Munin linking) lives in [06-munin-linking](../06-munin-linking/).

**AT vs subprocess:** Tier 1 CLI scenarios use subprocess + live or test MCP server; discovery logic is proven in [04-discovery](../04-discovery/) in-process first.
