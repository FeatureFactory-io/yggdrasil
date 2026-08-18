# Yggdrasil Conventions (ESM-01)

## Screen ID Convention (Traceability)

All screens follow a consistent naming pattern for end-to-end traceability.

### Format: `{ENTITY}-{OPERATION}-{VERSION}`

**Components:**
- `{ENTITY}` — Uppercase entity name (ELEMENT, RELATIONSHIP, STEREOTYPE, PACKAGE, DIAGRAM, CHANGESET, VIEW, CHAT)
- `{OPERATION}` — Screen operation type (CRUDLF patterns below)
- `{VERSION}` — Version number (usually `-1` for MVP)

### CRUDLF Operations

| Operation | Description |
|-----------|-------------|
| `LIST+FIND` | Entry point: list with search/filter |
| `CREATE_{ENTITY}` | Creation form |
| `VIEW_{ENTITY}` | Detail / read-only view |
| `EDIT_{ENTITY}` | Edit form |
| `DELETE_{ENTITY}` | Deletion confirmation |

**Examples:**
- `ELEMENT-LIST+FIND-1` — Elements list with search/filter
- `ELEMENT-CREATE_ELEMENT-1` — Create new element
- `ELEMENT-VIEW_ELEMENT-1` — View element details
- `RELATIONSHIP-LIST+FIND-1` — Relationships list
- `VIEW-BROWSE-1` — View browser (multi-level filters)
- `CHAT-ASSIST-1` — AI chat assistant
- `CHANGESET-LIST+FIND-1` — Pending change review queue

### Graph Domain Entities

| Entity | Role |
|--------|------|
| **METAMODEL** | Type catalog (convention): Stereotypes + Packages; Model binds immutably |
| **ELEMENT** | Vertex in the graph (Application, Capability, etc.) — stereotype defines kind |
| **RELATIONSHIP** | Edge between elements (depends_on, owns, etc.) |
| **STEREOTYPE** | Metamodel definition: allowed properties, edge rules |
| **PACKAGE** | Metamodel view root (Context, Technology, Application, Code) |
| **DIAGRAM** | Cytoscape presentation layout instance on a Model |
| **CHANGESET** | Staged writes from Ratatosk awaiting review |
| **VIEW** | Saved query / filter configuration (view browser) |

### Traceability Chain

Every Screen ID must appear in:

1. **User Journey** (`docs/features/user_journey.md`) — `#### Screen: {ENTITY}-{OPERATION}-{VERSION}`
2. **Screen Flow** (`docs/ux/2_dialogue-maps/screen-flow.drawio`) — box label
3. **Feature File** (`docs/features/act-*/{entity}-{operation}.feature`) — feature title
4. **Template** (`templates/...`) — HTML comment + `data-testid`
5. **Tests** (`tests/...` for pytest; `docs/features/` for behave AT; `tests/e2e/` for E2E) — test names reference Screen ID

### Semantic URLs (API / MCP)

REST and MCP expose graph views via semantic paths:

```
/models/{model_slug}/views/{package_slug}/{stereotype}?filter={json}&depth={n}&mode={graph|table}&content={preset-slug|custom}
/models/{model_slug}/views/?browse_view={slug}
/elements/{id}
/traverse?from={id}&depth={n}&as_of={iso8601}
```

**`depth` (View Browser):** integer ≥ 1. Filters define the **root set** (matching elements). `depth=N` includes nodes reachable within **N − 1 outgoing hops** from any root (BFS, visited set for cycles). Default when omitted: `1` (roots only). When no element-narrowing filter is applied, roots = **graph sources** (nodes with zero incoming edges). Graph JSON, navigator tree, and table rows all use the same depth-scoped subgraph.

**`mode` (View Browser presentation):** `graph` (three-panel explorer, default) or `table` (results grid). Replaces legacy `view=` query param (W14 migration).

**`browse_view` (named View):** slug of a persisted `graph.BrowseView` for the current Model and signed-in user. Server expands to equivalent filter + depth + mode + content query string; applies saved viewport in graph mode when present in payload. Scoped to `(model, owner)` — not carried across Models.

**`content` (Content preset / custom flag):** built-in preset slug (`minimal`, `current-state`, `jira-info`) or `custom` after field-by-field edits in the Content editor. Presets are shareable via live URL; **`custom`** signals that full `content.bindings` come from session (mockup) or named View payload (W15). Use **Edit content** to pick node primary/secondary fields, edge label, and table columns; **Save View** persists bindings.

### Important Guidelines

- Plan before executing; work incrementally (one Act at a time)
- Write tests before implementation; maintain 100% pass rate
- Use `data-testid` on all interactive elements
- Prioritize accessibility (ARIA, semantic HTML, keyboard navigation)
- Commit after each major step with conventional commits (`feat`, `fix`, `docs`, `chore`)
