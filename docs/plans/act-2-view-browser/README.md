# Act 2 View Browser — README

## Mockup graduation checklist

Every wave must:

1. Read mockup: `src/yggdrasil/web/templates/mockups/view/browse.html`
2. Diff prod: `src/yggdrasil/web/templates/web/view/browse.html`
3. Port `data-testid` values from [`docs/features/CATALOG.md`](../../features/CATALOG.md) § VIEW-BROWSE-1
4. Replace `{% url 'mockup_*' %}` with `{% url 'web:*' %}`
5. Wire service-backed data via `browse_service`
6. Enable controls only when backend slice is green
7. Point Gherkin AT at `/views/` (not `/mockups/…`)
8. Append row to [`lessons_learned.md`](lessons_learned.md)

## Final step (mandatory)

After every scenario checkpoint: append one row to `lessons_learned.md`.
