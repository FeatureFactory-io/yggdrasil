# Change Reconciliation — VIEW-BROWSE-1 Views v2 (Mockup → Spec)

> **Implement only [§ Approved target state](#approved-target-state-mockup-aligned) below.** Rejected pre-mockup design is archived in [§ Archive](#archive--rejected-pre-mockup-design-2026-08-18) — do not implement from Archive.

**Feature:** `VIEW-BROWSE-1` (Act 2 View Browser)
**Activity:** BPE-08 Process Change Request (post-mockup back-propagation)
**Status:** Approved — mockup validated 2026-08-18 (`ca42ea7`)
**Parent CR:** [`VIEW-BROWSE-1_VIEWS_V2_CONTENT_VIEWPORT_CR.md`](VIEW-BROWSE-1_VIEWS_V2_CONTENT_VIEWPORT_CR.md)
**Mockup:** [`src/yggdrasil/web/templates/mockups/view/browse.html`](../../../src/yggdrasil/web/templates/mockups/view/browse.html)

---

## Trigger

The Views v2 CR (2026-08-18) proposed a **Content preset dropdown** and separate **Content editor** panel. During mockup prototyping, Priya's workflow was corrected: **Filters panel is the sole View editor** — scope (package / stereotypes) and visible fields (Content) live in one place with a single **Apply Filters** primary.

This document back-propagates the **as-built mockup** into journey, features, IA, conventions, and architecture so W15 implements what was validated in HTML/JS — not the superseded Content-dropdown design.

---

## Reconciliation matrix (post-mockup)

| Layer | Source | Pre-mockup CR | Mockup as-built | Drift? | Action |
|-------|--------|---------------|-----------------|--------|--------|
| User journey | `user_journey.md` | Partial Filters-first note | Full toolbar + field_map narrative | **Y** | Revised in place |
| Scenarios | `view-browse-content.feature` | Content dropdown + editor | Filters field sections | **Y** | Scenarios rewritten 69–79 |
| Scenarios | `view-browse-views.feature` | Header Views dropdown | Canvas toolbar Views | **Y** | Comments + AT notes |
| Scenarios | `view-browse-canvas.feature` | `results-container` count | No count; `graph-cy-container` | **Y** | Scenario 36 updated |
| Mockups | `mockups/view/browse.html` | — | Filters-first + in-node labels | — | Reference implementation |
| Screen flow | `screen-flow.md` | Header Views | Canvas toolbar Views | **Y** | Footnote updated |
| IA guidelines | `IA_guidelines.md` | §6.4.1–6.4.2 Content picker | §6.4 Filters-first Content | **Y** | Sections replaced |
| Conventions | `conventions.md` | `?content=` preset URL | `field_{stereotype}=` params | **Y** | URL row updated |
| Prior plan | `INDEX.md` | W15 content presets | W15 field_map from Filters | **Y** | W15 row updated |
| Architecture | `SAO.md` | `content.bindings` presets | `content.field_map` | **Y** | Payload note updated |
| CATALOG | `CATALOG.md` | content-editor-* testids | view-field-* testids | **Y** | Testid table updated |
| As-built (prod) | `view-browser.js` | Unchanged | N/A until W15 | **Y** | Out of scope here |

---

## Approved target state (mockup-aligned)

### Toolbar layout

| Zone | Controls | testids |
|------|----------|---------|
| **Page header** | Export, History, Munin | `export-btn`, `history-btn`, `open-munin-btn` |
| **Canvas toolbar (left)** | Filters toggle; active View name badge when `browse_view` loaded | `filters-toggle`, `active-view-name` |
| **Canvas toolbar (right)** | Depth slider; **Views** dropdown; Table / Graph toggle | `browser-depth-control`, `views-dropdown`, `toggle-table`, `toggle-graph` |

No element-count informer in the canvas toolbar.

### Filters panel = View editor

| Control | Behavior |
|---------|----------|
| **Package** | Multi-select; changing selection **narrows** element and relationship stereotype option lists (package-scoped catalog) |
| **Element stereotypes** | Multi-select; options scoped by selected packages |
| **Relationship stereotypes** | Multi-select; options scoped by selected packages |
| **Field sections** | One block per selected stereotype (`view-fields-{slug}`); checkboxes per `property_schema` path (`view-field-{slug}-{path}`) |
| Stereotype change | Field sections update **immediately** (client preview); graph labels refresh live in mockup |
| **Clear** | Resets to loaded named View baseline or empty filters | `filter-panel-clear-btn` |
| **Save View** | Opens save modal (shared with Views dropdown) | `save-view-btn` |
| **Apply Filters** | **Sole primary** — full-page GET with filters + field params | `apply-filters-btn` |

Applying filters **clears** `browse_view` slug (custom session overrides named View until re-loaded).

### Content model (`field_map`)

```json
"content": {
  "field_map": {
    "component": ["name", "owner", "health"],
    "depends_on": ["stereotype", "properties.protocol"]
  }
}
```

- Keys = stereotype slugs (element or relationship) active in filters.
- Values = ordered list of field paths from `Stereotype.property_schema`.
- **Graph nodes:** Cytoscape `label` = multiline **`Key: value`** inside round-rectangle nodes (`width`/`height`: `label`, centered text).
- **Graph edges:** label from relationship stereotype field_map (e.g. `depends_on · protocol: HTTP`).
- **Table:** columns = union of element field_map paths (Name + Stereotype always first).
- **Inspector:** **Visible fields** section mirrors active field_map; full properties remain under Other properties / Provenance.

Built-in Content **presets** (`minimal`, `current-state`, …) may seed field_map in W15 helpers — there is **no preset picker** in the mockup UI.

### Live URL encoding

| Param | Example | Purpose |
|-------|---------|---------|
| `package` | repeated | Package scope |
| `stereotype` | repeated | Element stereotype scope |
| `edge_stereotype` | repeated | Relationship stereotype scope |
| `field_{stereotype}` | repeated paths | Visible fields per stereotype |
| `depth`, `mode` | unchanged | Levels + presentation |
| `browse_view` | slug | Named View expansion (field_map from payload unless `field_*` overrides) |

**Not in live URL:** viewport.

### Graph layout

- **Sparse subgraph** (few internal edges): `grid` layout with overlap avoidance.
- **Connected subgraph:** `cose` with `nodeDimensionsIncludeLabels`.
- **Always** `fit` after layout completes (`resize` + `fit`, 48px padding).
- Manual **⊡** fit and **↺** re-plot remain available (`graph-zoom-fit`, `graph-replot-btn`).

### Viewport (unchanged from v2 CR)

Opt-in **Include graph viewport** on Save View modal (`save-view-include-viewport`); restored after layout + fit when loading named View in graph mode.

---

## Archive — rejected pre-mockup design (2026-08-18)

Historical record only. BPE-08 replaced a separate Content toolbar (preset dropdown + editor panel + `?content=` URL) with Filters-first `field_map`. W14/W15 implement **Approved target state** above.

---

## Spec files revised

| File | Change |
|------|--------|
| `VIEW-BROWSE-1_VIEWS_V2_CONTENT_VIEWPORT_CR.md` | Pointer + status; Q1 revised |
| `docs/features/user_journey.md` | Toolbar layout; field_map; URL table |
| `docs/features/act-2-view/view-browse-content.feature` | Scenarios 69–79 rewritten |
| `docs/features/act-2-view/view-browse-views.feature` | Toolbar placement notes |
| `docs/features/act-2-view/view-browse-canvas.feature` | Remove results-container AT |
| `docs/features/act-2-view/_implementation_notes.md` | Component map |
| `docs/features/CATALOG.md` | Testids + step catalog |
| `docs/ux/IA_guidelines.md` | §6.3–6.4, §8.2 labels |
| `docs/conventions.md` | `field_*` URL params |
| `docs/architecture/SAO.md` | field_map payload |
| `docs/ux/2_dialogue-maps/screen-flow.md` | Views footnote |
| `docs/plans/act-2-view-browser/INDEX.md` | W15 description |
| `PRD.MD` | Key Feature 2 — Filters-first Content + canvas-toolbar Views |

---

## Out of scope

- Production W15 implementation (separate BPE wave)
- Re-opening v1 Filters / Levels decisions
