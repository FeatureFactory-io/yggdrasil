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
