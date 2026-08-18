# Change Reconciliation — VIEW-BROWSE-1 Views v2 (Content + Viewport)

**Feature:** `VIEW-BROWSE-1` (Act 2 View Browser)
**Activity:** BPE-08 Process Change Request
**Status:** Approved — 2026-08-18 (Q1–Q4 accepted; proceed to W15 planning after W14)
**Date:** 2026-08-18
**Prerequisite:** Views v1 CR approved — [`VIEW-BROWSE-1_VIEWS_V1_CHANGE_RECONCILIATION.md`](VIEW-BROWSE-1_VIEWS_V1_CHANGE_RECONCILIATION.md); W14 implements v1 payload before W15.

---

## Trigger

Priya needs to control **what appears on the graph and table** — not only *which* elements (Filters + Levels from v1), but *which properties* label nodes/edges and which columns appear in table mode. She also wants to **save and restore the graph camera** (zoom, pan, centered element) when returning to a named View.

PRD Key Feature 2: *"some properties hidden/available"* (e.g. show owners on Applications dependent on a Tech Stack). Journey deferred Content + viewport to this CR. As-built: graph nodes use **name only** ([`browse_service.py`](../../../src/yggdrasil/graph/browse_service.py) `label: el.name`); edges use stereotype slug; table columns fixed (Name, Stereotype, Owner, Health, Package); Cytoscape viewport is ephemeral (lost on reload).

**Views v2 scope:** extend the **View** payload and live URL with **Content** bindings + optional **viewport** snapshot. Does not re-open Filters/Levels/persistence decisions from v1.

This activity does **not** implement code.

---

## Reconciliation matrix

Affected Screen IDs: `VIEW-BROWSE-1` (primary), `CHAT-MUNIN-1` (semantic URLs may reference `content=` or named Views with viewport).

| Layer | Source | Pre-CR state | Drift? | Notes |
|-------|--------|--------------|--------|-------|
| PRD | `PRD.MD` §2 | Properties hidden/shown on same view; no Content mechanism | **Y** | Tie to Content presets |
| User journey | `user_journey.md` Act 2 | View = Filters + Levels only; Content deferred one line | **Y** | Full View definition; Content UI narrative |
| Scenarios | `view-browse-canvas.feature` | Graph viewport = fit/zoom controls only; fixed table columns | **Y** | Add 69–76 in `view-browse-content.feature` |
| Scenarios | `view-browse-views.feature` | Save/load filters + depth only | **Y** | Extend save/load for content + viewport |
| Mockups | `mockups/view/browse.html` | Name-only node labels; no Content picker | **Y** | Content dropdown + viewport save checkbox |
| Screen flow | `screen-flow.md` | Views footnote (v1) | **N** | Content is in-browser on VIEW-BROWSE-1 |
| IA guidelines | `IA_guidelines.md` §8.2 | Cytoscape defaults `data(name)` / `data(stereotype)`; no Content organism | **Y** | §6.5 Content picker; dynamic label contract |
| Conventions | `conventions.md` | No `content=` param | **Y** | Semantic URL row |
| Prior plan | `INDEX.md` | W14 Views v1; v2 stub only | **Y** | W15 wave |
| Architecture | `SAO.md` | BrowseView payload v1; Content deferred | **Y** | Payload v2 schema; graph.json enrichment |
| As-built | `browse_service.py`, `view-browser.js` | Fixed labels/columns; no viewport persistence | **Y** | W15 implementation |
| CATALOG | `CATALOG.md` | No Content testids | **Y** | content-dropdown, save-view-include-viewport |

---

## Proposed decisions (approval gate)

| # | Question | Proposed decision |
|---|----------|-------------------|
| **Q1** | Content preset storage | **Built-in presets** (Minimal, Current State, Jira Info) are **starting templates** only. Priya **customizes field-by-field** in the **Content editor** panel; resulting **bindings** persist in `BrowseView.payload.content` (and in mockup `sessionStorage` until saved). Defer separate `BrowseContentPreset` ORM table. |
| **Q2** | Live URL for Content | **`?content={preset-slug}`** selects a built-in template (`minimal`, `current-state`, `jira-info`). After customization, URL becomes **`?content=custom`** (mockup + W15) while full bindings live in session / named View payload — custom bindings are too large for bookmark URLs. |
| **Q3** | Viewport in saved Views | **Opt-in** — Save View dialog checkbox **Include graph viewport** (default unchecked). Viewport ignored in table mode. Not encoded in live URL (too fragile for bookmarking). |
| **Q4** | W15 vs W14 order | **W15 blocked on W14** — `BrowseView` model and v1 save/load must ship first; v2 extends payload with nullable `content` and `viewport` keys (backward compatible). |

