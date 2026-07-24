# Act 2 View Browser — Plan Index

**Branch:** `feature/act-2-view-browser`
**Feature:** `VIEW-BROWSE-1` — [`docs/features/act-2-view/view-browse.feature`](../../features/act-2-view/view-browse.feature)
**Posture:** Dr. Dobbs v2 — test-first, mockup graduation, `lessons_learned.md` after each wave.

## Initial setup (BPE-01)

1. `git checkout main && git pull`
2. `git checkout -b feature/act-2-view-browser`
3. Implement waves F0→W6; append to [`lessons_learned.md`](lessons_learned.md) after each checkpoint.

## Wave order

| Wave | Deliverable | Checkpoint |
|------|-------------|------------|
| F0 | `graph/browse_service.py` + MCP delegate | `pytest src/yggdrasil/graph/tests/test_browse_service.py -x` |
| W1–W5 | `/views/` shell, table, filters, graph JSON | `pytest src/yggdrasil/web/tests/test_view_browse.py -x` |
| W6 | Navbar, Gherkin `/views/` URLs | `pytest src/yggdrasil/web/tests/ -x` |

## Deferred (stub in prod)

VIEW-BROWSE-1-07, 09, 10, 11 — saved views, export/history, Munin wiring, time travel replay.

## v0.2 status

Implemented in tag `0.2`: F0 + W1–W6 core (list, filters, graph JSON, navbar).
