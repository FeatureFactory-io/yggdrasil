# Ratatosk spec realignment — change inventory and doc plan

> **Scope:** Documentation and feature specs only (`PRD.MD`, `user_journey.md`, `docs/features/**`, `SAO.md`). Implementation is a separate milestone.
>
> **Source:** Full conversation thread (MetaModel → guidance → bootstrap/update semantics → scout loop → config → model context).

---

## Part A — Complete change inventory (conversation conclusions)

### A1. Metamodel (context, minor doc touch-ups)

| # | Change | Notes |
|---|--------|-------|
| A1.1 | Multiple `Metamodel` rows allowed; each `YggdrasilModel` binds to one slug immutably | Already true in code; clarify in journey if ambiguous |
| A1.2 | C4 is MVP default via `ensure_c4_metamodel()`; custom metamodels via Django admin | Act 10 is Part II for GUI editor |
| A1.3 | Ratatosk consumes metamodel via `_metamodel_guidance()` text (stereotypes, packages, schemas, rules) appended to LLM **user** message | Document in pipeline step 2; not invent catalog rows |
| A1.4 | MCP `list_stereotypes` is read-only catalog access for CLI; not metamodel CRUD | Already in Act 5 |

### A2. Ratatosk vs Munin responsibilities

| # | Change | Owner |
|---|--------|-------|
| A2.1 | Ratatosk extracts **element** candidates (name, stereotype, package, confidence, properties) | Ratatosk |
| A2.2 | Munin plans **relationships**, edge stereotypes, diagram membership, metamodel validation | Munin |
| A2.3 | Journey/PRD examples that show Ratatosk emitting `add-relationship ops` are **wrong** for Ratatosk NER; move to Munin handoff narrative | Docs fix |
| A2.4 | User confirmed: Munin handling links ("where shall I link this?") is **intentional** | No Ratatosk relationship NER in MVP spec |

### A3. Bootstrap vs update — graph policy (user-corrected)

| # | Change | `bootstrap` | `update` |
|---|--------|-------------|----------|
| A3.1 | Graph mutation policy | **Wipe** all Elements + Relationships on the Model, then rescan repo | **Incremental** — never wipe |
| A3.2 | What is preserved on bootstrap wipe | `YggdrasilModel` row + metamodel FK + RBAC | N/A |
| A3.3 | Input | Repo path — full filesystem tree scan | Stdin blob **triggers** analysis (diff, prose, commit log) |
| A3.4 | Re-bootstrap on populated model | **Clean wipe**, not delta merge | N/A |
| A3.5 | Relationship to each other | **Different commands, different policies** — re-bootstrap is **not** "update by another name" | Same 7-step **family**, different steps 0/3–6 behavior |
| A3.6 | `unchanged` bucket | **Not meaningful** against pre-wipe graph on bootstrap | Core to incremental reconcile; never sent to Munin |
| A3.7 | Wipe scope (user confirmed) | Elements + Relationships only | — |
| A3.8 | Wipe mechanism (user confirmed) | **Single bulk wipe** operation before scan (fast; auditable via ChangeSet; revertible via rollback/time-travel) | — |

### A4. Update scout loop (user-corrected — NOT stdin-only)

| # | Change |
|---|--------|
| A4.1 | Stdin/diff/commit log is the **trigger**, not the only evidence |
| A4.2 | **Bounded scout loop:** trigger → plan evidence → gather → extract → reconcile → handoff |
| A4.3 | **Local tools:** `read_file`, `list_dir`, `git_diff_paths` (require `--repo` or `$WORKSPACE`) |
| A4.4 | **Yggdrasil MCP read tools** for model drill-down (see A5) |
| A4.5 | **External MCP** (e.g. Atlassian `get_issue` for `#MIM-056`) when configured |
| A4.6 | Example: `feat(llm.planner): … #MIM-056` → read `src/llm/planner/**` + fetch ticket + extract Component |
| A4.7 | Limits: **10** scout rounds, **1000** file reads, **50** MCP calls per run (large-PR scale; overridable in config) |
| A4.8 | Blackboard records scout plan, tool calls, evidence sources |

