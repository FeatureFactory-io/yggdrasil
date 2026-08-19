# API ↔ MCP Reconciliation

**Purpose:** Single source of truth for REST endpoint ↔ MCP tool parity (SAO §18.7).
**Update rule:** Add or change a row whenever a tool or endpoint ships or its contract changes.

**Status:** Spec reconciliation for diagram editor (BPE-08, 2026-08-19). Diagram rows are **spec** — not yet implemented in production.

---

## Diagram tools (W26 target)

| MCP tool | HTTP endpoint | Method | Auth | Write? | Notes |
|---|---|---|---|---|---|
| `list_diagrams` | `/api/v1/diagrams/?model_id=…&package_id=…&tag=…&has_draft=…` | GET | Bearer | No | Returns `has_draft` per row |
| `get_diagram` | `/api/v1/diagrams/{id}/` | GET | Bearer | No | Committed metadata + membership + presentation |
| `get_diagram_draft` | `/api/v1/diagrams/{id}/draft/` | GET | Bearer | No | 404 when no draft |
| `update_diagram_draft` | `/api/v1/diagrams/{id}/draft/` | PATCH | Bearer | Yes | Merge draft — no ChangeSet |
| `update_diagram_draft` (create session) | `/api/v1/diagrams/draft/` | POST/PATCH | Bearer | Yes | Create-mode session before first Save |
| `save_diagram` | `/api/v1/diagrams/{id}/save/` | POST | Bearer | Yes | Munin → ChangeSet → clear draft |
| `discard_diagram_draft` | `/api/v1/diagrams/{id}/draft/` | DELETE | Bearer | Yes | Drop draft only |
| `delete_diagram` | `/api/v1/diagrams/{id}/` | DELETE | Bearer | Yes | Requires confirm; `delete_diagram` op |
| `move_diagram` | `/api/v1/diagrams/{id}/move/` | POST | Bearer | Yes | Body: `{ "package_id": … }` |

---

## Existing tools (reference)

| MCP tool | HTTP endpoint | Method | Status |
|---|---|---|---|
| `list_elements` | `/api/v1/elements/?model_id=…` | GET | Partial / as-built |
| `get_element` | `/api/v1/elements/{id}/` | GET | Partial |
| `list_relationships` | `/api/v1/relationships/?model_id=…` | GET | Partial |
| `list_stereotypes` | `/api/v1/stereotypes/?model_id=…` | GET | Partial |
| `list_packages` | `/api/v1/packages/?model_id=…` | GET | Spec |
| `list_changesets` | `/api/v1/changesets/?model_id=…` | GET | Partial |
| `get_changeset` | `/api/v1/changesets/{id}/` | GET | Partial |
| `propose_changeset` | `/api/v1/changesets/` | POST | Partial |
| `apply_changeset` | `/api/v1/changesets/{id}/apply/` | POST | Partial |
| `list_ratatosk_runs` | `/api/v1/ratatosk-runs/?model_id=…` | GET | Partial |
| `get_ratatosk_run` | `/api/v1/ratatosk-runs/{id}/` | GET | Partial |
| `trigger_ratatosk_run` | `/api/v1/ratatosk-runs/` | POST | Partial |
| `search` | `/api/v1/elements/search/` | GET | Partial |
| `traverse` | `/api/v1/browse/traverse/` | GET | Partial |

---

## ChangeSet ops (diagram save batch)

| Op | Trigger | Rollback (spec) |
|---|---|---|
| `create_diagram` | First Save on create session | `delete_diagram` |
| `update_diagram` | Rename, move package, summary/tags | inverse field patch |
| `delete_diagram` | List hover Delete | `create_diagram` + presentation restore |
| `update_diagram_presentation` | Save with layout/membership diff | prior presentation snapshot |
| `add_element` | Pending elements in draft | `delete_element` |
| `add_relationship` | Pending relationships in draft | `delete_relationship` |
| `add_to_diagram` | Place elements on canvas | remove from diagram membership |

**Note:** As-built `add_to_diagram` rollback inverse is broken — fix in W24 (`changeset/services.py`).

---

## Drift log

| Date | Change |
|---|---|
| 2026-08-19 | BPE-08: diagram draft/save MCP + REST rows; new ChangeSet ops documented |