---

## Approved target state

### View definition (complete)

A **View** is a named, Model-scoped browse snapshot:

| Part | Payload field | v1 | v2 |
|------|---------------|----|----|
| Filters | `filters.*` | ✓ | ✓ |
| Levels | `levels.depth` | ✓ | ✓ |
| Presentation | `presentation` | ✓ | ✓ |
| **Content** | `content` | — | ✓ |
| **Viewport** | `viewport` | — | ✓ (graph, opt-in on save) |

Ephemeral UI still excluded: inspector selection, panel collapse, Munin open state.

### Content model

**Content** controls what properties are visible on the canvas — split by **presentation mode**:

| Mode | Content bindings | Editor section |
|------|------------------|----------------|
| **Graph View** (`mode=graph`) | `bindings.nodes`, `bindings.edges` | Node primary, node secondary, edge label |
| **Table View** (`mode=table`) | `bindings.table` | Table column checklist |

Built-in presets seed **both** halves when first selected, but the **Content editor shows only the section for the active mode**. Apply updates graph labels **or** table columns — never both at once. Saved Views persist the full `content.bindings` object (graph + table halves).

- **Content editor (primary UX):** Priya opens **Edit content** from the canvas toolbar. In **Graph View** she edits node/edge field bindings; in **Table View** she edits table columns only. Presets pre-fill the active half; **Apply content** updates the current mode live. **Save View** persists both halves.
- **Graph rendering:** Cytoscape `label` = formatted primary + secondary (graph bindings only).
- **Table mode:** column set from `content.bindings.table` only.
- **Inspector:** unchanged — always full `properties` (Content does not hide inspector data).

### Viewport model (graph-only)

```json
"viewport": {
  "zoom": 1.15,
  "pan": { "x": -120, "y": 40 },
  "center_element_id": "290"
}
```

- Captured from Cytoscape on save when **Include graph viewport** is checked.
- Restored after graph layout when loading named View or `browse_view=` with viewport in payload.
- **Fit** / **Re-plot** remain manual overrides after load.

### Canonical payload v2 example

```json
{
  "filters": { "package": "application", "stereotype": "component", "health": null, "as_of": null, "rules": null },
  "levels": { "depth": 3 },
  "presentation": "graph",
  "content": { "preset": "current-state", "bindings": { "nodes": { "*": { "primary": "name", "secondary": ["owner"] } }, "edges": { "*": { "label": "stereotype" } }, "table": ["name", "stereotype", "owner", "health", "package"] } },
  "viewport": { "zoom": 1.2, "pan": { "x": 0, "y": 0 }, "center_element_id": "290" }
}
```

v1 records without `content` / `viewport` → defaults: preset `minimal`, no viewport restore.

### Dual persistence (extended)

| Mechanism | Encodes |
|-----------|---------|
| Live URL | filters, `depth`, `mode`, **`content={preset-slug\|custom}`** |
| Named View | full payload including custom `content.bindings` + optional viewport |
| Session (mockup) | custom `content.bindings` until Save View or preset pick clears them |
| `browse_view=` | expands all of the above |

Viewport is **not** in live URL.

### UI (spec)

| Control | Location | testid |
|---------|----------|--------|
| Content preset dropdown | Canvas toolbar (graph + table) | `content-dropdown` |
| Preset menu item | Dropdown | `content-option-{slug}` |
| Open Content editor | Toolbar button + dropdown item | `content-editor-toggle`, `content-editor-open` |
| Graph content editor section | Visible when `mode=graph` | `content-editor-graph-section` |
| Table content editor section | Visible when `mode=table` | `content-editor-table-section` |
| Start from preset (graph) | Editor — template select | `content-editor-preset-select` |
| Start from preset (table) | Editor — template select | `content-editor-table-preset-select` |
| Node primary field | Editor — select | `content-editor-node-primary` |
| Node secondary field | Editor — checkbox per path | `content-editor-node-secondary-{path}` |
| Edge label field | Editor — select | `content-editor-edge-label` |
| Table column | Editor — checkbox per path | `content-editor-table-col-{path}` |
| Reset / Apply | Editor footer | `content-editor-reset-btn`, `content-editor-apply-btn` |
| Include viewport | Save View modal checkbox | `save-view-include-viewport` |

