# Change Reconciliation — VIEW-BROWSE-1 Depth Traversal

**Feature:** `VIEW-BROWSE-1` (Act 2 View Browser / content browser)
**Activity:** BPE-08 Process Change Request
**Status:** Approved — 2026-08-17 (Q1–Q3 confirmed in BPE-01)
**Date:** 2026-08-17

---

## Trigger

Priya must control **how much of the graph** is visible without leaving the View Browser — stay at capabilities only, or expand to apps and stacks that depend on them. The current as-built navigator groups elements **flat under C4 packages**; the canvas renders **all filter-matching elements** with no hop limit. The journey already lists `?depth=N` in semantic URLs but it is not wired to browse UI or multi-hop `traverse`.

**Approved direction (conversation 2026-08-17):**

- **Level 0 (roots)** = elements matching current browse filters (stereotype, package, health, advanced filter).
- **Depth N** = BFS expansion **N − 1 hops** along **outgoing** edges from the root set (N = 1 → roots only; N = 2 → roots + direct neighbors; …).
- **Canvas control:** slider “Show N levels deep” (max = longest reachable hop from roots, capped at 20).
- **Navigator:** traversal tree rooted at filter matches; **chevron expand/collapse per node** unchanged (local disclosure only — does not change URL depth).
- **No edge-stereotype layer profiles** in v1 — follow directed edges; cycles handled with visited set.

This activity does **not** implement code.

---

## Reconciliation matrix

Affected Screen IDs: `VIEW-BROWSE-1` (primary). Secondary: MCP `traverse` (Act 5), `EXPORT-BRIEFING-1` (export scoped subgraph).

| Layer | Source | Pre-CR state | Drift? | Notes |
|-------|--------|--------------|--------|-------|
| PRD | `PRD.MD` Key Feature 2 | Multi-level view described; no depth control | **Y** | Depth slider + hop semantics |
| User journey | Act 2 `VIEW-BROWSE-1` | Package tree; flat filtered subgraph; `?depth=N` in URL table only | **Y** | Traversal tree + depth slider |
| Scenarios | `view-browse-navigator.feature` | Package toggles (`package-toggle-*`) | **Y** | Traversal tree scenarios; package-tree ATs revised |
| Scenarios | `view-browse-canvas.feature` | Filter sync; no depth | **Y** | Scenarios 55–60 |
| Scenarios | `act-5-mcp/mcp-query.feature` | `traverse` depth=1 only (as-built) | **Y** | QUERY-04b multi-hop |
| Mockups | `mockups/view/browse.html` | Package accordion; no depth slider | **Y** | Slider + traversal tree mockup |
| Screen flow | `screen-flow.md` | Hub browse; no depth note | **N** | No navigation change |
| IA guidelines | `IA_guidelines.md` | Canvas controls: zoom/replot only | **Y** | §6.3 depth slider organism |
| Conventions | `conventions.md` | `?depth=N` listed without semantics | **Y** | Normative hop definition |
| Prior plan | `act-2-view-browser/INDEX.md` | W7–W12; flat `browse_service` | **Y** | W13 depth traversal wave |
| Architecture | `SAO.md` | `traverse` one-hop; browse flat filter | **Y** | Shared BFS in `browse_service` |
| As-built | `browse_service.py`, `browse_helpers.py` | Flat `_filtered_queryset`; package buckets | **Y** | Out of scope for BPE-08 |
| As-built | `mcp/tools/query.py` `traverse` | Accepts `depth` but walks one hop only | **Y** | Align with BFS helper |
| CATALOG | `CATALOG.md` | `browser-package-tree` testids | **Y** | `browser-element-tree`, depth testids |

---

## Proposed target state

### Decisions (proposed — approve or revise)

| # | Decision |
|---|----------|
| **Q1** | **Root set** = elements matching active browse filters. If no element-narrowing filter is applied (entire model would be roots), use **graph sources** (nodes with zero incoming edges) as roots so depth stays meaningful on unfiltered browse. |
| **Q2** | **Default** `depth=1` when query param omitted (roots only in graph + navigator). Table mode lists the same depth-scoped node set (flat). |
| **Q3** | **Direction** = `outgoing` for View Browser BFS. Incoming/both deferred (MCP `traverse` keeps its own `direction` param). |
| **Q4** | **Edges in scope** = relationships where both endpoints are in the depth-scoped node set. |
| **Q5** | **Navigator tree** replaces package accordion with **traversal tree** (parent = BFS predecessor closest to a root; shared node if multiple paths — show once under first-discovered parent). Chevron toggles hide/show children **without** changing `depth`. |
| **Q6** | **Slider max** = min(longest hop from any root, 20). Label: “Show {N} levels deep”. URL sync: `?depth=N` (preserves other filters). |
| **Q7** | **Shared algorithm** in `browse_service.subgraph_from_roots(...)` used by `/views/graph.json`, navigator SSR, table rows, and multi-hop MCP `traverse`. |

### Product

1. Filter panel unchanged; filters define **roots**.
2. Canvas toolbar (graph mode): depth slider + existing zoom/replot controls.
3. Changing depth reloads navigator, graph JSON, table rows, and inspector selection if selected node falls out of scope (clear selection + empty inspector).
4. Semantic URL (unchanged key, new semantics):

```
/models/{model-slug}/views/?stereotype=capability&depth=2
/models/{model-slug}/views/graph.json?stereotype=capability&depth=3
```

5. Munin / MCP clients construct the same `depth` param as the slider.

### Spec files revised in this CR

| File | Change |
|------|--------|
| `PRD.MD` | Key Feature 2: depth-controlled hop expansion |
| `docs/features/user_journey.md` | Act 2 layout, URL table, Priya scenario |
| `docs/conventions.md` | `depth` semantics |
| `docs/ux/IA_guidelines.md` | Depth slider organism §6.3 |
| `docs/features/act-2-view/view-browse-navigator.feature` | Traversal tree scenarios; revise 17–19 |
| `docs/features/act-2-view/view-browse-canvas.feature` | Scenarios 55–60 |
| `docs/features/act-2-view/_implementation_notes.md` | W13 wave, algorithm note |
| `docs/features/act-5-mcp/mcp-query.feature` | QUERY-04b multi-hop traverse |
| `docs/features/CATALOG.md` | Depth + element-tree testids |
| `docs/plans/act-2-view-browser/INDEX.md` | W13 + CR reference |
| `docs/architecture/SAO.md` | Browse BFS + traverse alignment |
| `src/yggdrasil/web/templates/mockups/view/browse.html` | Depth slider + traversal tree mockup |

Existing AT scenarios 01–15 remain valid when **no filters + depth=1 + graph sources fallback** returns a non-empty root set; Plan Feature (BPE-01) will validate fixture expectations per wave.

---

## Open questions for user

1. **Q1 graph-sources fallback** when no filters — approve, or always treat “no filter” as all elements are roots (depth slider only useful with filters)?
2. **Q2 default depth=1** — approve, or default to max reachable depth (legacy flat-all behavior)?
3. **Q3 outgoing-only** for browse — approve, or expose direction toggle in filter panel now?

---

## Fast-path justification

Not applicable — drift across journey, features, mockup, plan, architecture, and as-built.

---

## Out of scope (BPE-08)

- Production code, URLConf, tests, migrations
- Edge-stereotype filters per hop (future advanced filter)
- Selection-root BFS (click node → re-root) — future; v1 is filter roots only
- Plan Feature (BPE-01) — invoke separately when ready to implement W13
