# Act 2 View Browser — Plan Index

**Branch:** `feature/act-2-view-browser-v03` (proposed)
**Feature:** `VIEW-BROWSE-1` — [`docs/features/act-2-view/`](../../features/act-2-view/)
**Posture:** Dr. Dobbs v2 — mockup → feature specs → TFK-07 → BPE waves

## Feature file map (v0.3)

| File | Scenarios | Component |
|------|-----------|-----------|
| [`view-browse.feature`](../../features/act-2-view/view-browse.feature) | 01–16 | Shell, filters, navbar, three-panel chrome |
| [`view-browse-navigator.feature`](../../features/act-2-view/view-browse-navigator.feature) | 17–24 | Left package/element tree |
| [`view-browse-inspector.feature`](../../features/act-2-view/view-browse-inspector.feature) | 25–34 | Right property panel + embed partials |
| [`view-browse-canvas.feature`](../../features/act-2-view/view-browse-canvas.feature) | 35–44 | Graph/table canvas + filter sync |
| [`view-browse-views.feature`](../../features/act-2-view/view-browse-views.feature) | 61–68 | Named Views save/load (W14) |
| [`view-browse-content.feature`](../../features/act-2-view/view-browse-content.feature) | 69–79 | Filters-first field_map + viewport (W15) |
| [`_implementation_notes.md`](../../features/act-2-view/_implementation_notes.md) | — | Component map, waves, embed contract |

## v0.2 status (shipped)

F0 + W1–W6: `browse_service`, `/views/` table, filters, graph JSON, navbar.
Scenarios **01–15** (except 11 @wip) covered by `test_view_browse.py`.

## v0.3 wave order