**Content editor panel** (collapse, parallel to Filters) — **mode-specific**:

**Graph View** (`content-editor-graph-section`):
- Start from preset, node primary, node secondary, edge label
- Apply updates Cytoscape labels only

**Table View** (`content-editor-table-section`):
- Start from preset, table column checklist
- Apply updates results table only

Shared: **Reset to preset** (left) · **Apply content** (primary, right)

Save View dialog (extended):

- Name input (unchanged)
- **Include graph viewport** checkbox — visible only when `mode=graph`; default unchecked

### API / graph.json

`GET /models/{slug}/views/graph.json` accepts `content=`; response node `data` includes bound label fields and property values needed for Cytoscape styles (server-side formatting preferred for consistency with table).

### Scenarios (69–76)

New file: `docs/features/act-2-view/view-browse-content.feature`

| ID | Scenario | Runner |
|----|----------|--------|
| 69 | Content dropdown visible in graph mode | AT |
| 70 | Default/minimal preset labels nodes with name only | AT + E2E |
| 71 | Selecting Current State preset shows owner on nodes / columns | AT + E2E @wip |
| 72 | `?content=current-state` applies preset without named View | AT |
| 73 | Save View persists content preset in BrowseView payload | AT @wip |
| 74 | Load named View restores content labels and table columns | AT + E2E @wip |
| 75 | Viewport restored on load when saved with include flag (graph) | E2E @wip |
| 76 | Viewport not applied when presentation is table | AT @wip |
| 77 | Content editor panel opens from toolbar | AT |
| 78 | Priya customizes node secondary fields and applies | AT + E2E @wip |
| 79 | Save View persists custom content bindings | AT @wip |

Scenarios 61–68 in `view-browse-views.feature` gain notes that 73–74 extend to content/viewport after W15.

### Implementation wave

| Wave | Deliverable | Scenarios |
|------|-------------|-----------|
| W14 | Views v1 (prerequisite) | 61–68 |
| W15 | Content bindings + viewport + payload v2 migration | 69–76 |

---

## Spec files to revise in this CR

| File | Change |
|------|--------|
| `PRD.MD` | Content presets sentence under Key Feature 2 |
| `docs/features/user_journey.md` | Complete View definition; Content + viewport narrative; URL table |
| `docs/conventions.md` | `content=` semantic URL |
| `docs/ux/IA_guidelines.md` | §6.5 Content dropdown; §8.2 dynamic labels note |
| `docs/features/act-2-view/view-browse-content.feature` | **New** — scenarios 69–76 |
| `docs/features/act-2-view/view-browse-views.feature` | Notes on content/viewport in save/load scenarios |
| `docs/features/act-2-view/_implementation_notes.md` | Content row; W15; scenario index 69–76 |
| `docs/features/CATALOG.md` | Content testids + steps |
| `docs/architecture/SAO.md` | BrowseView payload v2; graph.json content param |
| `docs/plans/act-2-view-browser/INDEX.md` | W15 row; CR approved link |
| `docs/plans/act-2-view-browser/VIEW-BROWSE-1_VIEWS_V1_CHANGE_RECONCILIATION.md` | CR #2 → closed reference |
| `mockups/views.py` + `mockups/view/browse.html` | Content picker + viewport checkbox prototype |

---

## Fast-path justification

Not applicable — drift across journey, scenarios, IA, architecture, and as-built.

---

## Out of scope (BPE-08)

- Production code, W15 implementation
- Stereotype-specific binding overrides beyond `*` (advanced tab — post-W15)
- Advanced filter builder (`filters.rules`)
- Viewport in live URL query string
- Separate `BrowseContentPreset` ORM (unless Q1 revised at W15 planning)

---

## Open questions for user

Confirm Q1–Q4 in the **Proposed decisions** table to set status → **Approved** and unblock BPE-01 Plan W15.
