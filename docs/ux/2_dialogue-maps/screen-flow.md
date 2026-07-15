# Yggdrasil — Dialogue Maps (Screen Flows)

Source of truth for screen IDs and navigation. All screen IDs follow the convention:
`{ENTITY}-{OPERATION}-{VERSION}` (see `docs/conventions.md`).

---

## Diagram 1 — Domain Model

Core entities, their properties, and relationships. C4 metamodel is the only supported
metamodel in MVP; Elena governs metamodel evolution in Part II.

```mermaid
---
title: Yggdrasil Domain Model
---
erDiagram
    MODEL {
        string  name
        string  metamodel   "c4 only in MVP"
        enum    mode        "auto | manual"
    }
    ELEMENT {
        string  name
        string  stereotype
        string  package
        jsonb   properties  "driven by stereotype schema"
        string  owner
        float   confidence
        enum    health
        enum    source      "ratatosk | human | mcp"
    }
    RELATIONSHIP {
        string  edge_stereotype
        jsonb   properties
        float   confidence
        enum    source      "ratatosk | human | mcp"
    }
    STEREOTYPE {
        string  name
        jsonb   property_schema
        jsonb   allowed_edge_rules
    }
    PACKAGE {
        string  name
        string  slug        "Context | Container | Component | Code"
    }
    DIAGRAM {
        string  name
        enum    type        "Context | Container | Component | Code"
    }
    CHANGESET {
        enum    source      "ratatosk | human | mcp | rollback"
        enum    status      "pending | applied | rolled_back | rejected"
        text    munin_reasoning
    }
    CHANGESET_OPERATION {
        enum    op          "add_element | update_element | delete_element | add_relationship | update_relationship | delete_relationship | add_to_diagram"
        jsonb   detail
        enum    status      "pending | accepted | rejected"
    }
    MUNIN_RULE {
        string  rule_text
        string  contributed_by
        int     source_changeset_item
        datetime created_at
    }
    RATATOSK_RUN {
        string  trigger
        enum    status      "running | complete | failed"
        text    extraction_log
        jsonb   blackboard  "intent task-list; survives crashes"
    }
    USER {
        string  email
    }
    TOKEN {
        string  name
        enum    scope       "read_only | read_write"
    }

    MODEL       ||--o{  ELEMENT             : "contains"
    MODEL       ||--o{  RELATIONSHIP        : "contains"
    MODEL       ||--o{  STEREOTYPE          : "defines"
    MODEL       ||--o{  PACKAGE             : "organises"
    MODEL       ||--o{  DIAGRAM             : "has"
    MODEL       ||--o{  CHANGESET           : "tracks"
    MODEL       ||--o{  MUNIN_RULE          : "LEARNED"
    ELEMENT     }o--o{  DIAGRAM             : "placed in"
    ELEMENT     }|--||  STEREOTYPE          : "typed by"
    ELEMENT     }|--||  PACKAGE             : "scoped to"
    RELATIONSHIP    }|--||  ELEMENT         : "from"
    RELATIONSHIP    }|--||  ELEMENT         : "to"
    RELATIONSHIP    }|--||  STEREOTYPE      : "typed by"
    CHANGESET   ||--o{  CHANGESET_OPERATION : "plans"
    CHANGESET   }o--o|  RATATOSK_RUN        : "produced by"
    CHANGESET   ||--o{  MUNIN_RULE          : "may produce"
    USER        ||--o{  TOKEN               : "owns"
```

---

## Diagram 2 — Act Flow Overview

High-level: what each Act does and how Acts hand off to each other.
No individual screens — just the story arc.