### A5. Model context for LLM (user decision — NOT full in-prompt graph)

| # | Change |
|---|--------|
| A5.1 | **Do not** inject full element/relationship graph into prompt (unbounded size) |
| A5.2 | Inject **depth-expanded ModelSummary** built under a **token budget** (default **8000 tokens**) at scout/map/extract turns |
| A5.3 | **Expansion algorithm:** (a) serialize top level → measure tokens `X` → `REM = BUDGET - X`; stop if `REM` near 0; (b) serialize next level derived from top-level nodes → measure `X` → decrement `REM`; repeat until budget exhausted; (c) pass whatever depth was reached into the prompt |
| A5.4 | **Level mapping (C4 example):** L0 = model slug + metamodel + totals; L1 = counts by package + stereotype; L2 = element names/slugs per package; L3+ = selected properties or immediate relationship hints — only if budget allows |
| A5.5 | **Drill-down via tools** when summary insufficient at any depth — never exceed budget by stuffing more graph |
| A5.6 | Yggdrasil MCP tools Ratatosk scout may call: `list_elements`, `get_element`, `search`, `traverse`, `list_stereotypes`, `list_packages` |
| A5.7 | `list_packages` in SAO/journey inventory but **not implemented** in code — spec as required; note impl gap |
| A5.8 | Reconcile still uses full snapshot `by_slug` in **code** after extract — separate from LLM context |
| A5.9 | Token counting uses same tokenizer as configured Ratatosk LLM (or conservative estimate); `BUDGET` overridable in config |

### A6. Prompt Stack — Ratatosk identity

| # | Change |
|---|--------|
| A6.1 | Expand system **identity** layer: role in pipeline, outcome, precision-over-recall, Munin/ChangeSet handoff, never write graph directly |
| A6.2 | **Step-specific** system prompts: map-filesystem, map-stdin, extract (not one generic block) |
| A6.3 | Metamodel ontology stays in **user** message (`_metamodel_guidance()`), not duplicated in system |
| A6.4 | Dynamic layer = ModelSummary + source material + `--instructions` — not full graph |

### A7. CLI configuration

| # | Change |
|---|--------|
| A7.1 | User config: `~/.ratatosk/config.yaml` (or `~/.config/ratatosk/config.yaml`) |
| A7.2 | Project config: `ratatosk.yaml` or `.ratatosk/config.yaml` in repo |
| A7.3 | Merge order: **CLI flags → env → repo → user → defaults** |
| A7.4 | Secrets via `env:VAR_NAME` only — never committed |
| A7.5 | Tool allowlists per config: `local`, `mcp.yggdrasil`, `mcp.atlassian`, … |
| A7.6 | Jenkins: agent config + injected secrets; `CI=true` → stricter limits |
| A7.7 | Future: `ratatosk doctor` — print merged config + reachable MCPs |

### A8. Candidate provenance

| # | Change |
|---|--------|
| A8.1 | Candidates carry `sources[]`: e.g. `commit:…`, `file:…`, `jira:MIM-056`, `mcp:search:…` |
| A8.2 | Stored on blackboard / handed to Munin for review and briefing |

### A9. Update `to_delete` policy and scenarios

| # | Change |
|---|--------|
| A9.1 | Add Gherkin for `to_delete` on **update** path (diff removes service, etc.) |
| A9.2 | Add negative: noise-only diff / commit must **not** delete existing elements |
| A9.3 | **Update delete policy (resolved):** **auto-propose** `to_delete` when diff/scout evidence indicates a mapped element was removed; subject to confidence threshold + ChangeSet review |
| A9.4 | Bootstrap wipe is **bulk delete before scan** (A3.8), not per-element `to_delete` reconcile |

### A10. Conflicts to remove from current docs/specs

