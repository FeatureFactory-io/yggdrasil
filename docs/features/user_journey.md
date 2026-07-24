# Yggdrasil User Journey (ESM-02)

Personas from [PRD.MD](../../PRD.MD). Primary actors: **Priya** (Software Architect), **Marcus** (Development Team Lead), **Elena** (Enterprise Architect), **Alex** (Platform / Nerve-Ring Lead). Priya and Marcus are the wedge's primary users (Part I); Elena governs the metamodel once the Model matures (Part II).

---

## Part I — MVP (The Wedge)

**Scope:** Connect a repo, bootstrap a Model, fully manage elements and relationships via GUI, keep the model current from CI/CD, query it via any AI client, and ask Munin about it. See [PRD.MD](../../PRD.MD) "The wedge / 1st bet".

## Act 0: Authentication & API Access

**Context:** Any user opens Yggdrasil. Unauthenticated users see log,in; authenticated users land on the dashboard. Accounts are admin-provisioned (Groups/PBAC — Key Features 6/7), not self-registered. CLI (Ratatosk) and MCP clients authenticate with a personal access token instead of a session.

#### Screen: AUTH-LOGIN-1

Elena opens `https://yggdrasil.featurefactory.io`. Login form: email, password, [Sign in]. On success → `VIEW-BROWSE-1` (default landing).

#### Screen: AUTH-TOKEN-1

**Context:** Priya needs to run Ratatosk from her laptop and point Cursor's MCP client at Yggdrasil — both need a token, not a browser session.

Priya opens "Settings → API Access" from the user menu.

**Layout:**

- **Existing tokens:** table of Name | Created | Last used | Scope | [Revoke]
- **[Generate New Token]** → modal: name (e.g. "laptop-ratatosk"), scope (read-only / read-write), [Create] → token shown once, [Copy]
- **Usage snippets** (copy-paste ready):
  - Shell: `export YGGDRASIL_TOKEN=<token>`
  - Ratatosk CLI (install once, then use in any shell or CI pipeline):
    ```bash
    pip install ratatosk
    ratatosk bootstrap ./repo --token=<token>
    ```
  - MCP via Docker (recommended — MCP client starts the container on demand, token stays local):
    `mcp_config.json`:
    ```json
    {
      "mcpServers": {
        "yggdrasil": {
          "command": "docker",
          "args": [
            "run", "--rm", "-i",
            "-e", "YGGDRASIL_TOKEN=<token>",
            "-e", "YGGDRASIL_SERVER_URL=https://yggdrasil.featurefactory.io",
            "featurefactory-io/yggdrasil-mcp:latest"
          ]
        }
      }
    }
    ```
    The container authenticates against the Yggdrasil DRF API using `YGGDRASIL_TOKEN` and exposes MCP tools over stdio. No port mapping needed.
  - MCP direct (cloud — no Docker required):
    ```json
    {
      "mcpServers": {
        "yggdrasil": {
          "url": "https://yggdrasil.featurefactory.io/mcp/sse",
          "headers": { "Authorization": "Bearer <token>" }
        }
      }
    }
    ```

---



## Act 1: Ratatosk Bootstrap (CLI)

**Context:** Priya just generated a token (`AUTH-TOKEN-1`). She wants an initial Model built from the repo her team already ships from — no manual data entry. She can also give Ratatosk a focused instruction to guide its analysis beyond the generic NER pass.

**Pattern:** CLI-only in MVP — the GUI shows the result of a run, not its trigger (see System Notes).

```bash
$ export YGGDRASIL_TOKEN=<token>

# First bootstrap — empty model, full filesystem scan
$ ratatosk bootstrap ./repo --token=$YGGDRASIL_TOKEN --model Yggdrasil --metamodel=c4

[ratatosk] wiping 0 elements and 0 relationships on model Yggdrasil (bulk ChangeSet op; revertible)
[ratatosk] building ModelSummary (8000 token budget) via MCP …
[ratatosk] scanning ./repo …
[ratatosk] found 3 services, 12 modules, 4 external dependencies, 8 domain objects
[ratatosk] buckets (bootstrap — add-heavy):
             to_add: 27 element candidates
[munin]    reading candidates, planning graph operations …
[munin]    ChangeSet #4: 27 add-element ops, 18 add-relationship ops
                         2 ops below threshold → queued for review
[ratatosk] run complete — ChangeSet #4 pending
          → https://yggdrasil.featurefactory.io/runs/4

# Re-bootstrap — populated model: wipe then rescan (NOT delta merge)
$ ratatosk bootstrap ./repo --token=$YGGDRASIL_TOKEN --model Yggdrasil --metamodel=c4 \
    --instructions "Do an extra pass on the business logic layer — check whether any Domain objects have drifted out of sync with their model representations."

[ratatosk] wiping 31 elements and 44 relationships on model Yggdrasil (bulk ChangeSet op; revertible)
[ratatosk] building ModelSummary via MCP …
[ratatosk] scanning ./repo with instructions …
[ratatosk] found 3 services, 12 modules, 4 external dependencies, 8 domain objects
[ratatosk] buckets (bootstrap — post-wipe):
             to_add: 27 element candidates
[munin]    reading candidates, planning graph operations …
[munin]    ChangeSet #5: 27 add-element ops, 19 add-relationship ops
[ratatosk] run complete — ChangeSet #5 pending
          → https://yggdrasil.featurefactory.io/runs/5
```

