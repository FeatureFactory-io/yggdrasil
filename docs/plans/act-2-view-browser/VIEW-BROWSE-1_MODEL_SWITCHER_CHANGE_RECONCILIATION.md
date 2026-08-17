# Change Reconciliation — VIEW-BROWSE-1 Model Switcher

**Feature:** `VIEW-BROWSE-1` (Act 2 View Browser / content browser)
**Activity:** BPE-08 Process Change Request
**Status:** Approved — 2026-08-17 (user: go with assumptions Q1–Q4)
**Date:** 2026-08-17

---

## Trigger

The View Browser is a content browser over a **Model** (instance graph). An organisation holds many Models. Priya must switch which Model she is browsing from the left navigator, and every shareable/AI-constructable view URL must include the Model slug.

Current specs treated Model as CLI/MCP context (`--model`, `list_models`, `model?`) while the GUI hard-coded an implicit default (`yggdrasil`) and used unscoped `/views/{package}/…` paths. This CR closes that gap.

This activity does **not** implement code.

---

## Reconciliation matrix

Affected Screen IDs: `VIEW-BROWSE-1` (primary), `VIEW-HISTORY-1`, `EXPORT-BRIEFING-1`, `AUTH-LOGIN-1` (landing), `CHAT-MUNIN-1` (semantic URLs).

| Layer | Source | Pre-CR state | Drift? | Notes |
|-------|--------|--------------|--------|-------|
| PRD | `PRD.MD` Key Features 1–2 | View browser + semantic URLs; `--model` only on Ratatosk CLI | **Y** | Revised in place |
| User journey | Act 2 `VIEW-BROWSE-1` | Static layout; URLs `/views/{package}/…`; history already `/models/{model}/history` | **Y** | Revised in place |
| Scenarios | `docs/features/act-2-view/*.feature` | All GET `/views/`; navigator asserts static `browser-model-name` | **Y** | Scenarios 48–54 added |
| Mockups | `mockups/view/browse.html` | Static `browser-model-name` heading | **Y** | Dropdown switcher in mockup |
| Screen flow | `docs/ux/2_dialogue-maps/screen-flow.md` | Hub is `VIEW-BROWSE-1`; Model is domain entity | **Y** | Model-scoped browse note |
| IA guidelines | `docs/ux/IA_guidelines.md` | Route `/views/`; subtitle `model: {name}` display-only | **Y** | Switcher organism §6.2 |
| Conventions | `docs/conventions.md` | `/views/{package_slug}/{stereotype}` | **Y** | Model segment added |
| Prior plan | `docs/plans/act-2-view-browser/` | W7–W11 three-panel explorer; no model wave | **Y** | W12 after Plan Feature |
| Architecture | `docs/architecture/SAO.md` | `graph` owns Model; web app undescribed for routing | **Y** (minor) | Model-scoped GUI browse |
| As-built | `browse_helpers.py`, `browse_service.py` | `DEFAULT_MODEL_SLUG = "yggdrasil"`; query parser never reads a model param | **Y** | Out of scope for BPE-08 |
| CATALOG | `docs/features/CATALOG.md` | `browser-model-name` = heading | **Y** | Switcher testids added |

---

## Approved target state

### Decisions (Q1–Q4)

| # | Decision |
|---|---------|
| **Q1** | Canonical browse path is `/models/{slug}/views/…` (aligned with `/models/{slug}/history`). |
| **Q2** | Elements / Relationships / ChangeSets / Runs inherit the current Model from session. No `/models/{slug}/elements/` prefix in this CR. |
| **Q3** | Default Model: sole visible → that one; else last-used cookie `yggdrasil_model`; else first by `name`. |
| **Q4** | Switcher does not create or ensure Models. Create remains `ratatosk bootstrap` / MCP `ensure_model`. |

### Product

1. The View Browser is **always scoped to one Model**.
2. **Model switcher** in the left navigator header (the current static name becomes a dropdown). Lists Models the signed-in user may read (owner-group / RBAC). Does **not** create Models — create remains `ratatosk bootstrap` / MCP `ensure_model`.
3. Changing Model navigates to that Model’s views and **resets** package/stereotype/filter/time-travel (different graph).
4. Canonical semantic URLs:

```
/models/{model-slug}/views/
/models/{model-slug}/views/{package-slug}/
/models/{model-slug}/views/{package-slug}/{stereotype-slug}?filter={json}
/models/{model-slug}/views/graph.json
/models/{model-slug}/views/{package}/{stereotype}/export?format=…
/models/{model-slug}/history?a=…&b=…          (already specified)
```

5. Unscoped alias: `GET /views/` → **302** to `/models/{default}/views/`.
6. **Default Model:** exactly one visible → that one; else last-used session cookie `yggdrasil_model`; else first Model by `name` among visible Models.
7. Zero Models: `/views/` returns **200** empty state (“No models yet — run `ratatosk bootstrap`”); switcher disabled.
8. Unknown slug: **404**.
9. Other GUI screens (Elements, Relationships, ChangeSets, Runs) **inherit the current Model from session**. They do not gain `/models/{slug}/elements/` prefixes in this CR.

### Spec files revised in this CR

| File | Change |
|------|--------|
| `PRD.MD` | Key Features 1–2: many Models; switcher; model-scoped semantic URLs |
| `docs/features/user_journey.md` | Act 0 landing; Act 2 switcher + URL table; Act 8 examples; export URL |
| `docs/conventions.md` | Semantic URL examples |
| `docs/ux/IA_guidelines.md` | Route, switcher, subtitle, nav |
| `docs/ux/2_dialogue-maps/screen-flow.md` | Model-scoped browse note |
| `docs/features/act-2-view/view-browse-navigator.feature` | Scenarios 48–54 |
| `docs/features/act-2-view/_implementation_notes.md` | CR delta / W12 placeholder |
| `docs/features/CATALOG.md` | Switcher testids |
| `src/yggdrasil/web/templates/mockups/view/browse.html` | Dropdown switcher (spec mockup only) |
| `docs/architecture/SAO.md` | One sentence on model-scoped GUI browse |

Existing AT scenarios 01–47 keep `GET /views/` (alias). Implementation planning will decide whether ATs follow the 302 or hit the canonical path.

---

## Fast-path justification

Not applicable — drift across all present spec layers; new scenarios required.

---

## Out of scope (BPE-08 closed)

- Production code, URLConf, tests, migrations
- Metamodel picker (still Part II / Key Feature 12)
- Model CRUD GUI (`MODEL-LIST+FIND`)
- Path-prefixed `/models/{slug}/elements/` (and siblings) — deferred; session inherit (Q2)
- Plan Feature (BPE-01) — invoke separately when ready to implement W12