```mermaid
---
title: Yggdrasil — Act Flow Overview (MVP)
---
flowchart TD
    classDef auth   fill:#4682B4,color:#fff,stroke:#2c5282
    classDef browse fill:#82b366,color:#000,stroke:#5a7d46
    classDef crud   fill:#d79b00,color:#fff,stroke:#9e6c00
    classDef ai     fill:#9673a6,color:#fff,stroke:#6b4e7a
    classDef nogui  fill:#888,color:#fff,stroke:#555,stroke-dasharray:5 5

    A0["**Act 0**\nAuth & API Access\n─────────────────\nAUTH-LOGIN-1\nAUTH-TOKEN-1"]
    A1["**Act 1**\nRatatosk Bootstrap\n─────────────────\n⌨ CLI only\nMUNIN-BRIEFING-1"]
    A2["**Act 2**\nView Browser\n─────────────────\nVIEW-BROWSE-1\nEXPORT-BRIEFING-1\nVIEW-HISTORY-1"]
    A3["**Act 3**\nElements CRUDLF\n─────────────────\nELEMENT-LIST+FIND-1\n+ VIEW / CREATE / EDIT / DELETE"]
    A4["**Act 4**\nRelationships CRUDLF\n─────────────────\nRELATIONSHIP-LIST+FIND-1\n+ VIEW / CREATE / EDIT / DELETE"]
    A5[/"**Act 5**\nMCP Browse\n─────────────────\nGUI-free\nCursor · Claude Desktop · scripts"/]
    A6[/"**Act 6**\nCI/CD Maintenance\n─────────────────\nGUI-free\nratatosk update"/]
    A7["**Act 7**\nChange Review\n─────────────────\nCHANGESET-LIST+FIND-1\nCHANGESET-VIEW_CHANGESET-1"]
    A8["**Act 8**\nChat with Munin\n─────────────────\nCHAT-MUNIN-1\n(panel in View Browser)"]
    A9["**Act 9**\nRun History\n─────────────────\nRATATOSK_RUN-LIST+FIND-1\nRATATOSK_RUN-VIEW_RATATOSK_RUN-1"]
    A10["**Act 10** *(Part II)*\nMetamodel Governance\n─────────────────\nSTEREOTYPE / PACKAGE / DIAGRAM\nLIST+FIND screens"]

    A0  ==>|"login → dashboard"| A2
    A0  -->|"generate token"| A1
    A0  -->|"generate token"| A5
    A1  ==>|"run complete → briefing"| A7
    A1  -->|"explore graph"| A2
    A2  -->|"nav: Elements"| A3
    A2  -->|"nav: Relationships"| A4
    A2  -->|"nav: ChangeSets"| A7
    A2  -->|"nav: Runs"| A9
    A2  <-->|"embedded panel"| A8
    A3  ==>|"write → Munin pipeline"| A7
    A4  ==>|"write → Munin pipeline"| A7
    A5  -->|"approve / reject changeset"| A7
    A6  ==>|"run complete → briefing"| A7
    A7  -->|"view run"| A9
    A8  -->|"drives view"| A2
    A8  -->|"pre-fill form"| A3

    class A0 auth
    class A2 browse
    class A3,A4,A7,A9,A10 crud
    class A1,A8 ai
    class A5,A6 nogui
```

---

## Diagram 3 — Navigation Hub

VIEW-BROWSE-1 is the central hub after login. Shows all entry-point screens reachable
from global nav and their internal CRUDLF sub-screens.

