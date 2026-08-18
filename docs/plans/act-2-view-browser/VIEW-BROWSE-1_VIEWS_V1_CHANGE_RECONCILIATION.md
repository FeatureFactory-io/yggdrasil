# Change Reconciliation — VIEW-BROWSE-1 Views v1

**Feature:** `VIEW-BROWSE-1` (Act 2 View Browser)
**Activity:** BPE-08 Process Change Request
**Status:** Approved — 2026-08-18 (decisions Q1–Q4 confirmed in plan gate)
**Date:** 2026-08-18

---

## Trigger

Priya needs to **save and reload browse sessions** on the View Browser — not just copy a URL, but name a snapshot (Filters + Levels/depth) and pick it from a dropdown. Live URLs must remain shareable/bookmarkable; named Views must persist per user and Model.

Prior specs deferred “saved views” (scenario 07 stub only). Journey described `[Save View]` and a header dropdown but defined neither the **View** entity nor save/load/delete flows. As-built: dropdown empty, Save View button disabled ([`browse.html`](../../../src/yggdrasil/web/templates/web/view/browse.html)).

**Views v1 scope:** Filters + Levels (`depth`) + presentation mode. **Content** (node/edge annotations) and **viewport** (zoom/pan) deferred to CR #2.

This activity does **not** implement code.

---

## Reconciliation matrix

Affected Screen IDs: `VIEW-BROWSE-1` (primary), `CHAT-MUNIN-1` (semantic URLs may reference `browse_view=`).

| Layer | Source | Pre-CR state | Drift? | Notes |
|-------|--------|--------------|--------|-------|
| PRD | `PRD.MD` Key Features 1–2 | Shareable filtered views; depth slider; no named Views | **Y** | One sentence on named Views |
| User journey | `docs/features/user_journey.md` Act 2 | “saved-views dropdown”; `[Save View]`; no View definition | **Y** | Views entity; dual URL/DB persistence |
| Scenarios | `view-browse.feature` | 07: dropdown visible only (`saved-views-dropdown`) | **Y** | Revise 07; add 61–68 in `view-browse-views.feature` |
| Scenarios | `view-browse-navigator/canvas/inspector.feature` | `?view=graph` for graph-mode AT | **Y** | Rename to `?mode=graph` in spec |
| Mockups | `mockups/view/browse.html` | “Saved views” stub dropdown | **Y** | Views dropdown + save dialog mockup |
| Screen flow | `screen-flow.md` | Hub browse; no View entity | **N** | Footnote: Views are in-browser state |
| IA guidelines | `IA_guidelines.md` §6.3, §11.2 | `saved-views-dropdown`, Save View in filter panel | **Y** | §6.4 Views organism; `views-dropdown` testid |
| Conventions | `conventions.md` | `depth`, filter JSON; no `browse_view` or `mode=` | **Y** | Semantic URL rows added |
| Prior plan | `INDEX.md` | “07 saved views” deferred | **Y** | W14 wave |
| Architecture | `SAO.md` | No `BrowseView` entity | **Y** | `graph.BrowseView` ORM (user preference) |
| As-built | `browse_helpers.py`, `browse.html`, `view-browser.js` | Filters + depth parsed; `?view=` for mode; save disabled | **Y** | W14 implementation |
| CATALOG | `CATALOG.md` | `saved-views-dropdown` | **Y** | Views testids + steps |

---

## Approved decisions (2026-08-18)

| # | Question | Decision |
|---|----------|----------|
| **Q1** | Presentation query param | **Rename `?view=` → `?mode=graph\|table`** in spec; W14 updates ATs, features, and JS together (breaking) |
| **Q2** | BrowseView persistence | **`graph.BrowseView` via Django ORM** — user preference; not ChangeSet-governed |
| **Q3** | Delete/rename RBAC | **Owner only**; viewers may load named Views but not save/delete/rename |
| **Q4** | Save entry points | **Both** — header Views dropdown and filter-panel Save View share one dialog |

---

## Approved target state

### View v1 definition

A **View** is a named, Model-scoped browse snapshot:

