# Yggdrasil User Journey (ESM-02)

Personas from [PRD.MD](../../PRD.MD). Primary actors: **Elena** (Enterprise Architect), **Marcus** (Development Team Lead), **Alex** (Platform / Nerve-Ring Lead).

---

## Act 0: Authentication

**Context:** Any user opens Yggdrasil. Unauthenticated users see login; authenticated users land on the dashboard.

#### Screen: AUTH-LOGIN-1

Elena opens `https://yggdrasil.example.com`. Login form: email, password, [Sign in]. On success → `VIEW-BROWSE-1` (default landing).

---

## Act 1: View Browser — Explore the Graph

**Context:** Elena needs to see all Applications supporting Capability "Fulfill Orders" and their owners. This is the flagship "view browser" (Key Feature #2).

**Pattern:** Multi-level filter panel + results table/graph toggle.

#### Screen: VIEW-BROWSE-1

**Layout:**
- **Header:** "View Browser" with saved-views dropdown
- **Filter panel (left):**
  - Package selector (Business View, Technology View, …)
  - Stereotype multi-select (Application, Capability, …)
  - Property filters (owner, health, confidential)
  - [Apply Filters] [Clear] [Save View]
- **Results (center):**
  - Table mode: columns Name, Stereotype, Owner, Health, Package
  - Graph mode: Cytoscape.js rendering of filtered subgraph
  - Toggle [Table] [Graph]
- **Detail drawer (right):** selected element summary + quick links to VIEW/EDIT

Elena selects Package "Business View", Stereotype "Capability", filters name contains "Fulfill Orders", sees 1 capability node; expands to dependent Applications in graph mode.

---

## Act 2: Elements — Complete CRUDLF

**Context:** Marcus needs to inspect and occasionally correct elements Ratatosk discovered.

**Pattern:** Standard CRUDLF with LIST+FIND as entry point.

#### Screen: ELEMENT-LIST+FIND-1

Marcus clicks "Elements" in nav. List page:

**Layout:**
- **Header:** "Elements" with count badge
- **Actions:** [Create Element] [Import]
- **Search:** "Find elements…" (name, stereotype, package)
- **Filters:** Stereotype, Package, Health, Source (Ratatosk/Manual)
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

## Act 3: Relationships — Complete CRUDLF

**Context:** Marcus wires upstream/downstream dependencies.

#### Screen: RELATIONSHIP-LIST+FIND-1

List: From Element | Edge Type | To Element | Confidence | Actions.

#### Screen: RELATIONSHIP-CREATE_RELATIONSHIP-1

Form: from element (search), edge stereotype, to element (search), properties.

---

## Act 4: Metamodel — Stereotypes & Packages

**Context:** Elena governs the metamodel (Zachman/TOGAF stereotypes).

#### Screen: STEREOTYPE-LIST+FIND-1

List of stereotype definitions with property schemas and allowed edge rules.

#### Screen: PACKAGE-LIST+FIND-1

Package hierarchy (Business View, Application Layer, …).

#### Screen: DIAGRAM-LIST+FIND-1

Diagrams per package; [Open in Graph Editor] launches Cytoscape layout editor.

---

## Act 5: Change Review — Ratatosk Writes

**Context:** Ratatosk submitted a ChangeSet with 12 proposed elements; 3 are low-confidence and need human approval.

#### Screen: CHANGESET-LIST+FIND-1

Queue: Run ID | Source | Submitted | Items | Confidence | Status (Pending/Applied/Rejected) | Actions.

#### Screen: CHANGESET-VIEW_CHANGESET-1

Diff view: proposed adds/updates/deletes side-by-side with current graph. [Approve All High Confidence] [Review Item-by-Item] [Reject].

---

## Act 6: AI Chat — Grounded Assistant

**Context:** Marcus asks "Who owns the Payment API?" before starting integration work.

#### Screen: CHAT-ASSIST-1

**Layout:**
- Chat thread (left/center): user messages + assistant responses with cited element links
- Context panel (right): elements referenced in last answer (live from graph)
- Input: natural language + optional @element mentions
- Assistant uses MCP/API ground truth; never hallucinates architecture

Marcus types "Who owns Payment API?" → assistant queries `/elements?stereotype=Application&name=Payment API` → responds with owner, health, and link to `ELEMENT-VIEW_ELEMENT-1`.

---

## Act 7: Ratatosk Runs (read-only in GUI)

**Context:** Alex checks last bootstrap run status.

#### Screen: RATATOSK_RUN-LIST+FIND-1

List: Run ID | Connector | Started | Duration | Elements discovered | ChangeSets created | Status.

#### Screen: RATATOSK_RUN-VIEW_RATATOSK_RUN-1

Run log, provenance summary, link to resulting ChangeSet.

---

## System Notes

- **Web UI:** Django + HTMX + Bootstrap + Cytoscape.js
- **API:** DRF REST (engine); all writes go through ChangeSet when from Ratatosk
- **MCP:** FastMCP thin layer over REST for Claude/Cursor
- **Ratatosk:** CLI only in MVP; GUI shows run history via API
