# Change Reconciliation — VIEW-BROWSE-1 Views v2 (Content + Viewport)

**Feature:** `VIEW-BROWSE-1` (Act 2 View Browser)
**Activity:** BPE-08 Process Change Request
**Status:** Approved — 2026-08-18 (Q1–Q4 accepted; mockup validated — see [`VIEW-BROWSE-1_VIEWS_V2_MOCKUP_RECONCILIATION.md`](VIEW-BROWSE-1_VIEWS_V2_MOCKUP_RECONCILIATION.md))
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
| Mockups | `mockups/view/browse.html` | Filters-first field_map; in-node Key: value labels | **N** | Validated — [`VIEW-BROWSE-1_VIEWS_V2_MOCKUP_RECONCILIATION.md`](VIEW-BROWSE-1_VIEWS_V2_MOCKUP_RECONCILIATION.md) |
| Screen flow | `screen-flow.md` | Views footnote (v1) | **N** | Content is in-browser on VIEW-BROWSE-1 |
| IA guidelines | `IA_guidelines.md` §8.2 | Cytoscape defaults `data(name)` / `data(stereotype)`; no Content organism | **Y** | §6.5 Content picker; dynamic label contract |
| Conventions | `conventions.md` | No `content=` param | **Y** | Semantic URL row |
| Prior plan | `INDEX.md` | W14 Views v1; v2 stub only | **Y** | W15 wave |
| Architecture | `SAO.md` | BrowseView payload v1; Content deferred | **Y** | Payload v2 schema; graph.json enrichment |
| As-built | `browse_service.py`, `view-browser.js` | Fixed labels/columns; no viewport persistence | **Y** | W15 implementation |
| CATALOG | `CATALOG.md` | content-editor-* testids | view-field-* testids | **Y** | Revised |

---

## Proposed decisions (approval gate)

| # | Question | Proposed decision |
|---|----------|-------------------|
| **Q1** | Content preset storage | **Filters-first `field_map`** (mockup-validated). Built-in presets may seed defaults in W15 service layer only — **no Content dropdown or editor panel**. Priya selects stereotypes in the Filters panel; field checklists derive from `property_schema`; **`Apply Filters`** commits scope + fields. Persist `content.field_map` in `BrowseView.payload`. |
| **Q2** | Live URL for Content | **`field_{stereotype}={path}`** repeated params encode `content.field_map` (mockup-validated). Applying filters with explicit field params **clears** `browse_view` until a named View is re-loaded. Built-in presets may seed defaults in W15 helpers only — **not** shareable via `?content=` in the UI. |
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

### Content model (mockup-validated — Filters-first)

**Content** is configured **inside the Filters panel** alongside scope filters — not a separate toolbar control.

```json
"content": {
  "field_map": {
    "component": ["name", "owner", "health"],
    "depends_on": ["stereotype", "properties.protocol"]
  }
}
```

- Keys = element or relationship stereotype slugs active in filters.
- Values = ordered field paths from `Stereotype.property_schema`.
- **Package** multi-select narrows stereotype option lists (package-scoped catalog).
- **Stereotype** multi-select renders one field section per slug (`view-fields-{slug}`).
- **Apply Filters** is the **sole primary** — commits scope + field_map to live URL.
- **Graph nodes:** Cytoscape `label` = multiline **`Key: value`** inside round-rectangle nodes.
- **Graph edges:** label from relationship stereotype field_map.
- **Table:** columns = union of element field_map paths (Name + Stereotype always first).
- **Inspector:** **Visible fields** section mirrors active field_map; full properties remain under Other properties / Provenance.

Built-in Content presets may seed `field_map` in W15 service helpers — there is **no preset picker** in the validated mockup UI.