| Stale content | Location | Replace with |
|---------------|----------|--------------|
| Re-bootstrap delta (`unchanged: 22`) | user_journey Act 1 transcript | Wipe message + fresh `to_add` |
| "Guided bootstrap reads existing model first" | user_journey L82–84 | "Re-bootstrap wipes graph, then scans with instructions" |
| "Same unified 7-step loop" (symmetric) | user_journey pipeline table | Two columns with explicit policy differences + scout row |
| ACT-1-DISC-03 delta not rewrite | ratatosk-discovery.feature | Bootstrap wipes graph |
| ACT-1-CLI-02 found 31 existing | ratatosk-bootstrap.feature | Wipe messaging |
| ACT-1-CLI-03/04 unchanged/to_update on bootstrap | ratatosk-bootstrap.feature | Bootstrap bucket semantics post-wipe |
| ACT-6-CICD-04 "just like bootstrap" | ratatosk-update.feature | Update is incremental only |
| Ratatosk add-relationship ops in transcript | user_journey Act 1 | Munin plans relationships |
| Ratatosk stdin-only | Act 6 comments, journey | Stdin-triggered scout |
| Full graph in LLM / snapshot-in-prompt | any | ModelSummary + MCP drill-down |
| SAO Q4 Ratatosk single-pass only | SAO §17.1 | Bounded scout loop for Ratatosk |
| SAO Agent Loop Skip (Ratatosk) | SAO §17.2 | Bounded scout loop Required |

---

## Part B — File-by-file documentation plan

### B1. [PRD.MD](PRD.MD)

**Section: `# How Ratatosk Works` (L430+)**

- Add **`## Ratatosk CLI commands`** subsection before or after bootstrap modes:
  - **`ratatosk bootstrap <repo>`** — heroic full scan; **wipes** graph content on target Model; preserves Model + metamodel binding; proposes fresh element candidates via ChangeSet.
  - **`ratatosk update`** — incremental maintenance; **never wipes**; stdin triggers bounded scout (repo reads + MCPs); delta reconcile.
- Rewrite **`## Maintain: CI/CD pipeline agent`** (L446): stdin triggers scout; may read changed files and issue trackers; not diff-only analysis.
- Add **`## Ratatosk agent boundaries`**: elements + evidence (Ratatosk) vs links + ChangeSet ops (Munin).
- Add **`## Ratatosk model awareness`**: ModelSummary in prompt + Yggdrasil MCP drill-down; explicitly reject unbounded graph-in-prompt.

**Section: `# Key features`**

- **#5 Ratatosk:** mention config file, scout loop, bootstrap wipe vs update incremental.
- **#11 Connector framework:** Ratatosk CLI MCP allowlist as MVP delivery path for Jira/GitLab/etc.

**Section: `Phase 2 — Bootstrap` (L471)**

- Clarify: re-run bootstrap **replaces** graph content (wipe), not merge.

---

### B2. [docs/features/user_journey.md](docs/features/user_journey.md)

**Act 1 — Bootstrap (L70+)**

1. Replace CLI transcript entirely (two examples):
   - **First bootstrap** (empty model): scan → `to_add` only.
   - **Re-bootstrap** (populated): `wiping 31 elements and 44 relationships` → scan → `to_add` (no `unchanged` from old graph).
2. Remove Ratatosk `add-relationship ops` from munin line; Munin may add relationships from element candidates.
3. Replace pipeline table (L105–115) with:

| Step | bootstrap | update |
|------|-----------|--------|
| 0 | **Wipe** Elements + Relationships on Model | — (keep graph) |
| 1 | Build **ModelSummary** + MCP snapshot for reconcile/tools | Same |
| 2 | Metamodel guidance text | Same |
| 3 | File tree | Stdin blob + classify |
| 4 | Map → target paths | **Scout plan** (paths, issue keys, probe intents) |
| 5 | Read files → extract | Gather evidence (local + MCP) → extract |
| 6 | Cleanup + constrain to metamodel | Cleanup + **delta reconcile** |
| 7 | ChangeSet (add-heavy) | ChangeSet (delta; `unchanged` not sent) |

