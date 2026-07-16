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
| **ELEMENT** | Vertex in the graph (Application, Capability, etc.) — stereotype defines kind |
| **RELATIONSHIP** | Edge between elements (depends_on, owns, etc.) |
| **STEREOTYPE** | Metamodel definition: allowed properties, edge rules |
| **PACKAGE** | Container / view root (Business View, Technology View) |
| **DIAGRAM** | Cytoscape presentation layout for a package |
| **CHANGESET** | Staged writes from Ratatosk awaiting review |
| **VIEW** | Saved query / filter configuration (view browser) |

### Traceability Chain

Every Screen ID must appear in:

1. **User Journey** (`docs/features/user_journey.md`) — `#### Screen: {ENTITY}-{OPERATION}-{VERSION}`
2. **Screen Flow** (`docs/ux/2_dialogue-maps/screen-flow.drawio`) — box label
3. **Feature File** (`docs/features/act-*/{entity}-{operation}.feature`) — feature title
4. **Template** (`templates/...`) — HTML comment + `data-testid`
5. **Tests** (`tests/...` for pytest; `features/at/` or `features/e2e/` for behave AT/E2E) — test names reference Screen ID

**Gherkin dual-location:** specs live in `docs/features/`; CI-owned runners in `features/at/` (AT) and `features/e2e/` (E2E). BPE-04/05 promote (copy) and keep both in sync. See `docs/architecture/test-architecture.md` §4.

### Semantic URLs (API / MCP)

REST and MCP expose graph views via semantic paths:

```
/views/{package_slug}/{stereotype}?filter={json}
/elements/{id}
/traverse?from={id}&depth={n}&as_of={iso8601}
```

### Important Guidelines

- Plan before executing; work incrementally (one Act at a time)
- Write tests before implementation; maintain 100% pass rate
- Use `data-testid` on all interactive elements
- Prioritize accessibility (ARIA, semantic HTML, keyboard navigation)
- Commit after each major step with conventional commits (`feat`, `fix`, `docs`, `chore`)
