# Act 10 Diagram Editor — Plan Index

**Feature:** `DIAGRAM-EDITOR-1`, `DIAGRAM-LIST+FIND-1`, related screens
**Prerequisite:** [`DIAGRAM_EDITOR_CHANGE_RECONCILIATION.md`](../DIAGRAM_EDITOR_CHANGE_RECONCILIATION.md) (BPE-08 approved 2026-08-19)
**Idea doc:** [`IDEA_DIAGRAM_JSON_PRESENTATION_FORMAT.md`](../IDEA_DIAGRAM_JSON_PRESENTATION_FORMAT.md)
**Global wave sequence:** Continues from [`act-2-view-browser/INDEX.md`](../act-2-view-browser/INDEX.md) after **W19 shipped**

## Feature file map

| File | Scenarios | Component |
|------|-----------|-----------|
| [`diagram-list.feature`](../../features/act-10-metamodel/diagram-list.feature) | 01–08 | List, Draft pill, hover actions |
| [`diagram-editor.feature`](../../features/act-10-metamodel/diagram-editor.feature) | 01–08 | Create/Edit, draft, Save/Discard |
| [`diagram-delete.feature`](../../features/act-10-metamodel/diagram-delete.feature) | 01–03 | Delete modal |
| [`diagram-move.feature`](../../features/act-10-metamodel/diagram-move.feature) | 01–03 | Move package modal |
| [`diagram-mcp.feature`](../../features/act-8-mcp/diagram-mcp.feature) | 01–08 | MCP draft/save parity |

## Wave order (W20–W27)

| Wave | Deliverable | Screens / scenarios | Depends on |
|------|-------------|---------------------|------------|
| **W20** | Presentation JSON schema (Pydantic) + `DiagramDraft` spec + mockups | Mockup validation | BPE-08 CR approved |
| **W21** | `VIEW-BROWSE-1` **Add Diagram** + `DIAGRAM-CREATE_DIAGRAM-1` + editor Create mode | Act 2 toolbar; diagram-editor.feature (create) | W20 |
| **W22** | Server draft store + auto-save PATCH + **Draft** pill + Edit loads draft/committed | diagram-list.feature (draft badge); diagram-editor.feature (edit) | W21 |
| **W23** | Canvas editing — grabify, tree drag, Tools palette, `+` relationship | diagram-editor.feature (palette, drag) | W22 |
| **W24** | ChangeSet ops + Munin **`save_diagram`** commit path | diagram-editor.feature (save/discard); changeset integration | W23 |
| **W25** | `DIAGRAM-LIST+FIND-1` production list + hover **Edit / Delete / Move** | diagram-list/delete/move.feature | W24 |
| **W26** | MCP draft/save/read tools + REST parity | diagram-mcp.feature; API_MCP_RECONCILIATION | W24 |
| **W27** | `CHAT-MUNIN-1` scoped to active diagram — chat patches draft | Act 8 diagram context | W26 |

## Mockup reference

| Template | Screen |
|----------|--------|
| [`mockups/diagram/list.html`](../../../src/yggdrasil/web/templates/mockups/diagram/list.html) | `DIAGRAM-LIST+FIND-1`, delete/move modals |
| [`mockups/diagram/editor.html`](../../../src/yggdrasil/web/templates/mockups/diagram/editor.html) | `DIAGRAM-EDITOR-1`, create modal shell |
| [`mockups/view/browse.html`](../../../src/yggdrasil/web/templates/mockups/view/browse.html) | `VIEW-BROWSE-1` **Add Diagram** button |

## Change request (BPE-08 approved 2026-08-19)

Cytoscape diagram editor — draft-first editing, Munin on Save, View Browser entry, MCP two-phase API. Spec: [`DIAGRAM_EDITOR_CHANGE_RECONCILIATION.md`](../DIAGRAM_EDITOR_CHANGE_RECONCILIATION.md). **W20+ blocked until human sign-off on CR.**
