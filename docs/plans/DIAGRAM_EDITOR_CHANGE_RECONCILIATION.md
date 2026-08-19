# Change Reconciliation — Cytoscape Diagram Editor (Draft + Munin Save)

**Feature:** `DIAGRAM-EDITOR-1`, `DIAGRAM-LIST+FIND-1`, `DIAGRAM-CREATE_DIAGRAM-1`, related screens
**Activity:** BPE-08 Process Change Request
**Status:** Approved — spec artifacts updated 2026-08-19
**Date:** 2026-08-19
**Prerequisite:** [`IDEA_DIAGRAM_JSON_PRESENTATION_FORMAT.md`](IDEA_DIAGRAM_JSON_PRESENTATION_FORMAT.md); View Browser W1–W19 shipped ([`act-2-view-browser/INDEX.md`](act-2-view-browser/INDEX.md))

---

## Trigger

Elena and Priya need **curated diagram views** of the architecture graph — not exploratory View Browser subgraphs, but named diagrams with saved layout, membership, and styling. Editors work on a **draft** (GUI canvas, ADE chat, MCP); **Save** commits via **Munin** → ChangeSet. Inventory queries need diagram **summary** and **tags** after save.

Prior spec: Act 10 `DIAGRAM-LIST+FIND-1` only — list + “Open in Graph Editor”; no View Browser entry, no draft model, no MCP write path, no hover lifecycle actions.

**Scope:** Cytoscape in-app editor only (Gaphor Phase 3 deferred per IDEA doc).

This activity does **not** implement production code (BPE-01 waves W20–W27).

---

## Reconciliation matrix

Affected Screen IDs: `VIEW-BROWSE-1`, `DIAGRAM-CREATE_DIAGRAM-1`, `DIAGRAM-EDITOR-1`, `DIAGRAM-LIST+FIND-1`, `DIAGRAM-DELETE_DIAGRAM-1`, `DIAGRAM-MOVE_DIAGRAM-1`, `CHAT-MUNIN-1` (diagram-scoped), `CHANGESET-VIEW_CHANGESET-1`. MCP tools — spec layer.

| Layer | Source | Pre-CR state | Drift? | Notes |
|-------|--------|--------------|--------|-------|
| IDEA doc | `IDEA_DIAGRAM_JSON_PRESENTATION_FORMAT.md` | Phase 1 list-first layout editor | **Y** | View Browser entry; draft; Munin enrichment |
| User journey | `user_journey.md` Act 2 / 10 | List + open editor; MCP read only | **Y** | Add Diagram; editor; draft/save; MCP write |
| Scenarios | `diagram-list.feature` | Open-in-editor; `@pending-mockup` | **Y** | Edit/Delete/Move; new feature files |
| Mockups | `mockups/view/browse.html` | No Add Diagram | **Y** | `mockups/diagram/list.html`, `editor.html` |
| Screen flow | `screen-flow.md` | DIAGRAM list only | **Y** | VB → editor; new ChangeSet ops |
| IA guidelines | `IA_guidelines.md` | Read-only Cytoscape in browser | **Y** | Editor organism; Draft badge |
| Conventions | `conventions.md` | DIAGRAM entity only | **Y** | New Screen IDs |
| Architecture | `SAO.md` | `get_diagram` spec; no draft tools | **Y** | Draft MCP + REST parity |
| As-built | ORM + `add_to_diagram` | No editor routes | **Y** | Greenfield W20+ |
| Prior plan | IDEA Phase 1 | Positions-only editor | **Y** | Superseded UX |

**Fast path:** Not applicable.

---

## Proposed decisions (approval gate)

| # | Question | Decision |
|---|----------|----------|
| **Q1** | Metamodel vs C4 for diagram kinds | **Metamodel defines diagram catalog**; create modal picks kind from Model’s Metamodel (C4 example: Context/Container/Component/Code → `Diagram.diagram_type`). Package scopes placement. |
| **Q2** | Edit vs committed state | **Draft-first** — GUI/MCP/chat patch draft; **Save** → Munin → ChangeSet. **Discard** drops draft. |
| **Q3** | Draft pill visibility | Show **`Draft`** badge on list + editor when committed `diagram_id` has unsaved server draft. Brand-new Create sessions are editor-only until first Save. |
| **Q4** | Entry points | **Both:** View Browser **Add Diagram** (after Filters) + `DIAGRAM-LIST+FIND-1` hover **Edit** / **Delete** / **Move**. |
| **Q5** | MCP write model | **`update_diagram_draft`** (patch, no ChangeSet) + **`save_diagram`** (commit). Not single-shot session propose. |
| **Q6** | ADE / Munin chat on diagram | **`CHAT-MUNIN-1`** scoped to active diagram patches **draft** only; user Save or `save_diagram` MCP to commit. |
| **Q7** | Implementation waves | **W20–W27** after W19 shipped — [`act-10-diagram-editor/INDEX.md`](act-10-diagram-editor/INDEX.md) |

