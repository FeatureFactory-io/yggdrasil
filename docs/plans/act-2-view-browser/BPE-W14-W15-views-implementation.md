# W14 + W15 — View Browser Named Views (Filters-first)

**Feature:** `VIEW-BROWSE-1` · **Waves:** W14 (persistence) → W15 (Filters-first Content + viewport)
**Spec authority:** [`VIEW-BROWSE-1_VIEWS_V2_MOCKUP_RECONCILIATION.md`](VIEW-BROWSE-1_VIEWS_V2_MOCKUP_RECONCILIATION.md) (UX target)
**Prerequisite CRs:** [Views v1](VIEW-BROWSE-1_VIEWS_V1_CHANGE_RECONCILIATION.md) · [Views v2](VIEW-BROWSE-1_VIEWS_V2_CONTENT_VIEWPORT_CR.md)
**Mockup reference:** [`src/yggdrasil/web/templates/mockups/view/browse.html`](../../../src/yggdrasil/web/templates/mockups/view/browse.html) · [`mockups/views.py`](../../../mockups/views.py) · [`mockup-view-browser.js`](../../../src/yggdrasil/web/static/js/mockup-view-browser.js)
**Branch (proposed):** `feature/view-browse-w14-w15-views`
**Scenarios:** 61–68 (W14) · 69–79 (W15)
**GitHub issues:** W14 [#94](https://github.com/FeatureFactory-io/yggdrasil/issues/94) · W15 [#95](https://github.com/FeatureFactory-io/yggdrasil/issues/95) (blocked on W14)

---

## BPE-01 vs BPE-02 boundary

| Phase | Activity | Deliverables |
|-------|----------|--------------|
| **Plan closure** | BPE-01 Steps 6–10 | This plan file, GitHub issue(s), INDEX update, user approval |
| **Implementation** | BPE-02–07 / MIN | Slices below — code, tests, commits |

**Execution order:** W14 must green before W15 starts. W15 implements the mockup-validated Filters-first View editor per reconciliation § Approved target state.

---

## What we are building (one sentence)

A **View** is a named, Model-scoped snapshot of **filters + field_map + depth + mode (+ optional viewport)**; Priya edits everything in the **Filters panel** and applies once; the canvas renders **Key: value** labels from `content.field_map`.

```mermaid
flowchart LR
  subgraph filters [Filters panel]
    pkg[Package multi]
    est[Element stereotypes]
    rst[Relationship stereotypes]
    fld[Field checklists]
  end
  subgraph persist [Persistence]
    url[Live URL field_* params]
    bv[graph.BrowseView payload]
  end
  subgraph canvas [Canvas]
    graph[Cytoscape in-node labels]
    table[Table columns]
  end
  filters -->|Apply Filters| url
  filters -->|Save View| bv
  bv -->|browse_view=| url
  url --> graph
  url --> table
```

---

## Approved semantics (from CRs — no open questions)

| Rule | Source |
|------|--------|
| `BrowseView` ORM on `graph` app; not ChangeSet-governed | Views v1 Q2 |
| Owner-only save/delete; viewers load-only | Views v1 Q3 |
| `?view=` → `?mode=graph\|table` (breaking migration in one wave) | Views v1 Q1 |
| Filters panel = sole View editor; `field_{stereotype}=` URL params | Mockup reconciliation |
| Apply Filters clears `browse_view` until View re-loaded | Mockup reconciliation |
| Viewport opt-in on Save modal; not in live URL | Views v2 Q3 |

---

## B — Approved UX (implement this)

- **Filters panel** = View editor: package + element/relationship stereotype multi-selects + per-stereotype field checkboxes (`view-field-*`)
- **Apply Filters** — sole primary; commits filters + `field_{stereotype}=` params; clears `browse_view` until View re-loaded
- **Save View** — persists payload including `content.field_map` + optional viewport
- **Views dropdown** — canvas toolbar (`views-dropdown`); active View name badge (`active-view-name`)
- **Canvas** — in-node multiline `Key: value` labels; table columns from field_map; grid/cose + fit
- **Named View load** — `?browse_view={slug}` expands payload; explicit `field_*` overrides

**Guardrails (not UX — engineering constraints):**

- BrowseView writes via ORM only — not ChangeSet pipeline
- Use `web/urls.py` only — not root `urls.py` / `settings.py` without human gate
- Production AT targets `/models/…/views/` — not `/mockups/`
- Log-story tests ship in same slice as behavior
- W15 blocked until W14 checkpoint passes

Design history: reconciliation doc § Archive only.

---

## A — Context Map

| File | Lines | Why |
|------|-------|-----|
| [`browse_service.py`](../../../src/yggdrasil/graph/browse_service.py) | 32–48, 303–340, 450–650 | `BrowseFilters`, BFS subgraph, graph JSON `label: el.name` — extend for `field_map` labels |
| [`browse_helpers.py`](../../../src/yggdrasil/web/browse_helpers.py) | 56–88, 210–324 | `ViewBrowseParams` (single package/stereotype today); context builder — extend for multi-select, `browse_view`, `field_map` |
| [`views.py`](../../../src/yggdrasil/web/views.py) | 108–220 | `ViewBrowseView`, `ViewBrowseGraphJsonView` — add save/delete POST views |
| [`browse.html`](../../../src/yggdrasil/web/templates/web/view/browse.html) | 313–474 | Production shell: header Views stub, single-select filters, disabled Save, `view=` hidden field, element count in toolbar |
| [`mockups/views.py`](../../../mockups/views.py) | 660–780, 907–1040, 990–1007, 1270–1330 | **Port targets:** `field_map_to_content_display`, `_parse_field_map_from_request`, label formatters, package-scoped filter options |
| [`mockup-view-browser.js`](../../../src/yggdrasil/web/static/js/mockup-view-browser.js) | 1–550 | Cascade, field sections, Apply URL builder, Save payload — adapt to production |
| [`view-browser.js`](../../../src/yggdrasil/web/static/js/view-browser.js) | all | Production Cytoscape init — merge layout/fit/label behavior from mockup template |
| [`view-browse-views.feature`](../../features/act-2-view/view-browse-views.feature) | 61–68 | W14 AT/E2E scenarios |
| [`view-browse-content.feature`](../../features/act-2-view/view-browse-content.feature) | 69–79 | W15 AT/E2E scenarios |
| [`tests/fixtures/view_browser.py`](../../../tests/fixtures/view_browser.py) | 65+ | Explorer topology for depth/field assertions |
| [`log_story.py`](../../../tests/support/log_story.py) | 12–41 | `assert_log_story` helper for caplog tests |

MCP / ToolExecutor: **not in scope** — semantic URLs are consumed by Munin via existing browse paths; no new MCP tools.

---

## C — SAO.md Sections That Apply

- **§1 Bounded contexts** — `BrowseView` lives in `graph`; web calls service layer.
- **§3 Code Organization** — browse query + label formatting in service/helpers; views thin.
- **§5 Test Strategy** — pytest + Django test client; integration tests real DB.
- **§11 Observability** — INFO at save/load/expand/delete decision points; caplog proof.
- **Retrospective — Named Views (W14)** — payload v1 schema, `mode=` param.
- **Retrospective — Views v2 (W15)** — `content.field_map`, viewport nullable keys.

---

## D — Tests to Create

### W14 — BrowseView persistence (`tests/graph/test_browse_view_service.py` — new)

| Test | Asserts |
|------|---------|
| `test_save_browse_view_creates_record` | ORM row with slug unique per model+owner |
| `test_save_browse_view_rejects_duplicate_slug` | ValidationError / 400 |
| `test_list_browse_views_scoped_to_model_and_owner` | 61–65 catalog scope |
| `test_expand_browse_view_to_query_string` | `browse_view=` → package, depth, mode |
| `test_delete_browse_view_owner_only` | Viewer cannot delete |
| `test_payload_v1_roundtrip` | filters + levels.depth + presentation |
| `test_save_browse_view_log_story_happy` | caplog: entry, processing, exit with slug= |
| `test_save_browse_view_log_story_reject` | caplog: validation on empty name / wrong model |

### W14 — Web (`src/yggdrasil/web/tests/test_view_browse_views.py` — new)

| Test | Asserts |
|------|---------|
| `test_views_dropdown_on_canvas_toolbar` | 61: `views-dropdown` visible; not in header |
| `test_save_view_post_creates_browse_view` | 62: POST → 302/200 + ORM |
| `test_browse_view_slug_loads_equivalent_filters` | 64: GET `?browse_view=` shows filtered content |
| `test_viewer_cannot_save_view` | 68: save buttons absent |
| `test_mode_query_param_replaces_view` | `?mode=table` works; `?view=` deprecated or aliased one release |
| `test_view_browse_save_log_story_happy` | caplog: ViewBrowseSaveView beats |

### W15 — Content helpers (`tests/graph/test_browse_content.py` — new; port from mockup tests)

| Test | Asserts |
|------|---------|
| `test_parse_field_map_from_query` | `field_component=name&field_component=owner` |
| `test_field_map_to_node_label_multiline` | `Name: munin\nOwner: platform-team` |
| `test_field_map_to_table_columns` | Name + Stereotype first, then field paths |
| `test_package_scoped_stereotype_options` | 79: package narrows stereotype list |
| `test_default_field_map_name_only` | 70: empty field_map → name label |
| `test_browse_content_log_story_happy` | caplog: field_map resolved, path count |

### W15 — Web + graph JSON (`test_view_browse_content.py` — new)

| Test | Asserts |
|------|---------|
| `test_field_sections_render_when_stereotype_selected` | 69, 72: `view-fields-component` |
| `test_filters_first_toolbar_controls` | 77: filters-toggle, apply-filters-btn, view-field-sections |
| `test_graph_json_includes_formatted_label` | 70–71: node data.label multiline |
| `test_table_columns_from_field_map` | 71 |
| `test_apply_filters_clears_browse_view_param` | URL builder / redirect behavior |
| `test_save_view_persists_field_map` | 73 |
| `test_load_view_restores_field_map` | 74 |
| `test_viewport_saved_and_restored_graph_only` | 75–76 |
| `test_view_browse_content_log_story_happy` | caplog: field_map in context + graph JSON |

### Behave step defs (TFK-07 — before E2E green)

Add to `docs/features/CATALOG.md` + `tests/features/steps/view_browser_steps.py`:

- `When Priya saves the current browse session as View "{name}"`
- `When Priya selects View "{name}" from the Views dropdown`
- `When Priya applies browse filters`
- `When Priya selects element stereotype "{slug}"`
- `When Priya checks visible field "{path}" for stereotype "{slug}"`
- `Then the stored View payload includes field_map for stereotype "{slug}"`
- `Then graph node "{name}" displays label containing "{text}"`

### E2E (@wip scenarios — Playwright after AT green)

- 71, 74, 75, 78: in-node labels, load View, viewport restore

---

## E — Log Story Script

| Where | Beat | Trigger | Must include |
|-------|------|---------|--------------|
| `BrowseViewService.save` | entry | POST save | `user_pk=`, `model_slug=`, `name=` |
| `BrowseViewService.save` | validation | duplicate slug / empty name | `reason=` |
| `BrowseViewService.save` | exit | success | `slug=`, `browse_view_id=` |
| `BrowseViewService.expand_to_params` | entry | `browse_view=` load | `slug=`, `user_pk=` |
| `BrowseViewService.expand_to_params` | branch | not found / wrong owner | `reason=not_found` |
| `BrowseViewService.expand_to_params` | exit | success | `depth=`, `mode=` |
| `BrowseViewService.delete` | exit | owner delete | `slug=`, `deleted=` |
| `browse_helpers.parse_view_browse_params` | processing | field_map parsed | `field_stereotypes=`, `field_path_count=` |
| `browse_content.resolve_field_map` | processing | merge query + saved View | `source=query\|payload` |
| `browse_service.format_node_label` | processing | label built | `element_id=`, `path_count=` |
| `ViewBrowseView.get` | branch | browse_view expanded | `browse_view=`, `expanded=` |
| `ViewBrowseSaveView.post` | exit | save redirect | `slug=`, `model_slug=` |
| `ViewBrowseGraphJsonView.get` | exit | JSON | `field_map_stereotypes=`, `node_count=` |

Log-story tests: pair each write path with `*_log_story_happy` and reject path where applicable.

---

## F — MCP Tools to Expose

**Not applicable.** Named Views and field_map are web-layer user preferences. Munin may construct semantic URLs (`browse_view=` or explicit `field_*` params) using existing browse endpoints — no new MCP tool registration.

---

## Current State Assessment

### Reusable (verified)

| Component | Location | Notes |
|-----------|----------|-------|
| BFS depth subgraph | `browse_service.subgraph_from_roots` | W13 shipped |
| Traversal tree SSR | `browse_helpers.build_traversal_tree` | W13 shipped |
| Model switcher | `browse.html` + context | W12 shipped |
| Cytoscape shell | `view-browser.js` | Needs label/layout port from mockup |
| Mockup field_map pipeline | `mockups/views.py` + 16 pytest tests | **Port to `src/yggdrasil/graph/browse_content.py`** |
| Log story helper | `tests/support/log_story.py` | Ready |

### Missing

| Gap | Scenarios |
|-----|-----------|
| `graph.BrowseView` model + migration | 62–68 |
| Save/delete/load HTTP endpoints | 62–66, 68 |
| `browse_view=` expansion in param parser | 64, 63 |
| `mode=` migration (from `view=`) | all graph/table AT |
| Toolbar layout (Views on canvas, no count) | 61, 36 |
| Multi-select package/stereotypes + edge stereotype | 79, 78 |
| Field sections + `field_*` URL encoding | 69–79 |
| Dynamic graph/table labels from field_map | 70–74 |
| Viewport capture/restore | 75–76 |
| Behave step defs for @wip scenarios | 62–79 |

---

## Clarification Questions (resolved — no blocker)

| Q | Answer |
|---|--------|
| Preset picker in Filters? | **No** — mockup-validated; presets may seed defaults in service only |
| W14 vs W15 UI split? | W14: ORM + save/load + toolbar shell; W15: Filters-first field_map UI + rendering |
| Port mockup JS wholesale? | Adapt patterns into `view-browser.js`; keep mockup route for design reference |

---

## Implementation Plan

Each slice: skeleton → red tests → green → log-story → `pytest` → commit.

### W14 — Named Views persistence

#### Slice W14-0 — Spec + mode migration prep

- [ ] Add `@mode` alias in `parse_view_browse_params`: accept `mode=`; deprecate `view=` (read both, prefer `mode`).
- [ ] Update Gherkin/features still using `?view=` → `?mode=` (grep `view=graph`).
- [ ] **Commit:** `docs(spec): migrate view browser AT to mode= query param`

#### Slice W14-1 — BrowseView model + service skeleton

- [ ] Add `BrowseView` to [`graph/models.py`](../../../src/yggdrasil/graph/models.py):
  - FK `model` → `YggdrasilModel`, FK `owner` → `User`
  - `name`, `slug`, `payload` JSONField, timestamps
  - `UniqueConstraint(model, owner, slug)`
- [ ] Migration + admin register (read-only list for ops).
- [ ] Add [`graph/browse_view_service.py`](../../../src/yggdrasil/graph/browse_view_service.py):
  - `save_view(user, model, name, payload) -> BrowseView`
  - `list_views(user, model) -> QuerySet`
  - `get_view(user, model, slug) -> BrowseView`
  - `delete_view(user, model, slug) -> None`
  - `expand_to_query_params(view) -> dict[str, list[str]]`
  - Payload validator for v1 keys (`filters`, `levels`, `presentation`)
- [ ] Unit tests + log-story (Section D W14 service rows).
- [ ] **Commit:** `feat(graph): add BrowseView model and save/list/delete service`

#### Slice W14-2 — HTTP save/delete + browse_view expansion

- [ ] `ViewBrowseSaveView` POST — parse current params → payload v1 → save → redirect to `?browse_view={slug}`
- [ ] `ViewBrowseDeleteView` POST — owner-only delete
- [ ] Extend `parse_view_browse_params`: if `browse_view` present, expand via service (unless explicit filter overrides — document precedence)
- [ ] Routes in [`web/urls.py`](../../../src/yggdrasil/web/urls.py):
  - `models/<slug>/views/save/`
  - `models/<slug>/views/<slug>/delete/`
- [ ] View tests + log-story.
- [ ] **Commit:** `feat(web): BrowseView save/delete and browse_view expansion`

#### Slice W14-3 — Production template shell (toolbar + modal)

- [ ] Move Views dropdown from header → canvas toolbar (`views-dropdown`); remove header dropdown.
- [ ] Wire Save View button + modal (`save-view-btn`, `save-view-name-input`, `save-view-confirm-btn`).
- [ ] Populate dropdown from `list_views`; `view-option-{slug}` links with `?browse_view=`.
- [ ] Delete affordance (`delete-view-btn`) owner-only.
- [ ] Remove `#browserElementCount` from toolbar (per mockup).
- [ ] Rename `clear-filters-btn` in toolbar → keep Clear **only** in filter panel footer (`filter-panel-clear-btn`).
- [ ] AT scenario 61 green.
- [ ] **Commit:** `feat(web): Views dropdown and save modal on View Browser`

#### Slice W14-4 — Behave steps + @wip 62–68

- [ ] TFK-07 step defs for save/load/delete (CATALOG updated).
- [ ] Green AT for 62–68 (E2E @wip acceptable until Playwright).
- [ ] **Commit:** `test(view-browser): AT steps for named Views W14`

**W14 checkpoint:**

```yaml
checkpoint:
  command: "pytest src/yggdrasil/graph/tests/test_browse_view_service.py src/yggdrasil/web/tests/test_view_browse_views.py tests/features/ -k 'VIEW-BROWSE-1-6' -x"
  log_story_command: "pytest src/yggdrasil/graph/tests/test_browse_view_service.py src/yggdrasil/web/tests/test_view_browse_views.py -k log_story -x"
```

---

### W15 — Filters-first Content + viewport

#### Slice W15-1 — Port content helpers from mockup

- [ ] Create [`graph/browse_content.py`](../../../src/yggdrasil/graph/browse_content.py):
  - Port `parse_field_map_from_query`, `field_map_to_content_display`, `format_node_label_from_paths`, `format_edge_label`, `build_table_columns`
  - Operate on real `Element`/`Relationship` property dicts (not mock dicts)
- [ ] Port/adapt tests from [`tests/mockups/test_view_browse_mockup.py`](../../../tests/mockups/test_view_browse_mockup.py).
- [ ] **Commit:** `feat(graph): browse content field_map helpers`

#### Slice W15-2 — Param parser + payload v2

- [ ] Extend `ViewBrowseParams`: `packages: list[str]`, `element_stereotypes`, `edge_stereotypes`, `field_map`, `browse_view`
- [ ] `build_view_browse_context`: merge `browse_view` payload field_map with query `field_*` (query wins)
- [ ] Extend `BrowseView` payload validator: optional `content.field_map`, `viewport`
- [ ] Save includes field_map + optional viewport from POST body
- [ ] **Commit:** `feat(web): parse field_map and v2 BrowseView payload`

#### Slice W15-3 — Filters panel UI (multi-select + field sections)

- [ ] Replace single-select package/stereotype with multi-select (`filter-package`, `filter-stereotype`, `filter-edge-stereotype`)
- [ ] Add `view-field-sections` / `view-field-{slug}-{path}` from stereotype `property_schema`
- [ ] Package-scoped stereotype options (server SSR catalog + JS cascade from mockup)
- [ ] Filter footer: Clear · Save/Update View · **Apply Filters** (sole primary)
- [ ] `active-view-name` badge when `browse_view` loaded
- [ ] Apply clears `browse_view` in client URL builder (port from mockup JS)
- [ ] AT 69, 72, 77 green.
- [ ] **Commit:** `feat(web): Filters-first field_map editor panel`

#### Slice W15-4 — Canvas rendering (graph + table + inspector visible fields)

- [ ] `browse_service` graph JSON: `data.label` = multiline Key:value from field_map
- [ ] Edge labels from relationship field_map
- [ ] Table partial: dynamic columns from field_map
- [ ] Inspector partial: **Visible fields** section (optional slice if inspector partial exists)
- [ ] Cytoscape: port grid/cose selection + `fitGraph()` after layout from mockup template
- [ ] AT 70–71, 73–74 green.
- [ ] **Commit:** `feat(web): render graph and table from content field_map`

#### Slice W15-5 — Viewport opt-in

- [ ] Save modal checkbox `save-view-include-viewport` (graph mode only)
- [ ] JS: capture zoom/pan/center_element_id on save
- [ ] JS: restore viewport after layout + fit on load
- [ ] AT/E2E 75–76.
- [ ] **Commit:** `feat(web): optional graph viewport in saved Views`

#### Slice W15-6 — Behave + E2E @wip

- [ ] TFK-07 steps for field_map scenarios.
- [ ] Playwright smoke for 71, 74, 75.
- [ ] **Commit:** `test(view-browser): AT and E2E for Views v2 field_map`

**W15 checkpoint:**

```yaml
checkpoint:
  command: "pytest src/yggdrasil/graph/tests/test_browse_content.py src/yggdrasil/web/tests/test_view_browse_content.py tests/features/ -k 'VIEW-BROWSE-1-6[89]' -x"
  log_story_command: "pytest src/yggdrasil/graph/tests/test_browse_content.py src/yggdrasil/web/tests/test_view_browse_content.py -k log_story -x"
```

---

## Commit Strategy

Angular convention; one concern per commit (matching slices above). Each slice ends with behavior + log-story green when Section E beats touched.

---

## Plan Closure (BPE-01)

1. Create GitHub issue **W14:** `VIEW-BROWSE-1 W14: Named Views (BrowseView save/load)` — body inlines A–F (W14 scope); label `status-queued`
2. Create GitHub issue **W15:** `VIEW-BROWSE-1 W15: Filters-first field_map + viewport` — blocked by W14 `#N`; label `status-queued`
3. Update [`INDEX.md`](INDEX.md) with plan link + `#N` / `#M`
4. **Commit:** `docs(plan): BPE-W14-W15 Views plan and GitHub issues #N #M`

**GitHub issues:** W14 [#94](https://github.com/FeatureFactory-io/yggdrasil/issues/94) · W15 [#95](https://github.com/FeatureFactory-io/yggdrasil/issues/95) blocked on W14

---

## Lessons Learned

*(Complete when closing BPE-01 — placeholder for GitHub issue body.)*

---

## Definition of Done (wave-level)

- [ ] Scenarios 61–68 (W14) AT green; E2E @wip documented
- [ ] Scenarios 69–79 (W15) AT green; E2E for 71/74/75
- [ ] Production UI matches mockup reconciliation (Filters-first, canvas toolbar Views)
- [ ] Log Story Script rows proven via caplog
- [ ] No superseded controls shipped (Content dropdown, node count badge)
- [ ] `make test` + `make check` pass
- [ ] Feature files + `_implementation_notes.md` updated with shipped status
