# BPE-W7 — Three-Panel View Browser Explorer

**Branch:** `feature/act-2-view-browser-v03`
**Wave:** W7 — shell + SSR navigator (production `/views/`)
**Unlocks:** VIEW-BROWSE-1 scenarios **16–20** (AT)

---

## A — Context Map

| File | Responsibility |
|------|----------------|
| `src/yggdrasil/graph/browse_service.py` | `element_summary` exposes `slug`, `package_slug`; reuse for navigator rows |
| `src/yggdrasil/web/browse_helpers.py` | `build_package_tree`, extend `build_view_browse_context` with `packages`, `model_name` |
| `src/yggdrasil/web/views.py` | `ViewBrowseView` — no URL changes; HTMX partial path preserved |
| `src/yggdrasil/web/templates/web/view/browse.html` | Three-panel shell replacing single-column layout |
| `src/yggdrasil/web/templates/web/view/partials/navigator.html` | Left panel SSR package tree |
| `src/yggdrasil/web/templates/web/view/partials/inspector_shell.html` | Right panel empty-state shell |
| `src/yggdrasil/web/templates/web/view/partials/results.html` | Centre canvas table/graph |
| `src/yggdrasil/web/static/js/view-browser.js` | Panel collapse toggles only |
| `mockups/views.py` | DRY — import `build_package_tree` from `browse_helpers` |
| `tests/fixtures/view_browser.py` | Explorer fixture (19 elements, 11 rels) |
| `docs/features/steps/view_browser_steps.py` | Behave Given fixture steps + persona stubs |

---

## B — Do-Not-Do

- Do **not** target `/mockups/` in AT/E2E (CATALOG AT honesty rule).
- Do **not** bypass `browse_service` for element lists — navigator SSR reads the same filtered queryset as table/graph.
- Do **not** add root `urls.py` / `settings.py` changes without human approval.
- Do **not** implement selection sync / embed inspector content in W7 — inspector shows **empty state** only.
- Do **not** remove or weaken existing v0.2 testids — extend layout.

---

## C — SAO Sections

- **§ Web rendering:** Server-rendered + HTMX (filters stay GET form; HTMX partial path preserved).
- **§ Test strategy:** AT for shell testids; E2E deferred to Phase 4 (W8–W11).
- **§18 MCP:** Not in scope — read tools already delegate to `browse_service`.

---

## D — Tests to Create

| Test | Asserts |
|------|---------|
| `test_view_browser_three_panel_shell` | Scenario 16: `browser-nav-panel`, `browser-inspector-panel`, `graph-cy-container`, toggle buttons |
| `test_view_browser_full_height_layout` | Scenario 16: `yrg-view-browser` on body |
| `test_view_browser_navigator_package_tree` | Scenarios 17–18: package toggles + model name |
| `test_view_browser_navigator_lists_elements` | Scenario 19: seeded element names in HTML |
| `test_view_browser_navigator_search_input` | Scenario 20: `browser-search-input` present |
| `test_view_browser_log_story_happy` | caplog: `ViewBrowseView.get` + context build beats |
| `tests/fixtures/test_view_browser_seed.py` | Explorer constants, seed helper, explorer fixture |
| `tests/web/test_browse_helpers.py` | `build_package_tree`, row slugs, context packages |
| `tests/features/test_view_browser_at_steps.py` | Behave Given + navigation/assertion steps |

Existing v0.2 tests in `test_view_browse.py` must remain green.

---

## E — Log Story Script

| Where | Beat | Trigger | Must include |
|-------|------|---------|--------------|
| `ViewBrowseView.get` | entry | GET /views/ | `user_pk=`, `element_count=` |
| `build_view_browse_context` | processing | context built | `package_count=`, `element_count=` |
| `ViewBrowseGraphJsonView.get` | exit | graph JSON | `nodes=`, `edges=` |

---

## F — MCP Tools

**Not applicable** — UI-only wave.