4. Add **`#### ModelSummary`** normative block (A5.2–A5.5): token-budget depth expansion (8000 default), level mapping, tool drill-down when budget stops early.
5. Add **`#### Prompt Stack (Ratatosk)`** (A6).
6. Add **`#### Bootstrap wipe rule`** (A3).

**Act 6 — CI/CD Update (L453+)**

1. Add `--repo` / `$GITHUB_WORKSPACE` to YAML example.
2. Add commit-message-only example triggering scout.
3. Replace "analyzes stdin blob" with scout loop narrative (A4).
4. Document **auto-propose `to_delete`** on update when removal evidence is strong (A9.3).

**System Notes (L602+)**

- Rewrite Ratatosk bullet (L607): bootstrap wipe, update scout, ModelSummary, config paths, Munin owns relationships.

**MCP tool table (L383+)**

- Column or annotation: Ratatosk scout read vs Munin write.
- Ensure `list_packages` listed for Ratatosk drill-down.

---

### B3. [docs/architecture/SAO.md](docs/architecture/SAO.md)

**§17.1 Mission Assessment**

| Row | From | To |
|-----|------|-----|
| Q1 Ratatosk | compiled pipeline only | compiled pipeline + **bounded scout loop** on update |
| Q4 | Multi-turn Munin only | Munin full ReAct; Ratatosk **bounded** multi-step scout |
| Q6 | Tool Surface for graph | Add: ModelSummary in prompt; graph detail via Tool Surface only |

**§17.2 Module Selection**

| Module | From | To |
|--------|------|-----|
| Agent Loop | Skip (Ratatosk) | **Required — bounded scout** (10 rounds / 1000 file reads / 50 MCP calls) |
| Agent Blackboard | Optional Ratatosk | **Required** for scout (`evidence_plan`, `tool_calls`, `sources`) |

**§17.3 Ratatosk — Field / Batch Specialist (L855+)**

Replace flow diagram:

```
Trigger (bootstrap | update)
  → [bootstrap only] bulk wipe Elements + Relationships on Model (single op; revertible)
  → ModelSummary + MCP snapshot
  → Metamodel guidance
  → [bootstrap] filesystem scan | [update] scout loop (stdin → plan → local/MCP gather)
  → Extract element candidates (Ratatosk NER)
  → [update only] delta reconcile
  → propose ChangeSet → Munin (relationships, validation, apply policy)
```

**§17.4 Agent Blackboard**

- Add Ratatosk scout keys: `evidence_plan`, `tool_calls`, `model_summary_chars`, `sources`.

**§18.3 MCP tool inventory (L1045+)**

- Mark `list_packages` as **Ratatosk scout read**.
- Add note: Ratatosk CLI may call subset of read tools + external connector MCPs per config allowlist.
- Optional new tool (spec only): `get_model_summary` if server-side summary generation preferred over client-built text.

**§1 graph bounded context (L34)** — no change needed unless adding wipe operation to changeset vocabulary.

---

### B4. [docs/features/](docs/features/) — Gherkin and catalog

#### Modify existing files

| File | Actions |
|------|---------|
| [act-1-ratatosk/ratatosk-bootstrap.feature](docs/features/act-1-ratatosk/ratatosk-bootstrap.feature) | Replace ACT-1-CLI-02 (wipe not "found 31"); revise ACT-1-CLI-03 (bootstrap buckets post-wipe); ACT-1-CLI-04 move unchanged/to_update/delete examples to **update** or Munin fixture |
| [act-1-ratatosk/ratatosk-discovery.feature](docs/features/act-1-ratatosk/ratatosk-discovery.feature) | **Replace ACT-1-DISC-03** with wipe scenario; add DISC-15 ModelSummary on blackboard; add DISC-16 metamodel guidance step recorded |
| [act-6-cicd/ratatosk-update.feature](docs/features/act-6-cicd/ratatosk-update.feature) | Fix ACT-6-CICD-04 title/body (incremental only); add CICD-15 `to_delete` from diff; CICD-16 no-delete on noise; CICD-17 commit-log triggers scout with `--repo`; CICD-18 ModelSummary + MCP drill-down; CICD-19 update never wipes |
| [CATALOG.md](docs/features/CATALOG.md) | New scenarios, step stubs, blackboard keys, config merge rules |