C4 is the default — and only — Metamodel in MVP. It is a first-class type catalog (Stereotypes + Packages) established via Django admin / fixture seed — not invented by Ratatosk. Each Model is bound to a Metamodel at create time (immutable thereafter). Ratatosk takes `--metamodel=c4` as the slug for ontology guidance and populates Elements/Relationships under that catalog. There is no end-user metamodel picker yet; evolving metamodels beyond C4 is Key Feature 12, Part II.

**Pipeline (bootstrap vs update — different step 0 and gather behavior):**

| Step | `ratatosk bootstrap` | `ratatosk update` |
|------|----------------------|-------------------|
| 0 | **Wipe** all Elements + Relationships on Model (single bulk op; revertible) | — (graph preserved; **never wipe**) |
| 1 | Build **ModelSummary** (token budget) + MCP snapshot for reconcile | Same |
| 2 | Metamodel guidance (Stereotypes/Packages for bound Metamodel) | Same |
| 3 | Filesystem tree (paths only) | Stdin blob (diff, commit log, prose); size-capped |
| 4 | Map project kind → target paths | **Scout plan** — paths, issue keys, MCP probe intents |
| 5 | Read files → extract element candidates | Gather evidence (local `--repo` + Yggdrasil MCP + connector MCPs) → extract |
| 5b | **Synthesize** — D0 pre-filter + D1 Sonnet canonicalize (merges/rejects) | Same (update mode when candidates present) |
| 6 | Cleanup, dedupe, constrain to metamodel | Cleanup + **delta reconcile** (`to_add` / `to_update` / `to_delete`) |
| 7 | ChangeSet (add-heavy; `source=ratatosk`) | ChangeSet (delta; `unchanged` never sent) |

1. **Ratatosk** (field agent — element NER + provenance, small/fast/cheap LLM) runs the pipeline above. **Elements only** — Ratatosk never plans relationships. Elements are never written outside a ChangeSet.
2. **Munin** (ontology specialist) reads element candidates and plans the ChangeSet — including **relationships**, diagram placement, and metamodel validation. Pre-bucketed input means higher confidence and fewer items requiring human review.

#### Bootstrap wipe rule

Re-bootstrap is **not** update. Running `bootstrap` on a populated Model **bulk-wipes** all Elements and Relationships (Model + metamodel binding preserved), then rescans from the repo. There is no `unchanged` bucket from the prior graph — the wipe removes it. Revert via ChangeSet rollback or time-travel (`Act 8`).

#### ModelSummary

Ratatosk does **not** inject the full graph into LLM prompts. Before extract, it builds a **ModelSummary** under a token budget (default **8000 tokens**, config: `model_summary_token_budget`):

1. Serialize levels top-down: L0 totals → L1 package/stereotype rollups → L2 element names → L3+ detail if budget remains.
2. Stop when the next level would exceed remaining budget.
3. Append guidance: use MCP read tools (`list_elements`, `get_element`, `search`, `traverse`, `list_packages`) for deeper detail.

A full snapshot remains in code for reconcile (`by_slug`); only the summary text enters the prompt.

#### Prompt Stack (Ratatosk)

| Layer | Content |
|-------|---------|
| System | Role (field NER), pipeline handoff to Munin, precision-over-recall, no direct graph writes |
| User (metamodel) | `build_metamodel_guidance()` — Stereotypes, Packages, allowed element kinds from bound Metamodel |
| User (context) | ModelSummary + materialized input (file excerpt or scout evidence) + optional `--instructions` |
| Tools | Local file reads + Yggdrasil MCP read subset + connector MCPs per config allowlist |

Scout bounds (defaults, config-overridable): **10** rounds, **1000** file reads, **50** MCP calls per run.

Acceptance tests may drive the same pipeline in-process; certification uses subprocess `ratatosk bootstrap` + HTTP MCP against a running Yggdrasil server.

High-confidence operations apply directly to the Model; below-threshold operations queue for human review in `Act 7`.

Priya follows the printed link to `MUNIN-BRIEFING-1` — Munin's post-run architectural briefing — rather than raw extraction logs.

#### Screen: MUNIN-BRIEFING-1

**Context:** Lands immediately after a Ratatosk run (bootstrap or update). Replaces raw logs as the post-run landing page. Designed to orient both experienced architects and users who are new to model-driven architecture.

**Layout:**

- **Munin's Summary** (narrative paragraph, auto-generated):
  > "I analysed 3 services, 12 modules, and 4 external dependencies. The model now contains 16 elements and 24 relationships across the Technology package. 3 operations are awaiting your review — mainly around module-to-service ownership."
