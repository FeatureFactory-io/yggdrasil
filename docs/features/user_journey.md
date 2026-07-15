# Yggdrasil User Journey (ESM-02)

Personas from [PRD.MD](../../PRD.MD). Primary actors: **Priya** (Software Architect), **Marcus** (Development Team Lead), **Elena** (Enterprise Architect), **Alex** (Platform / Nerve-Ring Lead). Priya and Marcus are the wedge's primary users (Part I); Elena governs the metamodel once the Model matures (Part II).

---

## Part I — MVP (The Wedge)

**Scope:** Connect a repo, bootstrap a Model, keep it current from CI/CD, browse/query it via GUI or any AI client, and ask Munin about it. No manual metamodel design or full CRUDLF here — Ratatosk and Munin populate and maintain the Model. See [PRD.MD](../../PRD.MD) "The wedge / 1st bet".

## Act 0: Authentication & API Access

**Context:** Any user opens Yggdrasil. Unauthenticated users see login; authenticated users land on the dashboard. Accounts are admin-provisioned (Groups/PBAC — Key Features 6/7), not self-registered. CLI (Ratatosk) and MCP clients authenticate with a personal access token instead of a session.

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
  - Ratatosk CLI: `ratatosk bootstrap ./repo --token=<token>`
  - `mcp_config.json`:
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

---

## Act 1: Ratatosk Bootstrap (CLI)

**Context:** Priya just generated a token (`AUTH-TOKEN-1`). She wants an initial Model built from the repo her team already ships from — no manual data entry.

**Pattern:** CLI-only in MVP — the GUI shows the result of a run, not its trigger (see System Notes).

```bash
$ export YGGDRASIL_TOKEN=<token>
$ ratatosk bootstrap ./repo --token=$YGGDRASIL_TOKEN --model Yggdrasil --metamodel=c4
[ratatosk] scanning ./repo …
[ratatosk] found 3 services, 12 modules, 4 external dependencies
[ratatosk] extracted 19 candidate elements, 27 candidate relationships
[munin]    reconciling against existing Model "Yggdrasil" (0 elements) …
[munin]    placed 16 elements into Context/Container/Component packages (C4)
[munin]    3 elements below confidence threshold → ChangeSet #1 queued for review
[ratatosk] run complete: 19 elements, 27 relationships, 1 ChangeSet pending
          → https://yggdrasil.featurefactory.io/runs/1
```

C4 is the default — and only — metamodel choice in MVP: Ratatosk seeds the Vertex/Edge/Stereotype/Diagram/Package structure (Context, Container, Component, Code views) automatically. There is no metamodel picker screen yet; designing/evolving the metamodel is Key Feature 12, Part II.

**Pipeline:** Ratatosk (field agent — NER + reconciliation against the existing graph, runs on a small/fast/cheap LLM) hands every candidate to **Munin** (ontology specialist — decides package/diagram placement). High-confidence placements apply directly to the Model; low-confidence ones queue as a ChangeSet (`Act 5`).

Priya follows the printed link to `RATATOSK_RUN-VIEW_RATATOSK_RUN-1` (`Act 7`) to see the run in the GUI.

---

## Act 2: View Browser — Explore the Graph

