# Act 2 View Browser — Implementation Notes (v0.3 three-panel explorer)

**Mockup:** [`src/yggdrasil/web/templates/mockups/view/browse.html`](../../../src/yggdrasil/web/templates/mockups/view/browse.html)
**Pattern source:** Mimir Content Browser [`act-16-content-browser/`](../../../mimir/docs/features/act-16-content-browser/) (adapted for C4 graph, not playbook methodology tree)

---

## Component map

| Panel | Responsibility | Primary testids | Feature file |
|-------|----------------|-----------------|--------------|
| Left navigator | Package tree, element list, search | `browser-nav-panel`, `browser-package-tree`, `browser-search-input`, `package-toggle-{slug}`, `nav-element-{slug}` | `view-browse-navigator.feature` |
| Centre canvas | Cytoscape graph + table toggle, filters | `graph-cy-container`, `toggle-table`, `toggle-graph`, `results-container` | `view-browse-canvas.feature` |
| Right inspector | Element/relationship properties (embed mode) | `browser-inspector-panel`, `inspector-empty`, `inspector-content` | `view-browse-inspector.feature` |
| Page shell | Header actions, Munin offcanvas | `view-browse-page`, `export-btn`, `open-munin-btn` | `view-browse.feature` |

---

## Scenario index (VIEW-BROWSE-1-01 … 44)

| IDs | Status | Runner | Notes |
|-----|--------|--------|-------|
| 01–15 | v0.2 implemented | AT (pytest + behave) | Single-column; update 02/08/14/15 to use fixture Given when TFK-07 lands |
| 16 | v0.3 shell | AT | Three-panel DOM + layout class |
| 17–24 | v0.3 navigator | AT + E2E | 17–20 AT testid shell; 21–24 Playwright interaction |
| 25–34 | v0.3 inspector | AT + E2E | 27–28 embed partials; 29–34 selection sync |
| 35–37, 45–46 | v0.3 canvas | AT | Graph JSON, mode SSR, canvas controls |

---

## Production implementation waves

| Wave | Deliverable | Scenarios unlocked |
|------|-------------|-------------------|
| W7 | Three-panel template shell + CSS (`yrg-view-browser`) | 16 |
| W8 | Left navigator (package tree HTMX or SSR) | 17–24 |
| W9 | Inspector + embed partials on Element/Relationship views | 25–34 |
| W10 | Full-height Cytoscape canvas + selection bus JS | 38–42 |
| W11 | Filter ↔ navigator ↔ graph sync | 43–44 |

Deferred from v0.2 (unchanged): 07 saved views, 09 export/history wiring, 11 time travel banner.

---

## Canvas controls — Mimir parity boundary

Adopt from Mimir Content Browser (`browser_graph.html`):

| Control | Yggdrasil | testid |
|---------|-----------|--------|
| Node count badge | yes | `graph-node-count` |
| Re-plot | yes | `graph-replot-btn` |
| Zoom in / out / fit | yes | `graph-zoom-in`, `graph-zoom-out`, `graph-zoom-fit` |

**Explicitly out of scope** (playbook methodology graph only — do not port):

- Custom layout toggle
- Layout picker (Layered ▾)
- Edge routing picker (Bezier ▾)
- Compound / workflow grouping
- Node size mode toggle

Yggdrasil uses a fixed `cose` layout and bezier edges from filtered `/views/graph.json`.

---

## Embed mode contract (inspector)

Inspector loads entity detail without chrome — same rule as Mimir FOB-CONTENT-BROWSER-08b:

```
GET /elements/{id}/?embed=1
GET /relationships/{id}/?embed=1
```

Response MUST include entity fields; MUST NOT include navbar, breadcrumbs, or full-page wrapper.

---

## Selection sync (client JS)

Tree click, table row click, graph node tap, and inspector endpoint link MUST produce identical outcome:

1. Highlight navigator row (one active)
2. Select Cytoscape node/edge
3. Load inspector content (element or relationship)

Chevron-only click on package row toggles accordion WITHOUT changing selection (Mimir FOB-26 pattern).

---

## testid convention change (v0.3)

Prefer **slug** over numeric PK for navigator rows so AT specs stay stable:

```
data-testid="nav-element-{slug}"     # e.g. nav-element-munin
data-testid="element-row-{slug}"     # table mode
```

Numeric `nav-element-{id}` in mockup is acceptable for design reference; production should use slug.