```mermaid
---
title: Yggdrasil — Navigation Hub (screen-level)
---
flowchart LR
    classDef auth       fill:#4682B4,color:#fff,stroke:#2c5282
    classDef browse     fill:#82b366,color:#000,stroke:#5a7d46
    classDef crud       fill:#d79b00,color:#fff,stroke:#9e6c00
    classDef ai         fill:#9673a6,color:#fff,stroke:#6b4e7a
    classDef nogui      fill:#888,color:#fff,stroke:#555,stroke-dasharray:5 5
    classDef listentry  stroke:#111,stroke-width:4px

    %% ── Auth ────────────────────────────────────────────────────
    LOGIN["AUTH-LOGIN-1"]
    TOKEN["AUTH-TOKEN-1"]
    LOGIN -->|"Settings"| TOKEN

    %% ── Central hub ─────────────────────────────────────────────
    BROWSE["VIEW-BROWSE-1\n🔍 View Browser"]

    LOGIN ==>|"success"| BROWSE

    %% ── Browse sub-screens ───────────────────────────────────────
    BROWSE --> EXPORT["EXPORT-BRIEFING-1\nExport Modal"]
    BROWSE --> HISTORY["VIEW-HISTORY-1\nModel History"]
    HISTORY -->|"open snapshot"| BROWSE

    %% ── Munin panel (embedded) ───────────────────────────────────
    BROWSE <-->|"panel"| MUNIN["CHAT-MUNIN-1\nMunin Chat"]

    %% ── Elements ─────────────────────────────────────────────────
    BROWSE -->|"nav"| EL_LIST["ELEMENT-LIST+FIND-1"]
    EL_LIST --> EL_VIEW["ELEMENT-VIEW_ELEMENT-1"]
    EL_LIST --> EL_CREATE["ELEMENT-CREATE_ELEMENT-1"]
    EL_LIST --> EL_EDIT["ELEMENT-EDIT_ELEMENT-1"]
    EL_LIST --> EL_DEL["ELEMENT-DELETE_ELEMENT-1"]
    EL_VIEW --> EL_EDIT

    %% ── Relationships ────────────────────────────────────────────
    BROWSE -->|"nav"| REL_LIST["RELATIONSHIP-LIST+FIND-1"]
    REL_LIST --> REL_VIEW["RELATIONSHIP-VIEW_RELATIONSHIP-1"]
    REL_LIST --> REL_CREATE["RELATIONSHIP-CREATE_RELATIONSHIP-1"]
    REL_LIST --> REL_EDIT["RELATIONSHIP-EDIT_RELATIONSHIP-1"]
    REL_LIST --> REL_DEL["RELATIONSHIP-DELETE_RELATIONSHIP-1"]
    REL_VIEW --> REL_EDIT

    %% ── ChangeSets ───────────────────────────────────────────────
    BROWSE -->|"nav"| CS_LIST["CHANGESET-LIST+FIND-1"]
    CS_LIST --> CS_VIEW["CHANGESET-VIEW_CHANGESET-1\n[Accept][Reject][Do Other]"]

    %% ── Runs ─────────────────────────────────────────────────────
    BROWSE -->|"nav"| RUN_LIST["RATATOSK_RUN-LIST+FIND-1"]
    RUN_LIST --> RUN_VIEW["RATATOSK_RUN-VIEW_RATATOSK_RUN-1"]

    %% ── Munin drives surrounding screen ─────────────────────────
    MUNIN -->|"navigate"| EL_VIEW
    MUNIN -->|"pre-fill"| EL_CREATE

    %% ── Class assignments ────────────────────────────────────────
    class LOGIN,TOKEN                                       auth
    class BROWSE,EXPORT,HISTORY                             browse
    class EL_LIST,EL_VIEW,EL_CREATE,EL_EDIT,EL_DEL         crud
    class REL_LIST,REL_VIEW,REL_CREATE,REL_EDIT,REL_DEL    crud
    class CS_LIST,CS_VIEW,RUN_LIST,RUN_VIEW                 crud
    class MUNIN                                             ai

    class EL_LIST,REL_LIST,CS_LIST,RUN_LIST                 listentry
```

---

## Diagram 4 — Write Pipeline

Every write — from any source — flows through the Munin pipeline and lands in a ChangeSet.
The ChangeSet mode (Auto / Manual) determines whether it applies immediately or queues for review.

