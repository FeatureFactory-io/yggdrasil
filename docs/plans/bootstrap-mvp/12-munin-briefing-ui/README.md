# Package 12 — Munin Briefing UI

Post-run briefing screen (MUNIN-BRIEFING-1) — HTMX UI after Ratatosk bootstrap/update.

> **DEFER (Tier 4 package)** — Implement after W0–W9 green. Feature quarantined @wip (hits `/mockups/`).

**Wave:** W10+
**Feature file:** `docs/features/act-1-ratatosk/munin-briefing.feature`
**Screen ID:** MUNIN-BRIEFING-1
**Mockup:** `/mockups/munin/briefing/` (migrate to real route)

| File | Scenario |
|------|----------|
| MUNIN-BRIEFING-1-01..10 | Page render, narrative, confidence, CTAs, C4 primer, navbar |

**Depends on:** Real Ratatosk run + ChangeSet data (not mockup-only GET). Bootstrap MVP W6+ produces munin_reasoning for briefing copy.

Gate: `pytest tests/integration/test_munin_briefing_views.py -x` + Playwright when route live.
