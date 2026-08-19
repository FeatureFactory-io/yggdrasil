# IDEA: Yggdrasil Diagram JSON — Presentation Format & Editor Path

**Status:** Idea / pre-plan
**Created:** 2026-08-19
**Related:** `Diagram` model (`graph.models`), `DIAGRAM-LIST+FIND-1` (Part II), `EXPORT-BRIEFING-1`, PRD Phase 1 convention

---

## Intent

Yggdrasil follows the Sparx Enterprise Architect pattern: **Elements and Relationships are the canonical model**; **Diagrams are curated views** that describe how to *paint* that model — not duplicate it.

A Diagram answers:

- **Which** Elements and Relationships appear on this view (membership)
- **How** they are shown (presentation): position, size, visibility, color, line style (dashed/dotted/bold), edge routing, diagram-only notes

We do **not** store element definitions (name, stereotype, properties) as authoritative data inside the diagram document. Those live in `Element` / `Relationship` and are referenced by ID.

**One-sentence rule:** *Diagram JSON references the graph; it does not replace the graph.*

---

## Relationship to existing code

| Today | Target |
|---|---|
| `Diagram.layout_data` (JSONB) — Cytoscape positions only | Evolve to full **presentation document** (`presentation_data` or extended `layout_data`) |
| `Element.diagrams` M2M — membership | Complement with explicit relationship visibility in JSON |
| View Browser (Cytoscape) — exploratory subgraph | Separate product surface: filtered BFS, not curated diagram |
| `add_to_diagram` ChangeSet op | Stays; presentation edits also go through ChangeSet |
| Mermaid export (View Browser / briefings) | Derived export from diagram JSON + live graph |

---

## Yggdrasil Diagram JSON (v1 sketch)

Stored on `Diagram` (JSONB). Versioned schema.

```json
{
  "version": 1,
  "diagram_id": 42,
  "membership": {
    "element_ids": [101, 102, 103],
    "relationships": [
      { "relationship_id": 55, "visible": true },
      { "relationship_id": 56, "visible": false }
    ]
  },
  "presentation": {
    "nodes": [
      {
        "element_id": 101,
        "x": 120,
        "y": 80,
        "width": 140,
        "height": 60,
        "style": {
          "border_color": "#198754",
          "background_color": "#e7eef7",
          "shape": "round-rectangle"
        },
        "label_override": null
      }
    ],
    "edges": [
      {
        "relationship_id": 55,
        "visible": true,
        "waypoints": [[200, 100], [300, 150]],
        "style": {
          "line_style": "dashed",
          "line_color": "#5a6478",
          "width": 2
        }
      }
    ],
    "annotations": [
      {
        "id": "note-1",
        "type": "note",
        "x": 400,
        "y": 50,
        "width": 180,
        "height": 80,
        "text": "External — out of scope"
      }
    ]
  },
  "extensions": {
    "gaphor": {}
  }
}
```

### Field ownership

| Section | Purpose | Canonical? |
|---|---|---|
| `membership.element_ids` | Which elements appear | IDs only → graph |
| `membership.relationships[].visible` | Show/hide edges on this diagram | Diagram |
| `presentation.nodes` | Layout + per-diagram node styling | Diagram |
| `presentation.edges` | Routing + per-diagram edge styling | Diagram |
| `presentation.annotations` | Notes, boundaries — diagram-only, not Elements | Diagram |
| `extensions.*` | Tool-specific fields with no Cytoscape equivalent | Diagram (lossy across editors) |

Element names, stereotypes, and properties are **always** resolved from the graph at render time (optional read-only cache allowed for offline external editors).

---

## Architecture: hub + spokes

```
                    ┌─────────────────────────────┐
                    │  Yggdrasil Diagram JSON     │
                    │  (canonical presentation)   │
                    └──────────────┬──────────────┘
                                   │
           ┌───────────────────────┼───────────────────────┐
           │                       │                       │
           ▼                       ▼                       ▼
   ┌───────────────┐      ┌─────────────────┐     ┌──────────────────┐
   │  Cytoscape    │      │  Export adapters │     │  Gaphor plugin   │
   │  in-app editor│      │  (derived)       │     │  (adapter)       │
   └───────────────┘      └─────────────────┘     └──────────────────┘
                          Mermaid / PlantUML
                          PNG / SVG
                          Markdown deck
```

- **Hub:** Yggdrasil Diagram JSON in Postgres
- **In-app:** Cytoscape reads/writes presentation natively (no intermediate format)
- **External:** Gaphor plugin converts to/from Gaphor subjects + presentations
- **Export:** One-way generators for decks and docs (Mermaid already planned for View Browser; diagram export adds layout-faithful PNG/SVG)

### View Browser vs Diagram

| | View Browser | Diagram |
|---|---|---|
| Purpose | Explore filtered subgraph | Curated, shareable view |
| Layout | Auto (`cose`) | Saved positions (`preset`) |
| Scope | Filter + depth | Explicit membership |
| Editor | Read-only explore | Draft-first curated editor (`DIAGRAM-EDITOR-1`) |

---

## Implementation path (phased)

### Phase 1 — Schema + Cytoscape editor (Part II)

**Screens:** `VIEW-BROWSE-1` (**Add Diagram**), `DIAGRAM-CREATE_DIAGRAM-1`, `DIAGRAM-EDITOR-1`, `DIAGRAM-LIST+FIND-1` (inventory + hover Edit/Delete/Move)

**Entry points:**

1. View Browser canvas toolbar **[Add Diagram]** → create modal → empty editor (Create mode)
2. Diagram list hover **Edit** → editor loads draft if present else committed (Edit mode)

**Draft-first editing:**