| Wave | Deliverable | Scenarios | Checkpoint |
|------|-------------|-----------|------------|
| W7 | Three-panel template + `yrg-view-browser` CSS | 16 | AT shell testids |
| W8 | Navigator SSR/HTMX + slug testids | 17–24 | AT 17–20; E2E 21–24 |
| W9 | Inspector + `?embed=1` on Element/Relationship views | 25–34 | AT 27–28; E2E 29–34 |
| W10 | Cytoscape full-height + selection bus JS | 38–42 | E2E |
| W11 | Filter ↔ navigator ↔ graph URL sync | 43–44 | AT + E2E |
| W12 | Model switcher | 48–54 | AT + E2E |
| W13 | Depth traversal BFS + slider + element tree | 55–60 | AT + E2E · [#93](https://github.com/FeatureFactory-io/yggdrasil/issues/93) |
| W14 | **Views v1** — `BrowseView`, save/load, `browse_view=`, `mode=` migration | 61–68 | [`BPE-W14-W15-views-implementation.md`](BPE-W14-W15-views-implementation.md) · [#94](https://github.com/FeatureFactory-io/yggdrasil/issues/94) |
| W15 | **Views v2** — Filters-first `field_map`, viewport, in-node labels | 69–79 | Same plan · [#95](https://github.com/FeatureFactory-io/yggdrasil/issues/95) |
| W16 | **Polish** — subtitle, toolbar sizing, header alignment, sticky Apply (#96–#99) | — | Shipped 2026-08-18 |
| W17 | **Inspector custom properties** — `property_schema` rows (#100) | 27b | Shipped 2026-08-18 · [`BPE-W17-inspector-custom-properties.md`](BPE-W17-inspector-custom-properties.md) · [#100](https://github.com/FeatureFactory-io/yggdrasil/issues/100) |
| W18 | **Filter custom properties** — dynamic field_map from metamodel (#101) | 81 | Shipped 2026-08-18 · [`BPE-W18-filter-custom-properties.md`](BPE-W18-filter-custom-properties.md) · [#101](https://github.com/FeatureFactory-io/yggdrasil/issues/101) |
| W19 | **Navigator package defaults** — top-level packages at depth=1 (#102) | 25 | Shipped 2026-08-18 · [`BPE-W19-navigator-default-tree.md`](BPE-W19-navigator-default-tree.md) · [#102](https://github.com/FeatureFactory-io/yggdrasil/issues/102) |
| W20 | **Diagram schema + mockups** — presentation JSON, DiagramDraft spec | — | [`act-10-diagram-editor/INDEX.md`](../act-10-diagram-editor/INDEX.md) · BPE-08 CR |
| W21 | **Add Diagram + create modal + editor Create mode** | diagram-editor 01 | W20 |
| W22 | **Draft store + Draft pill + Edit load** | diagram-list 04; diagram-editor 02–03 | W21 |
| W23 | **Canvas editing** — drag, palette, relationship draw | diagram-editor 04–06 | W22 |
| W24 | **Munin save_diagram + ChangeSet ops** | diagram-editor 07–08 | W23 |
| W25 | **Diagram list production + hover actions** | diagram-list 03–05; delete/move | W24 |
| W26 | **MCP + REST diagram tools** | diagram-mcp.feature | W24 |
| W27 | **Diagram-scoped Munin chat** | Act 8 diagram context | W26 |

**TFK-07 before W8:** gaps #7–17 in [`docs/features/CATALOG.md`](../../features/CATALOG.md#known-gaps--tfk-07).

## Mockup reference

[`src/yggdrasil/web/templates/mockups/view/browse.html`](../../../src/yggdrasil/web/templates/mockups/view/browse.html) — three-panel layout with Yggdrasil self-model data.

## Deferred (unchanged)

09 export/history prod wiring · 11 time travel banner.

## Change request (BPE-08 closed, approved 2026-08-18)

**Views v1** — named browse snapshots (Filters + Levels/depth); dual URL + DB persistence; `mode=` replaces `view=`. Specs: [`VIEW-BROWSE-1_VIEWS_V1_CHANGE_RECONCILIATION.md`](VIEW-BROWSE-1_VIEWS_V1_CHANGE_RECONCILIATION.md). **W14** unblocked for Plan Feature.

## Change request (BPE-08 approved 2026-08-18)

**Views v2** — Filters-first `content.field_map` + graph viewport in View payload; live URL uses `field_{stereotype}=` params (mockup-validated). Specs: [`VIEW-BROWSE-1_VIEWS_V2_CONTENT_VIEWPORT_CR.md`](VIEW-BROWSE-1_VIEWS_V2_CONTENT_VIEWPORT_CR.md), [`VIEW-BROWSE-1_VIEWS_V2_MOCKUP_RECONCILIATION.md`](VIEW-BROWSE-1_VIEWS_V2_MOCKUP_RECONCILIATION.md). **W15** after W14.

## Change request (BPE-08 closed, approved 2026-08-17)

Model switcher in the left navigator; canonical URLs `/models/{slug}/views/…`. Specs: [`VIEW-BROWSE-1_MODEL_SWITCHER_CHANGE_RECONCILIATION.md`](VIEW-BROWSE-1_MODEL_SWITCHER_CHANGE_RECONCILIATION.md). **W12 shipped.**

## Change request (BPE-08 closed, approved 2026-08-17)

Depth traversal: filter roots + `?depth=N` BFS subgraph; canvas depth slider; navigator traversal tree. Specs: [`VIEW-BROWSE-1_DEPTH_TRAVERSAL_CHANGE_RECONCILIATION.md`](VIEW-BROWSE-1_DEPTH_TRAVERSAL_CHANGE_RECONCILIATION.md). Plan: [`BPE-W13-depth-traversal.md`](BPE-W13-depth-traversal.md). **W13 shipped** — [#93](https://github.com/FeatureFactory-io/yggdrasil/issues/93).

## Change request (BPE-08 closed, shipped 2026-08-18)

Inspector custom properties (W17), filter custom properties (W18), navigator package defaults (W19). Specs: [`VIEW-BROWSE-1_INSPECTOR_PROPERTIES_CR.md`](VIEW-BROWSE-1_INSPECTOR_PROPERTIES_CR.md), [`VIEW-BROWSE-1_FILTER_CUSTOM_PROPERTIES_CR.md`](VIEW-BROWSE-1_FILTER_CUSTOM_PROPERTIES_CR.md), [`VIEW-BROWSE-1_NAVIGATOR_DEFAULTS_CR.md`](VIEW-BROWSE-1_NAVIGATOR_DEFAULTS_CR.md). **W17–W19 shipped** — [#100](https://github.com/FeatureFactory-io/yggdrasil/issues/100) [#101](https://github.com/FeatureFactory-io/yggdrasil/issues/101) [#102](https://github.com/FeatureFactory-io/yggdrasil/issues/102).

## Change request (BPE-08 approved 2026-08-19)

**Diagram editor** — draft-first Cytoscape editor, View Browser **Add Diagram**, Munin on Save, MCP two-phase API. Spec: [`DIAGRAM_EDITOR_CHANGE_RECONCILIATION.md`](../DIAGRAM_EDITOR_CHANGE_RECONCILIATION.md). Waves **W20–W27** in [`act-10-diagram-editor/INDEX.md`](../act-10-diagram-editor/INDEX.md).