---

## Approved target state

See [`diagram_editor_bpe-08_cr_8c0acdee.plan.md`](../../.cursor/plans/diagram_editor_bpe-08_cr_8c0acdee.plan.md) (plan reference; do not edit during BPE-01) and updated artifacts:

- [`docs/features/user_journey.md`](../features/user_journey.md) — Act 2 Add Diagram; Act 10 diagram screens; MCP table
- [`docs/features/act-10-metamodel/diagram-*.feature`](../features/act-10-metamodel/)
- [`docs/features/act-8-mcp/diagram-mcp.feature`](../features/act-8-mcp/diagram-mcp.feature)
- [`docs/ux/IA_guidelines.md`](../ux/IA_guidelines.md) — § Diagram editor
- [`docs/plans/IDEA_DIAGRAM_JSON_PRESENTATION_FORMAT.md`](IDEA_DIAGRAM_JSON_PRESENTATION_FORMAT.md) — Phase 1 revised
- [`docs/architecture/SAO.md`](../architecture/SAO.md) — diagram draft + MCP tools
- [`docs/architecture/API_MCP_RECONCILIATION.md`](../architecture/API_MCP_RECONCILIATION.md) — diagram rows
- Mockups: [`src/yggdrasil/web/templates/mockups/diagram/`](../../src/yggdrasil/web/templates/mockups/diagram/)

### Draft model (summary)

| State | Storage | Commit path |
|-------|---------|-------------|
| Draft | `DiagramDraft.draft_data` (spec) per user/model/diagram | PATCH auto-save |
| Committed | `Diagram.layout_data` + M2M membership | `save_diagram` → Munin → ChangeSet |

### New ChangeSet ops (spec)

`create_diagram`, `update_diagram`, `delete_diagram`, `update_diagram_presentation` (+ existing `add_element`, `add_relationship`, `add_to_diagram` on save batch).

### Out of scope (this CR)

Gaphor plugin; Mermaid/PNG export from curated diagram; Metamodel catalog entity for diagram kinds (DTA); production `diagram_service` implementation.

---

## Spec diffs applied

| File | Change |
|------|--------|
| `user_journey.md` | Act 2 Add Diagram; diagram screen sections; MCP tools |
| `diagram-list.feature` | Hover actions; Draft pill; Edit replaces Open-in-Editor |
| `diagram-editor.feature` | New — create/edit/draft/save/discard |
| `diagram-delete.feature` | New — delete modal |
| `diagram-move.feature` | New — move package modal |
| `diagram-mcp.feature` | New — draft/save MCP scenarios |
| `IA_guidelines.md` | Diagram editor organism |
| `screen-flow.md` | Screen IDs + navigation |
| `conventions.md` | Screen ID examples |
| `CATALOG.md` | testids |
| `IDEA_DIAGRAM_JSON_PRESENTATION_FORMAT.md` | Phase 1 alignment |
| `SAO.md` | MCP + REST diagram tools |
| `API_MCP_RECONCILIATION.md` | New parity rows |
| `act-2-view-browser/INDEX.md` | W20–W27 rows |
| `act-10-diagram-editor/INDEX.md` | New wave index |
| Mockups | list + editor templates; mockup routes |

---

## Architectural notes

1. **`Diagram.diagram_type`** is metamodel-scoped — intentional; ORM hard-codes C4 `TYPE_CHOICES` until DTA catalog entity.
2. **Draft vs ChangeSet** — only Save invokes Munin; chat/MCP use `update_diagram_draft`.
3. **Delete diagram** — removes presentation + Diagram row; graph Elements/Relationships remain unless deleted in editor session.
4. **`add_to_diagram` rollback** — inverse map broken in as-built; fix in W24.

---

## Approval gate

- [x] Change Reconciliation Document saved at `docs/plans/DIAGRAM_EDITOR_CHANGE_RECONCILIATION.md`
- [x] In-place spec revisions complete
- [ ] User sign-off before BPE-01 W20 (human gate)

**No production code in BPE-08.**
