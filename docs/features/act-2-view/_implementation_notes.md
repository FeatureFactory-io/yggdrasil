# Act 2 View Browser — Implementation Notes (v0.3 three-panel explorer)

**Mockup:** [`src/yggdrasil/web/templates/mockups/view/browse.html`](../../../src/yggdrasil/web/templates/mockups/view/browse.html)
**Pattern source:** Mimir Content Browser [`act-16-content-browser/`](../../../mimir/docs/features/act-16-content-browser/) (adapted for C4 graph, not playbook methodology tree)

---

## Component map

| Panel | Responsibility | Primary testids | Feature file |
|-------|----------------|-----------------|--------------|
| Left navigator | **Traversal tree**, search, **Model switcher** | `browser-nav-panel`, `browser-element-tree`, `browser-search-input`, `browser-model-switcher`, `nav-toggle-{slug}`, `nav-element-{slug}` | `view-browse-navigator.feature` |
| Centre canvas | Cytoscape graph + table toggle, filters, **depth slider** | `graph-cy-container`, `toggle-table`, `toggle-graph`, `browser-depth-slider`, `browser-depth-value`, `results-container` | `view-browse-canvas.feature` |
| Right inspector | Element/relationship properties (embed mode) | `browser-inspector-panel`, `inspector-empty`, `inspector-content` | `view-browse-inspector.feature` |
| Page shell | Header **Views** dropdown, save dialog, Munin offcanvas | `views-dropdown`, `save-view-btn`, `save-view-confirm-btn`, `view-option-{slug}` | `view-browse-views.feature` |
| Page shell | Munin offcanvas | `view-browse-page`, `export-btn`, `open-munin-btn` | `view-browse.feature` |

---

## Scenario index (VIEW-BROWSE-1-01 … 68)

| IDs | Status | Runner | Notes |
|-----|--------|--------|-------|
| 01–15 | v0.2 implemented | AT (pytest + behave) | Single-column; update 02/08/14/15 to use fixture Given when TFK-07 lands |
| 16 | v0.3 shell | AT | Three-panel DOM + layout class |
| 17–24 | v0.3 navigator | AT + E2E | Revise for traversal tree (BPE-08 depth CR) |
| 25–34 | v0.3 inspector | AT + E2E | 27–28 embed partials; 29–34 selection sync |
| 35–37, 45–46 | v0.3 canvas | AT | Graph JSON, mode SSR, canvas controls |
| 48–54 | **W12 implemented** | AT + E2E | Model switcher; canonical `/models/{slug}/views/` |
| 55–60 | **W13 shipped** | AT + E2E | Depth slider + BFS subgraph |
| 61–68 | **Views v1 spec** (BPE-08 CR) | AT + E2E (@wip 62–66, 68) | Named Views — Filters + Levels |

---

## Production implementation waves

| Wave | Deliverable | Scenarios unlocked |
|------|-------------|-------------------|
| W7 | Three-panel template shell + CSS (`yrg-view-browser`) | 16 |
| W8 | Left navigator SSR/HTMX | 17–24 |
| W9 | Inspector + embed partials on Element/Relationship views | 25–34 |
| W10 | Full-height Cytoscape canvas + selection bus JS | 38–42 |
| W11 | Filter ↔ navigator ↔ graph URL sync | 43–44 |
| W12 | **Model switcher** (shipped) | 48–54 |
| W13 | **Depth traversal** — `browse_service.subgraph_from_roots`, slider, traversal tree, multi-hop `traverse` | 55–60 |
| W14 | **Views v1** — `graph.BrowseView`, save/load dropdown, `browse_view=` URL, `mode=` migration | 61–68 |

Deferred from v0.2 (unchanged): 09 export/history prod wiring, 11 time travel banner.

W12 and W13 are **shipped**. Views v1 CR: [`VIEW-BROWSE-1_VIEWS_V1_CHANGE_RECONCILIATION.md`](../../../plans/act-2-view-browser/VIEW-BROWSE-1_VIEWS_V1_CHANGE_RECONCILIATION.md). W14 unblocked after BPE-01 Plan Feature.

---

## Depth-scoped subgraph (W13)

**Algorithm:** `browse_service.subgraph_from_roots(model, filters, depth)` — shared by web browse, `graph.json`, and MCP `traverse`.

1. **Roots** = elements matching browse filters. If no element-narrowing filter → graph **sources** (zero incoming edges).
2. **BFS** along **outgoing** edges for `depth − 1` hops (visited set for cycles).
3. **Edges** = relationships where both endpoints ∈ node set.
4. **Navigator** = tree from BFS parent map; chevron toggles local child visibility only.

---

## Canvas controls — Mimir parity boundary

Adopt from Mimir Content Browser (`browser_graph.html`):

| Control | Yggdrasil | testid |
|---------|-----------|--------|
| Node count badge | yes | `graph-node-count` |
| Re-plot | yes | `graph-replot-btn` |
| Zoom in / out / fit | yes | `graph-zoom-in`, `graph-zoom-out`, `graph-zoom-fit` |
| Depth slider | yes (Yggdrasil-specific) | `browser-depth-slider`, `browser-depth-value` |

**Explicitly out of scope** (playbook methodology graph only — do not port):

- Custom layout toggle
- Layout picker (Layered ▾)
- Edge routing picker (Bezier ▾)
- Compound / workflow grouping
- Node size mode toggle

Yggdrasil uses a fixed `cose` layout and bezier edges from depth-scoped `/views/graph.json`.

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

Chevron-only click on a navigator node toggles child rows WITHOUT changing selection or URL `depth` (Mimir FOB-26 pattern).

---

## testid convention change (v0.3)

Prefer **slug** over numeric PK for navigator rows so AT specs stay stable:

```
data-testid="nav-element-{slug}"     # e.g. nav-element-munin
data-testid="nav-toggle-{slug}"      # chevron for traversal tree node
data-testid="element-row-{slug}"     # table mode
```

Numeric `nav-element-{id}` in mockup is acceptable for design reference; production should use slug.