| Part | v1 payload field | Notes |
|------|------------------|-------|
| **Filters** | `filters.package`, `stereotype`, `health`, `as_of`, `rules` | `rules` reserved `null` until advanced filter builder ships |
| **Levels** | `levels.depth` | Same semantics as `?depth=N` (BFS hops) |
| **Presentation** | `presentation` | `graph` \| `table` — encoded as `?mode=` in live URL |

Ephemeral UI excluded: inspector selection, panel collapse, Munin panel open state.

**Canonical payload example:**

```json
{
  "filters": {
    "package": "application",
    "stereotype": "component",
    "health": null,
    "as_of": null,
    "rules": null
  },
  "levels": { "depth": 3 },
  "presentation": "graph"
}
```

### Dual persistence

1. **Live URL** — `package`, `stereotype`, `health`, `as_of`, `depth`, `mode=graph|table`
2. **Named View** — `graph.BrowseView` record; load via dropdown or `?browse_view={slug}` (server expands to query string)

### Domain model (W14 — spec only here)

`graph.BrowseView`: `model` FK, `owner` FK (User), `name`, `slug` (unique per model+owner), `payload` JSONField, timestamps. ORM writes; not ChangeSet pipeline.

### Semantic URLs

| Concept | Encoding |
|---------|----------|
| Live filters + depth | existing query params |
| Presentation | `mode=graph` \| `mode=table` |
| Named View | `?browse_view={slug}` on `/models/{model}/views/` |
| Munin link | `/models/{model}/views/?browse_view=payment-review` |

### UI (spec)

| Control | testid |
|---------|--------|
| Views dropdown | `views-dropdown` |
| Save current (filter panel) | `save-view-btn` |
| Named View menu item | `view-option-{slug}` |
| Save dialog confirm | `save-view-confirm-btn` |
| Delete View | `delete-view-btn` |

### Scenarios (61–68)

New file: `docs/features/act-2-view/view-browse-views.feature`. Interactive save/load/delete marked `@wip` until W14 step defs land; shell scenarios (61, 67 partial) AT-ready.

### CR #2 (Views v2 — reconciled 2026-08-18)

[`VIEW-BROWSE-1_VIEWS_V2_CONTENT_VIEWPORT_CR.md`](VIEW-BROWSE-1_VIEWS_V2_CONTENT_VIEWPORT_CR.md) — Content bindings + viewport snapshot. **W15** after W14. Status: pending approval.

---

## Spec files revised in this CR

| File | Change |
|------|--------|
| `PRD.MD` | Named Views sentence under Key Feature 2 |
| `docs/features/user_journey.md` | Views definition; save/load narrative; URL table |
| `docs/conventions.md` | `mode=`, `browse_view=` rows |
| `docs/ux/IA_guidelines.md` | §6.4 Views organism; testid renames; `mode=` in mode-scoped note |
| `docs/ux/2_dialogue-maps/screen-flow.md` | Footnote on Views |
| `docs/features/act-2-view/view-browse.feature` | Scenario 07 → Views dropdown; `mode=` in 16 |
| `docs/features/act-2-view/view-browse-views.feature` | **New** — scenarios 61–68 |
| `docs/features/act-2-view/view-browse-*.feature` | `?view=` → `?mode=` in graph-mode URLs |
| `docs/features/act-2-view/_implementation_notes.md` | Views component row; W14; scenario index 61–68 |
| `docs/features/CATALOG.md` | Views testids; `mode=` in step catalog |
| `docs/features/support/visibility.py` | Comment: `mode=graph` |
| `docs/features/steps/view_browser_steps.py` | Graph-mode step uses `?mode=graph` |
| `docs/architecture/SAO.md` | BrowseView entity; mode-scoped note |
| `docs/plans/act-2-view-browser/INDEX.md` | W14 row; link this CR |
| `src/yggdrasil/web/templates/mockups/view/browse.html` | Views dropdown + save modal mockup |

---

## Fast-path justification

Not applicable — drift across journey, scenarios, IA, conventions, architecture, and as-built.

---

## Out of scope (BPE-08 closed)

- Production code, migrations, `BrowseView` model implementation
- Content/viewport (CR #2)
- Advanced JSON filter builder (`filters.rules`)
- Plan Feature W14 — invoke BPE-01 separately when ready
