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
| W15 | **Views v2** — Filters-first `field_map`, viewport, in-node labels | 69–79 | Same plan · [#95](https://github.com/FeatureFactory-io/yggdrasil/issues/95) blocked on W14 |

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