**Context:** Priya needs to see all Applications supporting Capability "Fulfill Orders" and their owners. This is the flagship "view browser" (Key Feature #2).

**Pattern:** Multi-level filter panel + results table/graph toggle.

#### Screen: VIEW-BROWSE-1

**Layout:**
- **Header:** "View Browser" with saved-views dropdown
- **Filter panel (left):**
  - Package selector (Context, Container, Component, Code — from the C4 bootstrap)
  - Stereotype multi-select (Application, Capability, …)
  - Property filters (owner, health, confidential)
  - [Apply Filters] [Clear] [Save View]
- **Results (center):**
  - Table mode: columns Name, Stereotype, Owner, Health, Package
  - Graph mode: Cytoscape.js rendering of filtered subgraph
  - Toggle [Table] [Graph]
- **Detail drawer (right):** selected element summary + quick links to VIEW/EDIT
- **Munin panel:** collapsible chat side panel (`Act 6`) that can drive this same screen

Priya selects Package "Business View", Stereotype "Capability", filters name contains "Fulfill Orders", sees 1 capability node; expands to dependent Applications in graph mode.

**AI-constructed URL:** Priya could reach the same scoped view without touching a filter control by asking Munin "show me apps that depend on Fulfill Orders" — Munin navigates straight to `/views/business-view/application?filter={"depends_on":"Fulfill Orders"}` (Key Feature 1). Any element/subgraph/list the filter panel can express has a corresponding URL an AI agent can construct directly, without going through the panel at all.

---

## Act 3: MCP Browse — Query via Any AI Client

**Context:** Priya is in Cursor, mid-task, and wants to know what depends on a service before touching it — without leaving her editor.

**Pattern:** No GUI screen — the FastMCP server wraps the same REST API the View Browser calls, so any MCP-aware client can query ground truth directly (Key Feature 4).

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

She asks Cursor: "What depends on the Payment API?" → Cursor calls the `traverse` tool (`from=Payment API, direction=incoming`) → gets back elements, owners, and health, grounded in the live Model — never a hallucinated architecture (Key Feature 1; the Organizational AI persona in [PRD.MD](../../PRD.MD)).

Available tools mirror the REST surface: `search`, `get_element`, `traverse`. `ask_munin` (`Act 6`) is a separate, higher-level tool for conversational/narrative queries.

---

## Act 4: CI/CD Maintenance — Ratatosk Update

**Context:** Marcus's team merges a PR that adds a new downstream call. The Model must reflect that before the next architecture question gets asked against it.

**Pattern:** Ratatosk runs as a pipeline step, fed the diff instead of a full repo scan (Phase 3: Maintain, [PRD.MD](../../PRD.MD)).

`.github/workflows/yggdrasil.yml` (or equivalent GitLab CI step):

```yaml
- name: Update Yggdrasil model
  run: |
    git log -p ${{ github.event.before }}..${{ github.sha }} \
      | ratatosk update --model Yggdrasil --token=$YGGDRASIL_TOKEN
```

Ratatosk parses the diff, identifies what changed structurally (new/removed calls, modules, dependencies), hands candidates to Munin for reconciliation, and posts the result as a run plus — if anything is low-confidence — a ChangeSet. Same pipeline as the bootstrap (`Act 1`), just incremental.

---

## Act 5: Change Review — Munin's Integration

**Context:** From the CI/CD run in `Act 4`, Ratatosk proposed 12 candidate elements; Munin placed 9 directly into the Model (high confidence) and queued 3 for human review because their package/stereotype placement was ambiguous.

#### Screen: CHANGESET-LIST+FIND-1

Queue: Run ID | Source | Submitted | Items | Confidence | Status (Pending/Applied/Rejected) | Actions.

#### Screen: CHANGESET-VIEW_CHANGESET-1

Diff view: Munin's proposed adds/updates/deletes side-by-side with the current graph, including Munin's reasoning for each placement (e.g. "placed under Container/Payment Service — closest existing Component by import graph"). [Approve All High Confidence] [Review Item-by-Item] [Reject].

Marcus approves the 3 pending items; the Model updates immediately and is reflected the next time anyone opens `VIEW-BROWSE-1` (`Act 2`) or queries via MCP (`Act 3`).

---

## Act 6: Chat with Munin

**Context:** Marcus is about to touch the Payment API and wants to know who owns it — and separately, the story of how it has drifted since the last release — before writing a line of code.

**Pattern:** Munin's chat is embedded **inside** the View Browser (`VIEW-BROWSE-1`) as a side panel, not a standalone page, so when Munin scopes a view it drives the very screen it's attached to. It is also reachable headlessly via the `ask_munin` MCP tool (`Act 3`).

#### Screen: CHAT-MUNIN-1 (embedded panel within VIEW-BROWSE-1)

**Layout:**
- **Chat thread** (panel, collapsible): user messages + Munin's responses with cited element links
- **Context panel:** elements referenced in the last answer (live from graph)
- **Input:** natural language + optional @element mentions
- Munin answers from MCP/API ground truth only, never hallucinates architecture — and can navigate the surrounding View Browser directly via semantic URLs (`Act 2`)

**Example 1 — find & navigate:** Marcus types "Who owns Payment API?" → Munin queries the graph, responds with owner/health, and navigates the surrounding view to `/elements/payment-api` (`ELEMENT-VIEW_ELEMENT-1`).

**Example 2 — scope a view:** "Show me everything that depends on Payment API and is owned by another team" → Munin constructs and navigates to `/traverse?from=payment-api&direction=incoming&filter={"owner_ne":"my-team"}`.

**Example 3 — tell a story:** "Tell me a story about changes in the model of Payment API" → Munin reads the bitemporal history (Key Feature 8: time-travel & diff) — every ChangeSet, Ratatosk run, and Munin placement decision that touched this element — and narrates it as a timeline, ending with a link to the diff between two points in time.

---

## Act 7: Ratatosk & Munin Run History (read-only in GUI)

**Context:** Alex checks the bootstrap run from `Act 1`, and the incremental run that just fired from `Act 4`.

#### Screen: RATATOSK_RUN-LIST+FIND-1

List: Run ID | Connector | Started | Duration | Elements discovered | ChangeSets created | Status.

#### Screen: RATATOSK_RUN-VIEW_RATATOSK_RUN-1

Run log split by agent: Ratatosk's raw extraction (elements/relationships discovered, source diff/scan) and Munin's integration decisions (where each candidate was placed and why, what queued as a ChangeSet). Link to the resulting ChangeSet (`Act 5`).

---

## Part II — Post-MVP (Governance & Manual Curation)

**Scope:** Everything below serves Elena (Enterprise Architect) governing the metamodel and manually curating elements. None of it is required for the wedge (Part I) — Ratatosk and Munin populate and maintain the Model without manual CRUD. Kept here for completeness and next-iteration planning.

## Act 8: Elements — Complete CRUDLF

**Context:** Marcus occasionally needs to inspect and correct elements Ratatosk/Munin discovered.

**Pattern:** Standard CRUDLF with LIST+FIND as entry point.

#### Screen: ELEMENT-LIST+FIND-1

Marcus clicks "Elements" in nav. List page:

**Layout:**
- **Header:** "Elements" with count badge
- **Actions:** [Create Element] [Import]
- **Search:** "Find elements…" (name, stereotype, package)
- **Filters:** Stereotype, Package, Health, Source (Ratatosk/Munin/Manual)
- **Table:** Name | Stereotype | Package | Owner | Health | Source | Actions
- **Row actions:** View, Edit, Delete
- **Empty state:** "No elements yet — connect Ratatosk or create manually"

#### Screen: ELEMENT-VIEW_ELEMENT-1

Detail page: structural properties (JSONB), behavioral links (incoming/outgoing relationships), state panel (health, provenance, confidence, last verified), mini Cytoscape ego-graph.

#### Screen: ELEMENT-CREATE_ELEMENT-1 / ELEMENT-EDIT_ELEMENT-1

Form: name, stereotype (dropdown from STEREOTYPE entities), package, properties (dynamic fields per stereotype schema), owner.

#### Screen: ELEMENT-DELETE_ELEMENT-1

Modal: confirms deletion; shows blast-radius (dependent relationships count).

---

## Act 9: Relationships — Complete CRUDLF

**Context:** Marcus wires upstream/downstream dependencies.

#### Screen: RELATIONSHIP-LIST+FIND-1

List: From Element | Edge Type | To Element | Confidence | Actions.

#### Screen: RELATIONSHIP-CREATE_RELATIONSHIP-1

Form: from element (search), edge stereotype, to element (search), properties.

---

## Act 10: Metamodel — Stereotypes & Packages

**Context:** Elena governs the metamodel (Zachman/TOGAF stereotypes) once the Model has matured beyond C4-only.

#### Screen: STEREOTYPE-LIST+FIND-1

List of stereotype definitions with property schemas and allowed edge rules.

#### Screen: PACKAGE-LIST+FIND-1

Package hierarchy (Business View, Application Layer, …).

#### Screen: DIAGRAM-LIST+FIND-1

Diagrams per package; [Open in Graph Editor] launches Cytoscape layout editor.

---

## System Notes

- **Web UI:** Django + HTMX + Bootstrap + Cytoscape.js
- **API:** DRF REST (engine); all writes go through a ChangeSet when the source is Ratatosk/Munin
- **MCP:** FastMCP thin layer over REST for Claude/Cursor/any MCP client; raw tools (`search`, `get_element`, `traverse`) plus a higher-level `ask_munin` tool
- **Ratatosk:** CLI only in MVP (`ratatosk bootstrap`, `ratatosk update`); field agent — NER + reconciliation against the existing graph; GUI shows run history via API, never triggers a run
- **Munin:** ontology specialist sitting between Ratatosk and the Model — decides package/diagram placement, auto-applies high-confidence changes, queues the rest as a ChangeSet; reachable via chat (embedded in the View Browser) and MCP; constructs semantic URLs on the user's behalf
- **Auth:** session auth for the Web UI; personal access tokens (`AUTH-TOKEN-1`) for Ratatosk CLI and MCP clients