- GUI canvas, model-tree drag, Tools palette, on-canvas **`+`**, MCP `update_diagram_draft`, and diagram-scoped `CHAT-MUNIN-1` all patch a **server-side draft** — not the canonical graph
- **Save** (editor button or MCP `save_diagram`) → Munin → ChangeSet → committed `Diagram.layout_data` + graph ops
- **Discard** drops draft only

**Implementation steps:**

1. Define presentation v1 schema (Pydantic); evolve `Diagram.layout_data`; add `DiagramDraft.draft_data` (spec)
2. REST/MCP: `get_diagram` (committed), `get_diagram_draft`, `update_diagram_draft`, `save_diagram`, `discard_diagram_draft`, `list_diagrams` (`has_draft`)
3. Cytoscape editor (`DIAGRAM-EDITOR-1`):
   - Three-panel layout (model tree · canvas · Tools palette)
   - `layout: preset` from saved positions; grabbable nodes
   - Relationship show/hide per diagram; on-canvas relationship draw
   - **Draft** pill on list + header when committed diagram has unsaved draft
4. Munin on Save: enrich `Diagram.summary` and `Diagram.tags` for inventory queries
5. ChangeSet ops: `create_diagram`, `update_diagram`, `delete_diagram`, `update_diagram_presentation`, plus `add_element`, `add_relationship`, `add_to_diagram`

**Deliverable:** Curated in-app diagrams with draft/staging and Munin commit path — no external editor required.

### Phase 2 — Export from curated diagrams

1. Diagram JSON + graph → **Mermaid C4** (structure; auto-layout)
2. Diagram JSON + Cytoscape → **PNG/SVG** (layout-faithful slides)
3. Optional: PlantUML C4 export
4. Wire into export UI alongside existing `EXPORT-BRIEFING-1` patterns

**Deliverable:** Deck-ready artifacts that respect saved layout where it matters.

### Phase 3 — Gaphor plugin (optional power editor)

**Package:** `yggdrasil-gaphor-plugin` (pip) + shared `yggdrasil-diagram` schema package

**Open flow:**

1. User: Open diagram from Yggdrasil (by ID)
2. Fetch Diagram JSON + referenced Elements/Relationships (API/MCP)
3. Converter: `element_id` → Gaphor subject (proxy); presentation → Gaphor items

**Save flow:**

1. Presentation diff → update Diagram JSON (via API)
2. Entity diff (new/changed elements or relationships in Gaphor) → **ChangeSet ops** (`add_element`, `update_element`, `add_relationship`, `add_to_diagram`, etc.) — never blind merge into JSON

**Why Gaphor:** Python stack, C4 modeling language, `ModelingLanguage` + plugin entry points; shared client/schema code with Yggdrasil backend.

**Why not Gaphor file as storage:** Model/presentation bundled in `.gaphor` conflicts with Yggdrasil owning the graph; web app cannot embed GTK.

### Phase 4 — Munin integration (existing direction)

- Diagram placement hints on element create (`diagram_hints`)
- Auto-suggest membership and initial layout
- LEARNED rules for diagram conventions (“Code diagram is for repo structure…”)

---

## Guardrails

1. **Diagram JSON never owns canonical element definitions** — IDs + presentation only.
2. **All entity writes go through ChangeSet** — Cytoscape, Gaphor, GUI, MCP, Munin.
3. **Gaphor subjects are proxies** — carry `yggdrasil_element_id`; property edits sync as ChangeSet items.
4. **Stale/conflict detection** — element deleted while external editor open → surface conflict on sync.
5. **Lossy fields** — tool-specific styling in `extensions.gaphor` (or similar); document Cytoscape vs Gaphor parity gaps.
6. **Do not use PlantUML/Mermaid as storage** — export channels only; they cannot preserve manual layout.

---

## Shared code (Python)

| Module | Consumers |
|---|---|
| `yggdrasil.diagram.schema` | Django services, API serializers, tests |
| `yggdrasil.diagram.cytoscape` | Server-side cytoscape payload builder |
| `yggdrasil.diagram.export` | Mermaid / PNG generators |
| `yggdrasil.diagram.gaphor` | Gaphor plugin adapter (Phase 3) |

Cytoscape JS in the browser mirrors schema rules for read/write; single source of truth for field names and semantics is the Python Pydantic models.

---

## Out of scope (this idea doc)

- Full `presentation_data` JSON Schema / OpenAPI spec
- ChangeSet op types for `update_diagram_presentation`
- Draw.io adapter (alternative external editor; same hub JSON)
- Detailed Gaphor ModelingLanguage class design
- Acceptance tests and iteration manifest entries

---

## Success criteria (when implemented)

- [ ] Architect opens Container Diagram, drags nodes, saves — layout persists across sessions
- [ ] Relationship hidden on diagram A still visible on diagram B
- [ ] Per-diagram edge dashed/bold styling renders in Cytoscape
- [ ] Diagram-only annotation renders; not stored as Element
- [ ] Export produces Mermaid (structure) and PNG (layout) from same diagram
- [ ] Gaphor plugin round-trips presentation; entity changes arrive as ChangeSet ops
- [ ] No duplicate element definitions inside Diagram JSON

---

## References

- `src/yggdrasil/graph/models.py` — `Diagram`, `layout_data`, Element M2M
- `docs/features/act-10-metamodel/diagram-list.feature`
- `docs/features/user_journey.md` — Act 10, EXPORT-BRIEFING-1
- `docs/ux/IA_guidelines.md` — §8.2 Cytoscape, `DIAGRAM-LIST+FIND-1`
- `PRD.MD` — Phase 1 convention (Element + Relation + Package + Diagram)
- [Gaphor modeling language docs](https://docs.gaphor.org/en/latest/modeling_language.html)
- [Gaphor plugins](https://docs.gaphor.org/en/latest/plugins.html)