- **Confidence distribution:** pill badges — e.g. `✓ 37 auto-applied` · `⚠ 3 queued for review` · `○ 2 below threshold (skipped)`
- **Key findings:** ranked list of the most-connected elements, any detected naming conflicts, low-confidence items, and potential duplicates — each entry links to the relevant element or ChangeSet
- **Suggested next steps:**
  - [Review pending ChangeSet →] (`Act 7`)
  - [Explore the graph →] (`VIEW-BROWSE-1`)
  - [Run again with instructions →] (pre-fills CLI command)
- **Raw run log** (collapsed by default) — links to `RATATOSK_RUN-VIEW_RATATOSK_RUN-1` (`Act 9`) for full extraction detail

**First-time users — C4 Primer overlay:** on first login or first bootstrap, a dismissible overlay explains the C4 metamodel in plain language:

> **C4 in 60 seconds**
> Your model is organised in four levels: **Context** (your system and its users), **Container** (apps, databases, services), **Component** (internal building blocks), **Code** (classes, modules). Elements are the nodes; Relationships are the edges between them. Stereotypes label what a node or edge *is*. Packages group related elements into views. Munin maintains the structure — you provide the intent.
>
> [Got it — show me the graph →] [Learn more about C4 →]

---



## Act 2: View Browser — Explore the Graph