**Superseded (do not implement without new CR):** Content preset dropdown, Content editor panel, separate Apply content button, `?content=` live URL.

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
  "filters": { "package": ["application"], "stereotype": ["component"], "edge_stereotype": ["depends_on"], "health": null, "as_of": null, "rules": null },
  "levels": { "depth": 3 },
  "presentation": "graph",
  "content": {
    "field_map": {
      "component": ["name", "owner", "health"],
      "depends_on": ["stereotype", "properties.protocol"]
    }
  },
  "viewport": { "zoom": 1.2, "pan": { "x": 0, "y": 0 }, "center_element_id": "290" }
}
```

v1 records without `content` / `viewport` → defaults: name-only labels, no viewport restore.

### Dual persistence (extended)

| Mechanism | Encodes |
|-----------|---------|
| Live URL | filters, `depth`, `mode`, repeated **`field_{stereotype}={path}`** |
| Named View | full payload including `content.field_map` + optional viewport |
| `browse_view=` | expands all of the above; explicit `field_*` overrides payload fields |

Viewport is **not** in live URL.

### UI (spec — mockup-validated)

| Zone | Control | testid |
|------|---------|--------|
| Page header | Export, History, Munin | `export-btn`, `history-btn`, `open-munin-btn` |
| Canvas toolbar (left) | Filters toggle; active View name when loaded | `filters-toggle`, `active-view-name` |
| Canvas toolbar (right) | Depth slider; **Views** dropdown; Table/Graph toggle | `browser-depth-control`, `views-dropdown`, `toggle-table`, `toggle-graph` |
| Filters panel | Package multi-select | `filter-package` |
| Filters panel | Element stereotype multi-select | `filter-stereotype` |
| Filters panel | Relationship stereotype multi-select | `filter-edge-stereotype` |
| Filters panel | Per-stereotype field sections | `view-field-sections`, `view-fields-{slug}`, `view-field-{slug}-{path}` |
| Filters panel | Clear · Save View · **Apply Filters** (primary) | `filter-panel-clear-btn`, `save-view-btn`, `apply-filters-btn` |
| Save View modal | Include graph viewport checkbox | `save-view-include-viewport` |

**Superseded:** `content-dropdown`, `content-editor-*`, `results-container`, `graph-node-count`, Views dropdown in page header.

### API / graph.json

`GET /models/{slug}/views/graph.json` accepts resolved `field_map` (from URL params or named View expansion); response node `data.label` includes server-formatted multiline **`Key: value`** text for Cytoscape.

### Scenarios (69–76)

New file: `docs/features/act-2-view/view-browse-content.feature`

| ID | Scenario | Runner |
|----|----------|--------|
| 69 | Filters panel shows field sections when stereotypes selected; no Content dropdown | AT |
| 70 | Default field_map labels nodes with name only | AT + E2E |
| 71 | Toggling owner field shows `Owner: …` inside node label | AT + E2E @wip |
| 72 | `field_component=owner` in URL applies without named View | AT |
| 73 | Save View persists field_map in BrowseView payload | AT @wip |
| 74 | Load named View restores in-node labels and table columns | AT + E2E @wip |
| 75 | Viewport restored on load when saved with include flag (graph) | E2E @wip |
| 76 | Viewport not applied when presentation is table | AT @wip |
| 77 | Package change narrows stereotype options (cascade) | AT |
| 78 | Priya toggles field checkboxes and applies filters | AT + E2E @wip |
| 79 | Save View persists custom field_map | AT @wip |

Scenarios 61–68 in `view-browse-views.feature` gain notes that 73–74 extend to content/viewport after W15.

### Implementation wave

| Wave | Deliverable | Scenarios |
|------|-------------|-----------|
| W14 | Views v1 (prerequisite) | 61–68 |
| W15 | Filters-first field_map + viewport + payload v2 | 69–79 |

---

## Spec files to revise in this CR

| File | Change |
|------|--------|
| `PRD.MD` | Filters-first Content + canvas-toolbar Views under Key Feature 2 |
| `docs/features/user_journey.md` | Complete View definition; Filters-first Content + viewport; URL table |
| `docs/conventions.md` | `field_{stereotype}=` semantic URL |
| `docs/ux/IA_guidelines.md` | §6.3.1 Filters-first Content; §8.2 in-node labels |
| `docs/features/act-2-view/view-browse-content.feature` | Scenarios 69–79 (Filters-first) |
| `docs/features/act-2-view/view-browse-views.feature` | Canvas-toolbar Views; content/viewport in save/load |
| `docs/features/act-2-view/_implementation_notes.md` | Filters panel row; W15; scenario index 69–79 |
| `docs/features/CATALOG.md` | view-field-* testids + steps |
| `docs/architecture/SAO.md` | BrowseView payload field_map; graph.json |
| `docs/plans/act-2-view-browser/INDEX.md` | W15 row; mockup reconciliation link |
| `docs/plans/act-2-view-browser/VIEW-BROWSE-1_VIEWS_V2_MOCKUP_RECONCILIATION.md` | **New** — mockup → spec back-propagation |
| `mockups/views.py` + `mockups/view/browse.html` | Filters-first prototype (validated `ca42ea7`) |

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

None — Q1–Q4 approved; mockup validated per [`VIEW-BROWSE-1_VIEWS_V2_MOCKUP_RECONCILIATION.md`](VIEW-BROWSE-1_VIEWS_V2_MOCKUP_RECONCILIATION.md). BPE-01 Plan W15 may proceed.