```mermaid
---
title: Yggdrasil — Write Pipeline (all sources → ChangeSet)
---
flowchart TD
    classDef source fill:#4682B4,color:#fff,stroke:#2c5282
    classDef munin  fill:#9673a6,color:#fff,stroke:#6b4e7a
    classDef cs     fill:#d79b00,color:#fff,stroke:#9e6c00
    classDef model  fill:#82b366,color:#000,stroke:#5a7d46
    classDef nogui  fill:#888,color:#fff,stroke:#555,stroke-dasharray:5 5

    %% ── Write sources ────────────────────────────────────────────
    CLI[/"⌨ ratatosk bootstrap / update\n(CLI — Act 1 & Act 6)"/]
    GUI["🖱 Human GUI form\n(Act 3 & Act 4)"]
    MCP[/"🔌 MCP tool call\ncreate / update / delete\n(Act 5)"/]

    %% ── Munin pipeline ───────────────────────────────────────────
    PIPELINE["Munin Pipeline\n────────────────────\n1. Validate inputs\n2. Check metamodel rules\n3. Compute blast-radius\n4. Plan graph operations\n5. Classify confidence"]

    %% ── ChangeSet ────────────────────────────────────────────────
    CS["CHANGESET-VIEW_CHANGESET-1\n────────────────────\nList of planned operations\n[Accept] [Reject] [Do Other]"]

    %% ── Mode fork ────────────────────────────────────────────────
    AUTO{"Model mode?"}
    APPLY["Apply directly to Model\n(audit trail kept)"]
    QUEUE["Queue for human review\nCHANGESET-LIST+FIND-1"]

    %% ── Graph ────────────────────────────────────────────────────
    MODEL_DB[("Live Model\n(Elements + Relationships)")]

    %% ── LEARNED feedback loop ────────────────────────────────────
    LEARNED[["LEARNED component\n(MuninRules — append-only)\nprepended to Munin prompt\non next run"]]

    CLI     --> PIPELINE
    GUI     --> PIPELINE
    MCP     --> PIPELINE

    PIPELINE ==> CS
    CS       --> AUTO

    AUTO -->|"Auto-approval"| APPLY
    AUTO -->|"Manual-review"| QUEUE
    QUEUE -->|"human approves"| APPLY
    QUEUE -->|"[Do Other] → correction"| LEARNED
    LEARNED -->|"prepended next run"| PIPELINE

    APPLY ==> MODEL_DB
    APPLY -->|"rollback available"| CS

    class CLI,MCP       nogui
    class GUI           source
    class PIPELINE,LEARNED  munin
    class CS,QUEUE      cs
    class AUTO          cs
    class APPLY,MODEL_DB    model
```

---

## Screen ID Index

| Screen ID | Act | Description |
|---|---|---|
| `AUTH-LOGIN-1` | 0 | Login form |
| `AUTH-TOKEN-1` | 0 | API token management |
| `MUNIN-BRIEFING-1` | 1 | Post-run architectural briefing |
| `VIEW-BROWSE-1` | 2 | View Browser with filters + graph/table toggle |
| `EXPORT-BRIEFING-1` | 2 | Export modal (Mermaid / Markdown deck / JSON) |
| `VIEW-HISTORY-1` | 2 | Model history timeline and A/B diff |
| `ELEMENT-LIST+FIND-1` | 3 | Elements list & search (LIST+FIND entry point) |
| `ELEMENT-VIEW_ELEMENT-1` | 3 | Element detail (properties, ego-graph) |
| `ELEMENT-CREATE_ELEMENT-1` | 3 | Create element form |
| `ELEMENT-EDIT_ELEMENT-1` | 3 | Edit element form |
| `ELEMENT-DELETE_ELEMENT-1` | 3 | Delete confirmation with blast-radius |
| `RELATIONSHIP-LIST+FIND-1` | 4 | Relationships list & search (LIST+FIND entry point) |
| `RELATIONSHIP-VIEW_RELATIONSHIP-1` | 4 | Relationship detail |
| `RELATIONSHIP-CREATE_RELATIONSHIP-1` | 4 | Create relationship form |
| `RELATIONSHIP-EDIT_RELATIONSHIP-1` | 4 | Edit relationship form |
| `RELATIONSHIP-DELETE_RELATIONSHIP-1` | 4 | Delete confirmation |
| `CHANGESET-LIST+FIND-1` | 7 | ChangeSet queue (LIST+FIND entry point) |
| `CHANGESET-VIEW_CHANGESET-1` | 7 | ChangeSet review with Accept / Reject / Do Other |
| `CHAT-MUNIN-1` | 8 | Munin chat panel (embedded in VIEW-BROWSE-1) |
| `RATATOSK_RUN-LIST+FIND-1` | 9 | Run list (LIST+FIND entry point) |
| `RATATOSK_RUN-VIEW_RATATOSK_RUN-1` | 9 | Run detail (extraction log + Munin blackboard) |
| `STEREOTYPE-LIST+FIND-1` | 10 | Stereotype definitions (Part II) |
| `PACKAGE-LIST+FIND-1` | 10 | Package hierarchy (Part II) |
| `DIAGRAM-LIST+FIND-1` | 10 | Diagram list with graph editor (Part II) |