**Context:** Priya needs to see all Applications supporting Capability "Fulfill Orders" and their owners. This is the flagship "view browser" (Key Feature #2).

**Pattern:** Multi-level filter panel + results table/graph toggle.

#### Screen: VIEW-BROWSE-1

**Layout:**

- **Header:** "View Browser" with saved-views dropdown
- **Filter panel (top of the list; collapsible panel - when collapsed reads what filters applied):**
  - Package selector (Context, Container, Component, Code — from the C4 bootstrap)
  - Stereotype multi-select (Application, Capability, …)
  - **Advanced filter builder:** compound AND/OR rules over any element property (see below)
  - **Time Travel:** date picker (defaults to "now"); selecting a past date sets `?as_of=` in the URL and re-runs the query against the historical snapshot — a banner "Viewing model as of 2026-01-15" appears; [Compare with now →] opens `VIEW-HISTORY-1`
  - [Apply Filters] [Clear] [Save View]
- **Results (center, under filters):**
  - Table mode: columns Name, Stereotype, Owner, Health, Package
  - Graph mode: Cytoscape.js rendering of filtered subgraph
  - Toggle [Table] [Graph]
  - **Actions bar:** [Export →] (`EXPORT-BRIEFING-1`) [History →] (`VIEW-HISTORY-1`)
- **Detail drawer (right):** selected element summary + quick links to VIEW/EDIT
- **Munin panel:** collapsible chat side panel (`Act 8`) that can drive this same screen

**Advanced filter builder:** each row is a rule (field · operator · value); rows are joined with AND or OR; groups can be nested. Supported operators by property type:


| Property type     | Operators                                                          |
| ----------------- | ------------------------------------------------------------------ |
| Text              | contains, not contains, equals, not equals, starts with, ends with |
| Numeric           | = , ≠ , > , ≥ , < , ≤                                              |
| Boolean           | is true, is false                                                  |
| Enum / Stereotype | is one of, is not one of                                           |


Every filter state is encoded as a JSON query object appended to the URL — shareable, bookmarkable, and AI-constructable:

```
/views/technology/application?filter={"and":[{"field":"version","op":"gt","value":1},{"field":"name","op":"contains","value":"payment"}]}
```

**Semantic URL rules (filter encoding):**


| Concept                | URL key / value                                                                          |
| ---------------------- | ---------------------------------------------------------------------------------------- |
| AND group              | `{"and": [...rules]}`                                                                    |
| OR group               | `{"or": [...rules]}`                                                                     |
| Rule                   | `{"field": "<prop>", "op": "<operator>", "value": <scalar or array>}`                    |
| Operators              | `eq` `neq` `gt` `gte` `lt` `lte` `contains` `not_contains` `starts` `ends` `in` `not_in` |
| Package scope          | path segment: `/views/{package-slug}/`                                                   |
| Stereotype scope       | path segment: `/views/{package-slug}/{stereotype-slug}`                                  |
| Depth (traversal)      | `?depth=N`                                                                               |
| Time travel            | `?as_of=2026-06-01`                                                                      |
| Pre-filled create form | `/elements/new?prefill={"name":"X","stereotype":"Container","package":"technology"}`     |


Munin (`Act 8`) and any MCP client can construct these URLs from natural language without touching the GUI (Key Feature 1). The filter builder always reflects the current URL state — paste a URL, restore the exact view.

Priya selects Package "Technology", Stereotype "Application", adds rule `version > 1 AND name contains "payment"` — URL updates live; she copies it to Slack. Marcus clicks it and lands on the identical subgraph.

#### Screen: EXPORT-BRIEFING-1

**Context:** Priya needs to present the Payment System architecture to stakeholders next week. She has scoped the subgraph she wants, and now needs a shareable artifact — not a screenshot, a structured document with proper C4 diagrams.

**Trigger:** [Export →] button in the View Browser actions bar. Opens a modal or side panel.

**Export formats:**

| Format | Output | Use case |
|---|---|---|
| **Mermaid diagram** | `.md` file with fenced `mermaid` C4 block for the current subgraph | Embed in GitHub / GitLab wiki, Notion, any Markdown renderer |
| **Markdown deck** | Multi-section `.md`: executive summary (generated by Munin), one section per C4 level present in the subgraph, Mermaid diagrams inline | Presentation to stakeholders; renderable as slides with Marp or similar |
| **JSON** | Raw element + relationship data for the current filter scope | Scripting, further processing |

**Munin narrative toggle:** for Mermaid and Markdown deck exports, an optional "Ask Munin to annotate" checkbox — Munin generates a 2–3 sentence description per section explaining the architectural intent, not just the structure.

**Download:** [Export as Mermaid] [Export as Markdown Deck] [Export as JSON] — each triggers a file download. No server-side storage; exports are point-in-time snapshots.

Semantic URL for export: `/views/{package}/{stereotype}/export?format=mermaid&filter=...` — constructible by Munin in chat so a GUI-free user can generate a download link without opening the browser.

#### Screen: VIEW-HISTORY-1

**Context:** Elena wants to know what the Technology package looked like three months ago and what changed since. Priya wants a diff between the model before and after a major refactor.

**Layout:**

- **Header:** "Model History — {Model name}"
- **Timeline rail (left):** chronological list of ChangeSet apply events — date, source (Ratatosk / Munin / Human), number of operations, [View snapshot]
- **Snapshot A / Snapshot B pickers (top):** two date selectors; defaults to "last Ratatosk run" vs "now"; selecting either updates the diff panel
- **Diff panel (center):**
  - **Added** (green): elements and relationships that exist in B but not A
  - **Removed** (red): exist in A but not B
  - **Modified** (amber): exist in both, properties changed — expandable to show field-level diff
  - Each row links to the relevant element or ChangeSet
- **[Open Snapshot A in View Browser →]** and **[Open Snapshot B in View Browser →]:** navigates to `VIEW-BROWSE-1` with `?as_of=<date>` pre-set

Semantic URL: `/models/{model}/history?a=2026-01-01&b=2026-04-01` — constructible by Munin in chat.

---



## Act 3: Elements — Full CRUDLF

**Context:** Priya notices the bootstrap missed "Notification Service" (not yet in the codebase). She needs to add it to the Model, wire its relationships, and tell Munin which diagrams it belongs in. Marcus needs to correct a misclassified component. Full lifecycle — find, inspect, create, edit, delete — is available in the GUI without CLI or MCP access.

**Pattern:** Full CRUDLF with LIST+FIND as entry point. Human writes (Create, Edit, Delete) go through the Munin pipeline — same as Ratatosk — so graph integrity and audit trail are never bypassed.

#### Screen: ELEMENT-LIST+FIND-1

Priya clicks "Elements" in nav.

**Layout:**

- **Header:** "Elements" with count badge
- **Actions:** [Create Element]
- **Search:** "Find elements…" (name, stereotype, package)
- **Filters:** Stereotype, Package, Health, Source (Ratatosk / Munin / Human)
- **Table:** Name | Stereotype | Package | Owner | Health | Source | Actions
- **Row actions:** View, Edit, Delete
- **Empty state:** "No elements yet — run Ratatosk bootstrap or create manually"



#### Screen: ELEMENT-VIEW_ELEMENT-1

Detail page: structural properties (JSONB), behavioral links (incoming/outgoing relationships with their stereotypes), state panel (health, provenance, confidence, last verified), mini Cytoscape ego-graph.

#### Screen: ELEMENT-CREATE_ELEMENT-1

**Form:**

- Name (required)
- Stereotype (dropdown — C4: System, Container, Component, Person, External)
- Package (dropdown — Context, Container, Component, Code)
- Properties (dynamic fields driven by stereotype schema)
- Owner
- **Relationships:** multi-row table — each row: direction (inbound / outbound), target element (search autocomplete), edge stereotype (e.g. depends_on, calls, serves)
- **Diagram placement:** checklist of existing Diagrams in the selected Package — checked = hint to Munin to include this element

On [Submit]: posts to the Munin pipeline with `source=human`. Munin validates placement and edge rules, produces a ChangeSet, auto-applies if in Auto-approval mode or queues for `Act 7` if in Manual-review mode.

#### Screen: ELEMENT-EDIT_ELEMENT-1

Same form as Create, pre-populated. Changes go through the same Munin pipeline.

#### Screen: ELEMENT-DELETE_ELEMENT-1

Modal: element name + stereotype; blast-radius panel showing all dependent relationships and elements affected. [Cancel] [Delete]. Deletion queues as a ChangeSet; Munin identifies now-orphaned relationships and includes them in the review.

---



## Act 4: Relationships — Full CRUDLF

**Context:** Marcus needs to wire a `depends_on` relationship between two existing elements that Ratatosk missed, and correct an edge stereotype that was misclassified.

**Pattern:** Full CRUDLF with LIST+FIND as entry point. All writes go through the Munin pipeline.

#### Screen: RELATIONSHIP-LIST+FIND-1

Marcus clicks "Relationships" in nav.

**Layout:**

- **Header:** "Relationships" with count badge
- **Actions:** [Create Relationship]
- **Filters:** Edge Stereotype, From Element, To Element, Confidence, Source
- **Table:** From Element | Edge Stereotype | To Element | Confidence | Source | Actions
- **Row actions:** View, Edit, Delete



#### Screen: RELATIONSHIP-VIEW_RELATIONSHIP-1

Detail page: from/to elements (linked), edge stereotype, properties, provenance (source, last verified, confidence), change history.

#### Screen: RELATIONSHIP-CREATE_RELATIONSHIP-1

**Form:**

- From element (search autocomplete)
- Edge stereotype (constrained by the from-element's allowed edge rules per its stereotype)
- To element (search autocomplete, constrained by edge stereotype's allowed targets)
- Properties (dynamic per edge stereotype schema)

On [Submit]: Munin validates the edge against metamodel rules, creates the relationship, adds it to relevant diagrams, queues ChangeSet if Manual-review mode.

#### Screen: RELATIONSHIP-EDIT_RELATIONSHIP-1

Same form as Create, pre-populated. Changing the edge stereotype re-validates targets.

#### Screen: RELATIONSHIP-DELETE_RELATIONSHIP-1

Modal: from/to elements + edge stereotype; confirms deletion. Munin checks if any diagram layout or package integrity is affected.

---



## Act 5: MCP Browse — Query via Any AI Client

**Context:** Priya is in Cursor, mid-task, and wants to know what depends on a service before touching it — without leaving her editor. Marcus wants to wire a batch of relationships programmatically.

**Batch writes are intentionally excluded from the GUI.** In the GUI, batches are produced by Ratatosk runs and Munin's agentic loop, then reviewed as ChangeSets (`Act 7`). Manual batch entry via a GUI table is premature complexity — MCP's `update_elements_batch` / `update_relationships_batch` tools serve this need for scripting and automation, and `ask_munin` in chat handles it for interactive use.

**Key design principle — GUI-free users are first-class citizens.** A significant class of users (architects embedded in AI-native workflows, platform engineers, automation authors) will *never* open the browser UI. Their interface is Claude Desktop, Cursor Agent, or a custom MCP client. The MCP tool catalog must provide **complete feature parity with the GUI** — every read, every write, every workflow action available in the browser must be reachable via a tool call. The GUI is a convenience wrapper; the MCP layer is the product.

**Pattern:** No GUI screen — the FastMCP server exposes the same service layer as the REST API via `tools_handler.py` (Key Feature 4). Any MCP-aware client (Cursor, Claude Desktop, custom scripts) gets full read/write access to the live Model.

Priya's `mcp_config.json` (from `AUTH-TOKEN-1`):

```json
{
  "mcpServers": {
    "yggdrasil": {
      "base_url": "https://yggdrasil.featurefactory.io/mcp",
      "headers": { "Authorization": "Bearer <token>" }
    }
  }
}
```

### MCP Tool Catalog

#### Query tools (read-only)

| Tool | Signature (key params) | Returns | Ratatosk scout |
|---|---|---|---|
| `list_models` | _(none)_ | All registered Models with id, name, metamodel, mode (auto/manual) | — |
| `list_elements` | `model?, stereotype?, package?, filter?, as_of?, cursor?` | Paginated element list — mirrors the GUI element list view | **read** |
| `search` | `query, stereotype?, package?, filter?, as_of?` | Full-text + filter search; returns matching elements with properties | **read** |
| `get_element` | `id_or_name` | Element: properties, relationships, provenance, confidence | **read** |
| `list_relationships` | `model?, stereotype?, from_id?, to_id?, cursor?` | Paginated relationship list | reconcile only |
| `get_relationship` | `id` | Relationship: from/to, stereotype, properties, provenance | — |
| `traverse` | `from, direction?, depth?, stereotype?, as_of?` | Subgraph of elements and relationships | **read** |
| `list_stereotypes` | `model?` | All stereotypes defined in the metamodel (populates filter dropdowns) | **read** |
| `list_packages` | `model?` | All packages in the metamodel | **read** (spec — implement in MCP) |
| `list_diagrams` | `model?, package?` | All C4 diagrams — id, type (Context/Container/Component/Code), package | — |
| `get_diagram` | `id` | Diagram with element + relationship membership | — |
| `list_changesets` | `status?, source?` | Queue of pending/applied ChangeSets | — |
| `get_changeset` | `id` | ChangeSet with full operations list and Munin reasoning | — |
| `list_ratatosk_runs` | `model?, status?, limit?` | Paginated run list — id, trigger, status, timestamp, changeset_id | — |
| `get_ratatosk_run` | `run_id` | Run status, extraction log, Munin blackboard | — |

#### Write tools (all routed through Munin pipeline; respects Model's Auto/Manual mode)

| Tool | Signature (key params) | Effect |
|---|---|---|
| `create_element` | `name, stereotype, package, properties?, relationships?, diagram_hints?` | Munin validates and places; auto-applies or queues ChangeSet |
| `update_element` | `id, **fields` | Munin validates change; auto-applies or queues |
| `delete_element` | `id` | Munin checks blast-radius; queues deletion ChangeSet |
| `create_relationship` | `from_id, stereotype, to_id, properties?` | Munin validates edge rules; applies or queues |
| `update_relationship` | `id, **fields` | Munin validates; applies or queues |
| `delete_relationship` | `id` | Applies or queues |
| `update_elements_batch` | `operations: list[{op, ...}]` | Batch create/update/delete; Munin plans as one ChangeSet |
| `update_relationships_batch` | `operations: list[{op, ...}]` | Batch create/update/delete relationships |

#### ChangeSet tools

| Tool | Signature | Effect |
|---|---|---|
| `approve_changeset` | `id, item_ids?` | Approve all or specific items; Munin applies |
| `reject_changeset` | `id, item_ids?, reason?` | Reject; reason appended to LEARNED if provided |
| `do_other_changeset` | `id, item_ids, instructions` | Reject specific items and redirect Munin: "Do X instead"; Munin replans and produces a replacement ChangeSet; instructions appended to LEARNED |

#### Model configuration tools

| Tool | Signature | Effect |
|---|---|---|
| `set_model_mode` | `model_id, mode: auto\|manual` | Toggle whether high-confidence ops auto-apply or always queue for review |

#### Munin tools (ontology specialist / conversational)

| Tool | Signature | Returns |
|---|---|---|
| `ask_munin` | `question, context_element_ids?` | Answer text + cited element links + semantic URLs; may trigger agentic loop for complex operations |
| `get_munin_blackboard` | `run_id` | Munin's current JSON task list (step status: pending / completed / failed) — for monitoring and recovery |

#### Ratatosk tools (field agent)

| Tool | Signature | Returns |
|---|---|---|
| `ask_ratatosk` | `path_or_diff, model, metamodel?, instructions?` | Ratatosk fetches current model via MCP, runs guided analysis, produces delta buckets; returns `run_id` immediately (async) |

### Example interactions

**Priya in Cursor (never opens the GUI):** "What depends on the Payment API?" → Cursor calls `traverse(from="payment-api", direction="incoming")` → elements, owners, confidence — grounded in the live Model. She then calls `create_relationship` to add a missing dependency; Munin queues a ChangeSet; she calls `approve_changeset` — all without leaving her editor.

**Marcus via script:** bulk-wires a new service's relationships by calling `update_relationships_batch` with 12 operations; Munin plans one ChangeSet; Marcus calls `get_changeset` to inspect, then `approve_changeset`.

**Elena in Claude Desktop (GUI-free):** calls `list_elements(stereotype="Domain", as_of="2026-01-01")` to see the domain model as it was six months ago; compares with current via `list_elements(stereotype="Domain")`; asks `ask_munin("What domain objects were added or changed since Jan?")`.

**CI agent:** calls `ask_ratatosk(path="./repo", model="Yggdrasil")` post-merge → polls `get_ratatosk_run(run_id)` → on completion, calls `approve_changeset(id)` if all operations are high-confidence; calls `do_other_changeset` for the one item it's uncertain about, passing Munin a corrective instruction.

---



## Act 6: CI/CD Maintenance — Ratatosk Update

**Context:** Marcus's team merges a PR that adds a new downstream call. The Model must reflect that before the next architecture question is asked.

**Pattern:** Ratatosk runs as a pipeline step. Stdin is a **trigger** for a bounded scout loop — not the sole evidence source. Update is **incremental only** — it never wipes the graph.

`.github/workflows/yggdrasil.yml` (or equivalent GitLab CI step):

```yaml
- name: Update Yggdrasil model
  run: |
    git log -p ${{ github.event.before }}..${{ github.sha }} \
      | ratatosk update --model Yggdrasil --token=$YGGDRASIL_TOKEN \
          --repo $GITHUB_WORKSPACE \
          --instructions "Focus on interface changes — any API contracts added, removed, or modified?"
```

Commit-message-only trigger (scout reads referenced paths + linked issues):

```bash
echo "feat(llm.planner): add planning to the agent #MIM-056" \
  | ratatosk update --model Yggdrasil --token=$YGGDRASIL_TOKEN \
      --repo ./repo
# Scout plan: read src/llm/planner/**, fetch MIM-056 via Atlassian MCP, probe existing planner elements via Yggdrasil MCP
```

Same stdin path for ad-hoc prose (README, notes):

```bash
cat README.md | ratatosk update --model Yggdrasil --token=$YGGDRASIL_TOKEN \
  --repo ./repo \
  --instructions "Extract containers and components mentioned in this overview"
```

Ratatosk builds a **ModelSummary**, classifies the stdin trigger (`diff` / `commit_log` / `prose`), runs a **bounded scout loop** (plan evidence → gather from `--repo` + Yggdrasil MCP + connector MCPs → extract → delta reconcile), and hands buckets to Munin. When scout/diff evidence shows a mapped element was removed, Ratatosk **auto-proposes `to_delete`** (confidence threshold + ChangeSet review still apply). Noise-only diffs must not delete existing elements. **`unchanged`** elements are never sent to Munin.

---



## Act 7: Change Review — Munin's Work Plan

**Context:** Munin produces a ChangeSet after every write source (Ratatosk, human GUI, CI/CD, MCP). The ChangeSet is Munin's structured plan of precise graph operations — not raw candidates. Operating mode determines whether the human sees it before or after it applies.

**Operating modes** (per-Model setting, accessible from Model config):

- **Auto-approval**: Munin applies the ChangeSet directly to the Model. A completed ChangeSet is kept as an audit trail. The human can inspect it and roll back the entire run if needed.
- **Manual-review**: all operations queue before applying. Human reviews each operation, accepts/rejects/instructs. Only then does Munin apply approved items.



#### Screen: CHANGESET-LIST+FIND-1

Queue: Run ID | Source (Ratatosk / Human / MCP) | Submitted | Operations | Mode | Status (Pending / Applied / Rolled Back / Rejected) | Actions.

#### Screen: CHANGESET-VIEW_CHANGESET-1

**Header:** Run ID, source, submission time, Mode badge (Auto / Manual), Munin's summary reasoning.

**Operations list** — each row is one precise graph operation Munin planned:


| #   | Operation      | Detail                                          | Status  | Actions                      |
| --- | -------------- | ----------------------------------------------- | ------- | ---------------------------- |
| 1   | Add Element    | "Notification Service" → Container / Technology | Pending | [Accept] [Reject] [Do Other] |
| 2   | Link Element   | Notification Service →`depends_on`→ Payment API | Pending | [Accept] [Reject] [Do Other] |
| 3   | Add to Diagram | Notification Service → Container Diagram C1     | Pending | [Accept] [Reject] [Do Other] |


**[Do Other]:** opens an instruction input inline — user types a correction ("don't add this to the Container diagram, it's an external system"). On submit, Munin re-processes that single operation with the instruction prepended as context, then updates the LEARNED component so the same mistake is not repeated.

**Bulk actions:** [Accept All] [Reject All] [Accept High Confidence]

**Auto-approval ChangeSet view:** shows the same operations list, already applied, with a [Roll Back Entire Run] action that reverses all operations as a new ChangeSet (source=rollback).

Marcus reviews 3 pending operations, accepts 2, uses [Do Other] on the third with "Code diagram is for repository structure, not runtime services" → Munin re-processes, moves the element to the Container diagram, appends the rule to LEARNED.

---



## Act 8: Chat with Munin

**Context:** Marcus is about to touch the Payment API and wants to know who owns it and how it has drifted since the last release, before writing a line of code.

**Pattern:** Munin's chat is embedded **inside** the View Browser (`VIEW-BROWSE-1`) as a collapsible side panel — when Munin scopes a view or opens a form, it drives the surrounding screen directly. Also reachable headlessly via the `ask_munin` MCP tool (`Act 5`).

#### Screen: CHAT-MUNIN-1 (embedded panel within VIEW-BROWSE-1)

**Layout:**

- **Chat thread:** user messages + Munin's responses with cited element links and clickable semantic URLs
- **Context panel:** elements referenced in the last answer (live from graph)
- **Input:** natural language + optional @element mentions

Munin answers from ground truth only (never hallucinates), drives the surrounding View Browser via semantic URLs, and can open pre-filled create/edit forms via prefill URLs.

**Munin's agentic loop:** for complex requests, Munin runs multiple tool calls in sequence — fetch an element, inspect its linked elements, decide which to update, execute a batch operation — maintaining a blackboard of its intent that survives a crash and supports recovery (see System Notes).

**Example 1 — find & navigate:** "Who owns Payment API?" → Munin queries the graph, responds with owner/health, navigates the view to `/elements/payment-api`.

**Example 2 — scope a view:** "Show me everything that depends on Payment API and is owned by another team" → Munin constructs `/traverse?from=payment-api&direction=incoming&filter={"owner_ne":"my-team"}` and navigates.

**Example 3 — propose an element:** "Add Notification Service as a Container under Technology" → Munin responds with a clickable link to `/elements/new?prefill={"name":"Notification Service","stereotype":"Container","package":"technology"}` — the human clicks, reviews the pre-filled form, and submits.

**Example 4 — tell a story:** "Tell me a story about changes in the model of Payment API" → Munin reads the bitemporal history — every ChangeSet, Ratatosk run, and Munin decision that touched this element — and narrates as a timeline with a diff link.

**Example 5 — batch update:** "Link all Components in the Payment package to the new API Gateway" → Munin runs an agentic loop: searches for all Components in the Payment package, plans the relationship additions, calls `update_relationships_batch`, posts a ChangeSet for review if in Manual mode.

**Example 6 — generate a briefing:** "Generate a Markdown briefing for the Payment System — one section per C4 level, Mermaid diagrams included, written for a non-technical audience" → Munin scopes the subgraph, generates Mermaid blocks for each level, writes a narrative per section, and returns a Markdown document in the chat — the user copies it or downloads it directly. (Same artifact as `EXPORT-BRIEFING-1`, generated conversationally rather than through the export UI.)

---



## Act 9: Ratatosk & Munin Run History (read-only in GUI)

**Context:** Alex checks the bootstrap run from `Act 1` and the incremental run from `Act 6`.

#### Screen: RATATOSK_RUN-LIST+FIND-1

List: Run ID | Connector | Started | Duration | Candidates extracted | Operations planned | ChangeSets created | Status.

#### Screen: RATATOSK_RUN-VIEW_RATATOSK_RUN-1

**Layout:**

- **Ratatosk extraction log:** raw candidates discovered (elements, relationships, diff sections)
- **Munin reasoning trace:** why each candidate was turned into a specific graph operation; edge rule checks; package placement decisions
- **Munin blackboard:** JSON task list showing each step Munin intended to execute, with status (completed / skipped / failed) — visible for debugging and trust; persists through crashes for recovery
- **Link to ChangeSet** (`Act 7`)

---



## Part II — Post-MVP (Governance & Metamodel)

**Scope:** Elements and Relationships are fully manageable in Part I (Acts 3-4). Part II is exclusively Elena's metamodel governance — Stereotypes, Packages, and Diagrams — enabling the Model to evolve beyond the C4 default.

## Act 10: Metamodel — Stereotypes & Packages

**Context:** Elena governs the metamodel once the Model has matured beyond C4-only.

#### Screen: STEREOTYPE-LIST+FIND-1

List of stereotype definitions with property schemas and allowed edge rules.

#### Screen: PACKAGE-LIST+FIND-1

Package hierarchy (Business View, Application Layer, …).

#### Screen: DIAGRAM-LIST+FIND-1

Diagrams per package; [Open in Graph Editor] launches Cytoscape layout editor.

---



## System Notes

- **Web UI:** Django + HTMX + Bootstrap + Cytoscape.js
- **API:** DRF REST (engine); all writes (human, Ratatosk, MCP) go through the Munin/ChangeSet pipeline
- **MCP:** FastMCP thin layer over REST; raw tools: `search`, `get_element`, `traverse`, `update_elements_batch`, `update_relationships_batch`; higher-level tool: `ask_munin`
- **Ratatosk:** CLI only in MVP (`ratatosk bootstrap`, `ratatosk update`); field agent — element NER + provenance (small/fast/cheap LLM). **`bootstrap`:** bulk-wipes Elements + Relationships on target Model, then full filesystem scan; add-heavy buckets. **`update`:** stdin-triggered bounded scout (local `--repo` + Yggdrasil MCP + connector MCPs); incremental delta reconcile; **never wipes**; auto-proposes `to_delete` when removal evidence is strong. **ModelSummary** (default 8000 token budget) in prompts; full graph via MCP drill-down only. Config merge: CLI → env → repo `ratatosk.yaml` → `~/.ratatosk/config.yaml`. Relationships planned by **Munin**, not Ratatosk. GUI shows run history, never triggers runs; also invocable via `ask_ratatosk` MCP tool
- **Munin — ontology specialist and agentic planner:**
  - Reads candidates from any source (Ratatosk, human form, MCP) and produces a ChangeSet: a structured plan of precise graph operations (add/update/delete/link)
  - Operates via an agentic loop with access to the same tools as MCP (via `tools_handler.py` exposing all `*_service.py`)
  - Maintains a **blackboard** (JSON task list) of its current intent — written before acting, updated as steps complete; survives crashes; visible in run history
  - Supports **batch operations** (`update_elements_batch`, `update_relationships_batch`) for multi-element reasoning in a single loop
  - **LEARNED component:** append-only log of `MuninRule` entities (`{model, rule_text, source_changeset_item, contributed_by, created_at}`) built from user "Do Other" feedback; prepended to Munin's BASE prompt on every run so corrections persist; per-Model, user-attributed, versioned
  - Generates semantic URLs and prefill URLs in chat responses (clickable HTML links)
  - Embedded in the View Browser as `CHAT-MUNIN-1`; also reachable via `ask_munin` MCP tool
- **ChangeSet operating modes** (per-Model): **Auto-approval** — Munin applies directly, ChangeSet kept as audit trail with rollback available; **Manual-review** — all operations queue for human accept/reject/do-other before applying
- **Concurrency:** optimistic locking on Element and Relationship writes; concurrent edits detected and surfaced as conflicts in the ChangeSet rather than silent overwrites
- **Auth:** session auth for the Web UI; personal access tokens (`AUTH-TOKEN-1`) for Ratatosk CLI and MCP clients
