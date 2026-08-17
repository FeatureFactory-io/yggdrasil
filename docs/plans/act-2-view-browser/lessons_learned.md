# Act 2 View Browser — Lessons Learned

## How to use

After every scenario checkpoint (pass or fail), append one entry.
Categories: `workflow-drift` | `tech-blocker` | `mockup-delta` | `decision`

## Seed entries (pre-implementation)

| Date | Category | Observation | Resolution |
|------|----------|-------------|------------|
| 2026-07-24 | workflow-drift | Gherkin hit `/mockups/view/browse/`; prod is `/views/` | Graduated URLs in feature file + `pages.py` |
| 2026-07-24 | workflow-drift | Feature cited `seed.json` 6 elements; seed has auth only | Added `tests/fixtures/view_browser.py` 6-element fixture |
| 2026-07-24 | workflow-drift | `GraphBrowseService` referenced but missing | Created `graph/browse_service.py` |
| 2026-07-24 | mockup-delta | Prod missing graph div, navbar links | Graduated from mockup in v0.2 |
| 2026-07-24 | decision | Element detail links → `/elements/{id}/` until Act 3 | Test link presence only |

## Implementation log

| Date | Category | Observation | Resolution |
|------|----------|-------------|------------|
| 2026-07-24 | tech-blocker | `list_elements` list comprehension syntax error | Fixed bracket in `browse_service.py` |
| 2026-07-24 | tech-blocker | ViewBrowse 500 when no `yggdrasil` model in DB | `build_view_browse_context` catches `ValueError`, empty state |
| 2026-07-24 | mockup-delta | Nav links for Elements/Relationships still mock URLs | Prod navbar uses `/mockups/…` until those Acts ship; testids present |
| 2026-07-24 | decision | Cytoscape loaded page-level only | CDN in `browse.html` `extra_js` per IA §5 |
| 2026-07-27 | decision | W7 ships SSR navigator + empty inspector; selection bus deferred W8–W10 | Three-panel shell on `/views/`; `@wip` only on E2E scenarios 21+ |
| 2026-07-27 | workflow-drift | Mockup `build_package_tree` duplicated in mockups | Shared helper in `browse_helpers.py`; mockup wraps adapter |
| 2026-07-27 | decision | `element-row-{slug}` primary testid in v0.3; `{id}` on `data-element-id` | Keeps v0.2 name-based assertions green |
| 2026-08-17 | tech-blocker | RBAC tests with `owner_group` failed when user lacked matching `Group` | Use `UserFactory(is_architect=True)` trait or `groups="architect"`; verify `user.groups` when mixing manual `Group` with factory users |
| 2026-08-17 | tech-blocker | AT Background + scenario both seeded models → `IntegrityError` on `(model_id, slug)` | Idempotent `get_or_create` / update-in-place in behave Given steps |
| 2026-08-17 | tech-blocker | Scenario 53 (zero models) still saw Background models | `step_architect_can_read_no_models` reassigns **all** models to unreadable `owner_group` |
| 2026-08-17 | tech-blocker | E2E scenario 51 timeout — switcher not found | Navigator chrome is graph-mode only (`yrg-graph-only`); E2E URL must include `?view=graph` |
| 2026-08-17 | tech-blocker | E2E login via manual `SessionStore` did not authenticate Playwright | Inject `sessionid` from Django test `Client.force_login` → `page.context.add_cookies` (see `tests/e2e/steps/view_browser_steps.py`) |
| 2026-08-17 | workflow-drift | Existing pytest/AT expected 200 on `/views/` after W12 alias | Default to canonical `/models/{slug}/views/…`; reserve alias assertions for scenarios 49/53 |
| 2026-08-17 | tech-blocker | `make test` collection failed on unregistered `@pytest.mark.e2e_self` | Register new markers in `pyproject.toml` `[tool.pytest.ini_options].markers` before use |
| 2026-08-17 | decision | W12 AT + E2E both cover scenario 51; separate step modules | AT: `docs/features/steps/`; E2E: `tests/e2e/steps/` + dedicated `.feature` under `tests/e2e/` |

---

## Documentation & PIP triage (2026-08-17)

| Lesson | Yggdrasil docs | Edda PIP? |
|--------|----------------|-----------|
| E2E Django `sessionid` injection | SAO, test-architecture §6 | **Yes** — generic TFK skill |
| AT Background idempotency | SAO, test-architecture §6 | **Yes** — generic BPE/rule |
| Mode-scoped visibility | IA §6.2.1, test-architecture §6 | **No** — product IA; Edda gets abstract “confirm rendering context” only if needed |
| RBAC factory + `owner_group` | tests/fixtures/CATALOG | **No** — project RBAC shape; one line in Skill 48 sufficient |
| Pytest marker registration | — | **No** — trivial pyproject hygiene |
| Canonical URL migration | — | **No** — one-time CR fallout |