#### New feature files

| File | Contents |
|------|----------|
| `act-1-ratatosk/ratatosk-scout.feature` | Scout plan, local read, Yggdrasil MCP probe, Atlassian optional, provenance on candidates |
| `act-1-ratatosk/ratatosk-config.feature` | Config merge, allowlists, env secrets, doctor @wip |
| `act-1-ratatosk/ratatosk-model-summary.feature` | ModelSummary format bounds; overflow triggers `list_elements`; no full graph in blackboard prompt field |

#### Step definitions (stubs @wip in plan; implement in BPE)

| File | New steps |
|------|-----------|
| [steps/discovery_steps.py](docs/features/steps/discovery_steps.py) | wipe assertions, scout blackboard, MCP tool call recorded |
| [steps/cli_steps.py](docs/features/steps/cli_steps.py) | config merge fixtures, `--repo` on update |

#### Optional cross-reference

| File | Action |
|------|--------|
| [act-5-mcp/mcp-query.feature](docs/features/act-5-mcp/mcp-query.feature) | ACT-5 scenario for `list_packages` when tool exists |
| [act-1-ratatosk/munin-briefing.feature](docs/features/act-1-ratatosk/munin-briefing.feature) | Briefing mentions relationships planned by Munin, not Ratatosk |

---

## Part C — Suggested edit sequence

1. **SAO §17–§18** — architecture truth first (downstream docs cite this).
2. **PRD** — product narrative.
3. **user_journey** Act 1 + Act 6 + System Notes + ModelSummary spec.
4. **Gherkin** — fix conflicts (DISC-03, CLI-02/03/04, CICD-04) before adding new files.
5. **New feature files** — scout, config, model-summary.
6. **CATALOG.md** + step stub list.
7. **Consistency grep** — `unchanged`, `found 31 existing`, `stdin only`, `add-relationship ops`, `same unified loop`.

---

## Part D — Explicitly out of scope for this doc pass

- Implementing wipe, scout loop, config loader, `list_packages` MCP, `ratatosk doctor`
- Changing `agent.py` / `runner.py` / `prompts.py`
- Behave step implementations (mark `@wip` until BPE)

---

## Part E — Resolved spec decisions

| # | Decision | Resolution |
|---|----------|------------|
| E1 | Update delete policy | **Auto-propose** `to_delete` on update when diff/scout shows a mapped element was removed; confidence threshold + ChangeSet review still apply |
| E2 | ModelSummary sizing | **Token-budget depth expansion** (default **8000 tokens**): add levels top-down until budget exhausted; drill-down via MCP tools beyond that — not fixed per-package caps |
| E3 | Scout bounds | **10** rounds, **1000** file reads, **50** MCP calls per run (large-PR scale; config-overridable) |
| E4 | Bootstrap wipe mechanism | **Single bulk wipe** before filesystem scan — fast, auditable in ChangeSet, revertible via rollback/time-travel |

### ModelSummary algorithm (normative)

```
BUDGET = 8000 tokens  # config: model_summary_token_budget
REM = BUDGET
summary = []

for level in TOP_LEVEL, NEXT_LEVEL, ...:   # derived from graph hierarchy
    chunk = serialize(level)               # e.g. L0 totals, L1 package rollups, L2 element names
    X = count_tokens(chunk)
    if X >= REM: break                     # REM "close to 0" — stop; use tools for deeper detail
    summary.append(chunk)
    REM -= X

prompt += join(summary)
if REM small and more levels exist:
    prompt += "Use list_elements / get_element / search / traverse for deeper detail."
```
