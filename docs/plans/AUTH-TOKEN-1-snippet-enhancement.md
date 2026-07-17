# AUTH-TOKEN-1 Snippet Enhancement — Implementation Plan

**Feature:** Usage snippets show the real token value after creation; each snippet has a copy-to-clipboard button.
**Screen:** AUTH-TOKEN-1 (`/auth/tokens/`)
**Branch:** `feature/auth-token-1-snippet-copy`

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `src/yggdrasil/auth/templates/auth/token.html` | 87–132 | Usage snippet blocks to modify — add copy buttons + conditional token value |
| `src/yggdrasil/auth/templates/auth/token.html` | 70–85 | `new_token_raw` block — already server-rendered; same variable drives snippets |
| `docs/features/act-0-auth/auth-token.feature` | 43–48 | AUTH-TOKEN-1-05 pattern — POST create scenario to extend |
| `docs/features/CATALOG.md` | 212–223 | AUTH-TOKEN-1 testid table — append new testids here |
| `src/yggdrasil/auth/tests/test_token_list_view.py` | 1–end | Integration view test pattern to follow |

---

## Do Not Do

- Do NOT create backend views, models, services, or URL patterns — this is pure frontend
- Do NOT store raw token values in the database (SAO security rule — only SHA-256 hash is stored)
- Do NOT use JavaScript to fetch the token from the backend — raw value already in page context via `new_token_raw`
- Do NOT add SPA/React patterns — server-rendered templates + inline JS only (SAO §Web)
- Do NOT add HTMX on this page — no partial reload needed

---

## SAO.md Sections That Apply

- §Web: server-rendered Django templates + HTMX; no SPA; client-side JS allowed for clipboard/cosmetic interactions
- §Auth: raw token shown exactly once at creation time — never again; this rule constrains scope to `new_token_raw` only

---

## Tests to Create

| Test | Level | Proves |
|------|-------|--------|
| `test_token_list_view_shows_snippet_copy_buttons` | view | GET /auth/tokens/ → 200 + all 4 `data-testid="snippet-copy-*"` present |
| `test_token_create_view_snippets_contain_raw_token` | view | POST /auth/tokens/create/ → response HTML snippets contain the raw token value |
| AT: AUTH-TOKEN-1-09 | AT | Each snippet block renders its copy button testid |
| AT: AUTH-TOKEN-1-10 | AT | After token generation, snippets contain the raw token value |

---

## Logs to Emit

No new log points required — this feature adds no new server-side branches. Existing `TokenService.create_token` logging already covers the POST path.

---

## MCP Tools to Expose

Not applicable — UI-only enhancement.

---

## Implementation Steps

### 1. Feature file — add 2 scenarios
File: `docs/features/act-0-auth/auth-token.feature`

- AUTH-TOKEN-1-09: GET `/auth/tokens/` → all 4 `snippet-copy-*` testids visible
- AUTH-TOKEN-1-10: POST create → snippets contain the raw token value (server-rendered)

### 2. CATALOG.md — register new testids
File: `docs/features/CATALOG.md` → AUTH-TOKEN-1 table

Add: `snippet-copy-shell`, `snippet-copy-ratatosk`, `snippet-copy-mcp-docker`, `snippet-copy-mcp-direct`

### 3. Template — `auth/token.html`
For each of the 4 snippet `<pre>` blocks:
- Wrap in a `div class="position-relative"`
- Replace `&lt;token&gt;` literal with `{% if new_token_raw %}{{ new_token_raw }}{% else %}&lt;token&gt;{% endif %}`
- Add a `<button data-testid="snippet-copy-{name}" onclick="copySnippet(this)">` after the `<pre>`

Add `copySnippet(btn)` in `{% block extra_js %}`:
```javascript
function copySnippet(btn) {
  const pre = btn.previousElementSibling;
  navigator.clipboard.writeText(pre.textContent).then(() => {
    const orig = btn.innerHTML;
    btn.innerHTML = '<i class="fa-solid fa-check" aria-hidden="true"></i> Copied';
    setTimeout(() => { btn.innerHTML = orig; }, 2000);
  });
}
```

### 4. View tests (pytest)
File: `src/yggdrasil/auth/tests/test_token_list_view.py` (or new file)

- `test_token_list_view_shows_snippet_copy_buttons`: GET, assert 4 testids in response
- `test_token_create_view_snippets_contain_raw_token`: POST create, assert raw token in HTML

### 5. Run tests
```
uv run pytest src/yggdrasil/auth/tests/ -x
uv run python manage.py behave --simple docs/features/act-0-auth/auth-token.feature
```

---

## Acceptance Criteria

- [ ] `uv run pytest src/yggdrasil/auth/tests/ -x` passes
- [ ] `uv run python manage.py behave --simple docs/features/act-0-auth/auth-token.feature` passes (10/10 scenarios)
- [ ] Each row in Tests to Create has a passing test
