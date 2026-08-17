# Heimdall — Product Requirements Document

**Version:** 0.1-draft
**Date:** 2026-08-13
**Status:** Draft — pending Gate A approval
**Authors:** FeatureFactory CTO

---

## 1. Mission

Heimdall is the AI-native active telemetry layer of the FeatureFactory platform. It watches enterprise infrastructure continuously, responds to incidents autonomously, drives continuous improvement proactively, and — in both modes — captures what it learns as Playbook Improvement Proposals (PIPs) that make the entire organisation smarter over time.

Where Huginn asks *"how is the team performing?"* and Yggdrasil asks *"what does the system look like?"*, Heimdall asks *"what is happening right now, why, and what should we do about it?"*

Named after the Norse watchman-god who stands at the edge of all nine worlds, sees everything before it reaches Asgard, and guards Bifröst — the bridge between realms. Nothing reaches the agents without passing through Heimdall first.

---

## 2. Problem

Modern engineering organisations generate enormous telemetry volume and almost no telemetry *meaning*. Alarms fire without context. Incidents drag on because no one knows which deployment caused what. Dashboards exist; understanding does not.

AI agents are the natural solution — but they fail on the same problem: without structured context (who owns this service, what changed, what does this depend on), agents chase statistical ghosts and produce confident wrong answers.

Heimdall solves both halves simultaneously:
- It gives humans a system that explains itself instead of reporting at them.
- It gives AI agents the structured context they need to reason correctly.
- It closes the loop: every incident and every improvement becomes a PIP that updates the playbooks agents and humans read next time.

---

## 3. Personas

| Persona | Role | What they need from Heimdall |
|---|---|---|
| **Platform Engineer / SRE** | Responds to incidents, manages infra | Faster MTTR; automated first-response; full trace context without digging |
| **Engineering PM** | OODA loop via Huginn | Runtime health feed alongside development metrics; incidents resolved surfaced as outcomes |
| **Tech Lead / Architect** | Owns service quality and infra evolution | Continuous improvement proposals; predicted SLO breaches; CDK/SAM PRs to review |
| **AI Agent** (Munin, Gjallarhorn, Ratatosk) | First-class consumer of SCI | Structured context packages — never raw CloudWatch |

---

## 4. Core Concepts

**Active Telemetry.** Telemetry that self-describes (carries meaning, not just metrics), adapts to context (enriched with service ownership, dependency topology, business impact), and feeds forward (linking cause and effect to guide decisions).

**Synthetic Context Interface (SCI).** The API layer Heimdall exposes to agents and humans. Returns meaning-packets assembled from multiple sources — never a raw CloudWatch response. The SCI is the bridge between raw infrastructure signal and structured agent reasoning.

**CMDB ABC.** A protocol contract (`CMDBAdapter`) that Heimdall uses to read service metadata and write service state. Yggdrasil is the reference implementation. AWS Service Catalog and any other CMDB implement the same contract. Heimdall has no hard dependency on Yggdrasil.

**Playbook Improvement Proposal (PIP).** Mimir's versioned change mechanism for locked playbooks. When Heimdall resolves an incident or detects a recurring pattern, it creates a PIP against the relevant runbook or workflow in Mimir — proposing a concrete update. PIPs are reviewed and merged like code PRs, making the organisation's shared knowledge improve with every event Heimdall handles.

**Autonomy Threshold.** A configurable per-environment policy that determines which actions Heimdall executes autonomously versus proposes for human approval. Ranges from `observe-only` (no autonomous action) through `propose` (Jira tickets + PRs only) to `autonomous` (executes within defined blast radius limits). Default: `propose`.

---

## 5. Operating Modes

Heimdall runs continuously in both modes simultaneously. They share the same signal pipeline and SCI but differ in trigger, cadence, and outcome.

---

### 5.1 Incident Response Mode

**Trigger:** A signal breach — 5xx spike, CloudWatch alarm, SLO burn rate exceeding threshold, or anomaly detected by the enrichment pipeline.

**Goal:** Minimise MTTR. Identify root cause, act within the autonomy threshold, and capture learnings.

#### Flow

```
Signal breach detected
  → SCI assembles context package
      (service owner · recent deploys · upstream deps · X-Ray trace · error log lines)
  → Heimdall Agent: root cause hypothesis
  → selects response from toolbox
  → executes or proposes (per autonomy threshold)
  → monitors resolution signal
  → incident closed
  → PIP generated → submitted to Mimir
  → incident state written back to CMDB (service state: degraded → healthy)
  → event emitted to Huginn feed
```

#### Agent Toolbox — Incident Mode

| Tool | Description | Autonomy gate |
|---|---|---|
| `get_trace(traceId)` | X-Ray `BatchGetTraces` + scoped Logs Insights | None — read-only |
| `get_service_context(service, window)` | SCI context package | None — read-only |
| `rollback_deployment(deploy_id)` | Triggers CodeDeploy rollback | Threshold: `autonomous` |
| `scale_service(service, config)` | ECS/EB scaling adjustment | Threshold: `autonomous` |
| `update_config(service, key, value)` | SSM Parameter Store update | Threshold: `autonomous` |
| `create_pr(repo, branch, diff, description)` | Opens a GitHub PR with a proposed code fix | Threshold: `propose` |
| `create_jira_ticket(project, summary, detail, assignee)` | Sends task to human via Jira | Threshold: `propose` |
| `update_service_state(service_id, state)` | Writes current health back to CMDB | Always |
| `submit_pip(playbook_id, proposal)` | Creates a PIP in Mimir against the relevant runbook | Always (post-incident) |

#### Incident Resolution Criteria

Heimdall monitors the signal that triggered the incident. Resolution is declared when:
- The triggering metric returns below threshold for a configurable hold-off window (default: 10 minutes), OR
- A human marks the incident resolved in Jira / the CMDB.

---

### 5.2 Continuous Improvement Mode

**Trigger:** Scheduled — sliding window analysis runs on a configurable cadence (default: daily). Also triggered ad-hoc by an agent or human via the SCI.

**Goal:** Detect degradation trends before they become incidents, predict SLO breaches, propose infrastructure and process improvements, and keep the system fit.

#### Flow

```
Scheduled window opens (default: 24h rolling)
  → Athena queries over enriched event history
  → Heimdall Agent: trend analysis across services
      - SLO burn rate trajectories
      - error rate drift
      - latency percentile shifts
      - cost anomalies
      - capacity headroom
  → predictions generated (horizon: configurable, default 7 days)
  → improvement proposals produced:
      - CDK/SAM PRs for infra changes
      - Jira tickets for human-owned improvements
      - Mimir PIPs for process/runbook improvements
  → findings written to CMDB service state
  → summary event emitted to Huginn feed
```

#### Agent Toolbox — Continuous Improvement Mode

All incident-mode read tools, plus:

| Tool | Description | Autonomy gate |
|---|---|---|
| `query_history(service, metric, window)` | Athena query over enriched Parquet events | None — read-only |
| `get_slo_burn_rate(service, window)` | SLO burn rate trend with projected breach date | None — read-only |
| `predict_capacity(service, horizon)` | Capacity headroom projection | None — read-only |
| `create_infra_pr(stack, change, description)` | Opens GitHub PR with CDK/SAM change proposal | Threshold: `propose` |
| `create_jira_ticket(...)` | Sends improvement task to human | Threshold: `propose` |
| `submit_pip(playbook_id, proposal)` | Creates PIP in Mimir against relevant workflow/activity | Always |
| `update_service_state(service_id, forecast)` | Writes predicted state + risk level to CMDB | Always |

---

## 6. Signal Ingestion

Heimdall ingests from the following suppliers. All event-push flows use **EventBridge → SNS → SQS → SAM Lambda**. On-demand query flows are called directly by the SCI at request time.

| Supplier | Signal | Flow |
|---|---|---|
| CloudWatch Alarms | Threshold breaches | SNS → SQS (event push) |
| CloudWatch Logs | ERROR/WARN events only (subscription filter) | Firehose → S3 hot (event push) |
| X-Ray / OTEL | Full distributed traces | `BatchGetTraces(traceId)` on demand |
| CloudWatch Logs Insights | Scoped log lines by traceId | Query on demand, scoped to service + window |
| CodePipeline / CodeDeploy | Deployment events | EventBridge → SQS (event push) |
| CloudTrail / Config | API audit, config drift | EventBridge → SQS (event push) |
| GitHub webhooks | Commits, PRs, merges | API Gateway → SQS (event push) |
| Cost Explorer | Spend anomalies | Scheduled Lambda poll |
| Huginn (via API) | Master Variables per service team | Scheduled Lambda poll |

**Log retention policy:**

| Tier | Store | Retention | Contents |
|---|---|---|---|
| Hot | S3 | 24h | Full application logs — safety net for trace gaps |
| Warm | S3 | 7d | ERROR-filtered events, enriched |
| Cold | S3 Parquet + Athena | 90d | All enriched events, queryable |

**Prerequisite:** Structured JSON logging with `traceId` (X-Amzn-Trace-Id) propagated across all services. Without this, `get_trace()` breaks and incident bisection degrades to log grep.

---

## 7. Context Enrichment

Every event that enters the enrichment Lambda receives a meaning-packet before storage or SCI delivery:

```
{
  "who":      // CMDB: owner, team, on-call
  "where":    // CMDB: upstream deps, environment, package, topology position
  "why":      // inferred: recent deploy on same service? known anomaly pattern?
  "impact":   // CMDB: SLO class, business capability affected, user-facing?
}
```

The CMDB adapter is called on the hot path. A 5-minute ElastiCache TTL shields the CMDB from enrichment Lambda volume.

**Adaptive fidelity:** A DynamoDB `heimdall_state` table holds a `mode` flag per environment: `normal | elevated | incident`. Enrichment Lambdas check this flag on each invocation to adjust filtering aggressiveness. Flag is set on incident open, cleared on resolution.

---

## 8. Synthetic Context Interface (SCI)

Lambda functions behind API Gateway. **Agents and humans call these — never CloudWatch, X-Ray, or Athena directly.**

| Tool | Composes from | Returns |
|---|---|---|
| `get_service_context(service_id, window)` | CMDB (owner, deps, SLO) + Athena (recent anomalies) + live enriched stream | Health + deploy history + ownership + upstream impact |
| `get_anomaly_context(anomaly_id)` | CMDB (topology) + Athena (similar past events) + Logs Insights | Signal + ranked probable causes + runbook refs |
| `get_release_impact(deploy_id)` | CMDB (affected services) + CloudWatch metric delta | What changed, affected services, current delta |
| `get_trace(trace_id)` | X-Ray `BatchGetTraces` + scoped Logs Insights | Full call chain + log content at error site |
| `get_slo_status(service_id)` | Athena (burn rate) + CMDB (SLO definition) | Current burn rate, projected breach, error budget remaining |
| `list_active_incidents()` | DynamoDB `heimdall_state` | All open incidents with severity and current hypothesis |

---

## 9. CMDB Integration

Heimdall reads service context and writes service state through a protocol abstraction — it has no direct dependency on any specific CMDB.

### CMDBAdapter Contract

```python
class CMDBAdapter(Protocol):
    def list_services(self) -> list[ServiceRecord]: ...
    def get_service(self, service_id: str) -> ServiceRecord: ...
    def get_releases(self, service_id: str, since: datetime) -> list[ReleaseRecord]: ...
    def update_service_state(self, service_id: str, state: ServiceState) -> None: ...
```

### ServiceRecord

```python
@dataclass
class ServiceRecord:
    id: str
    name: str
    owner_team: str
    on_call: str
    slo: SLODefinition
    dependencies: list[str]      # service IDs
    environment: str
    tech_stack: list[str]
    business_capability: str
```

### Provided Implementations

| CMDB | Implementation | Notes |
|---|---|---|
| **Yggdrasil** | `YggdrasilCMDBAdapter` | Reference implementation. Calls `/api/v1/` REST endpoints using a PAT. Writes state via `propose_changeset`. |
| **AWS Service Catalog** | `AWSServiceCatalogAdapter` | Reads from Service Catalog portfolios and products. State written as resource tags. |

Any CMDB with an API can implement `CMDBAdapter`. The adapter is selected via config (`HEIMDALL_CMDB_PROVIDER`).

---

## 10. Mimir Integration — PIPs

After every incident resolution and after every continuous improvement cycle, Heimdall submits a **Playbook Improvement Proposal** to Mimir via its MCP interface.

### PIP Content

A PIP targets a specific Mimir playbook activity (e.g., *"Incident Response: Payment Service"*, *"Deployment Runbook: Checkout API"*) and proposes a concrete update:

```
Title:        "Add canary traffic check before full rollout — payment-service"
Playbook:     FeatureFactory / Incident Response
Activity:     Deployment Verification
Trigger:      Incident INC-2026-0847 — latency spike traced to full rollout
              without canary validation
Root cause:   Deploy v2.4.1 shipped to 100% traffic immediately; no canary phase
Proposed change:
  Add step: "Verify < 1% error rate on 10% canary traffic for 5 min before
  promoting to 100%."
Evidence:     X-Ray trace heimdall://traces/abc123, Athena query results attached
Confidence:   high (same pattern observed in 3 of last 5 incidents on this service)
```

PIPs are submitted programmatically via Mimir's MCP `submit_pip` tool. Mimir gates them through its standard review process before they update the locked playbook. Human review is always required — Heimdall proposes, humans approve.

---

## 11. Huginn Feed

Heimdall exposes a REST API endpoint that Huginn polls at its configured interval (default: every sync cycle, typically hourly).

### `GET /api/v1/feed/application-health/`

Returns current application health per service, queryable by project/team scope.

```json
{
  "as_of": "2026-08-13T14:32:00Z",
  "services": [
    {
      "service_id": "payment-service",
      "team": "payments",
      "health": "degraded",
      "active_incidents": 1,
      "slo_burn_rate": 0.72,
      "error_budget_remaining_pct": 28,
      "last_deploy": "2026-08-13T11:15:00Z",
      "last_deploy_id": "deploy-v2.4.1"
    }
  ],
  "incidents_resolved_since": "2026-08-12T14:32:00Z",
  "incidents": [
    {
      "id": "INC-2026-0847",
      "service_id": "payment-service",
      "opened_at": "2026-08-12T16:20:00Z",
      "resolved_at": "2026-08-12T17:05:00Z",
      "mttr_minutes": 45,
      "root_cause": "Deploy v2.4.0 — missing canary phase",
      "resolution": "Rollback to v2.3.9 via Heimdall automated rollback",
      "pip_submitted": true
    }
  ]
}
```

Huginn maps this feed into its Master Variable computation — specifically QUALITY and TRANSPARENCY — and surfaces it in SitReps and OODA context.

---

## 12. Autonomy Model

The autonomy threshold is configured per environment and per action category. It is not a single global toggle.

| Level | Behaviour |
|---|---|
| `observe` | No autonomous action. All findings surfaced as read-only context to the SCI. |
| `propose` | Creates PRs and Jira tickets. No direct infrastructure changes. *Default.* |
| `autonomous` | Executes within defined blast radius limits (rollbacks, scaling, config). Creates PRs for code changes regardless of threshold. Requires explicit opt-in per environment. |

**Blast radius limits (autonomous mode):**
- Rollbacks: only to the immediately preceding deploy; no multi-step rollbacks without human confirmation.
- Scaling: within ±50% of current capacity; no scale-to-zero.
- Config changes: only to parameters tagged `heimdall-managed=true` in SSM.
- Code changes: always via PR regardless of threshold — Heimdall never merges directly.

---

## 13. Infrastructure Footprint

Heimdall is deployed as a separate CDK stack (`HeimdallStack`) in the same AWS account as the FeatureFactory platform. It does not run inside Huginn or Yggdrasil.

```
HeimdallStack
  ├── EventBridge rules (per supplier)
  ├── SNS topics (infra / deploy / code / cost)
  ├── SQS queues + DLQs (one per topic)
  ├── SAM Lambda functions
  │   ├── enrichment/          # attaches meaning packets
  │   ├── sci/                 # SCI endpoint handlers
  │   ├── incident_agent/      # incident response orchestrator
  │   ├── improvement_agent/   # continuous improvement orchestrator
  │   └── feed/                # Huginn feed endpoint
  ├── API Gateway (SCI + Huginn feed)
  ├── S3 buckets (hot / warm / cold with lifecycle rules)
  ├── Kinesis Firehose (CW Logs subscription filter → S3 hot)
  ├── Athena workgroup + named queries
  └── DynamoDB (heimdall_state: mode flag, active incidents, ElastiCache invalidation)

Shared with platform (via DataStack):
  ├── Neptune (context graph — Yggdrasil's static/dynamic model + Heimdall's state edges)
  └── ElastiCache Redis (separate key namespace: heimdall:*)
```

Tech stack: Python, AWS SAM, CDK (Python). No Django. No Celery. Lambda-native.

---

## 14. Integration Map

```
CloudWatch / X-Ray / CodePipeline / CloudTrail / GitHub / Cost Explorer
    ↓ (event push or on-demand query)
Heimdall Enrichment Pipeline
    ↓ (reads context)           ↑ (writes state)
CMDB Adapter (Yggdrasil / AWS SC / any)
    ↓ (enriched signal)
Synthetic Context Interface (SCI)
    ↓ (context packages)
Heimdall Agents (Incident / Continuous Improvement)
    ↓                    ↓                    ↓                    ↓
GitHub PRs          Jira tickets         Mimir PIPs          CMDB state update
                                              ↓
                                    Huginn feed (pull)
```

---

## 15. Out of Scope — MVP

- Multi-cloud (Azure Monitor, GCP Cloud Operations). AWS-only for MVP.
- Real-time streaming dashboard UI. SCI is the interface; no Heimdall-native GUI in MVP.
- ML-based anomaly detection. Rule-based thresholds + LLM reasoning in MVP; embedding-based anomaly detection deferred.
- Heimdall managing its own telemetry (meta-observability). Covered by standard CloudWatch on the Lambda/API Gateway layer.
- Slack/Teams notifications. Jira is the human task interface in MVP.
- Autonomous code merges. Heimdall creates PRs; humans merge.

---

## 16. Open Questions

| # | Question | Owner | Due |
|---|---|---|---|
| OQ-1 | Which Mimir playbook(s) receive PIPs first — a dedicated "Heimdall Operations" playbook or existing service runbooks? | Denis | Gate A |
| OQ-2 | What is the right default hold-off window for incident resolution declaration? 10 minutes may be too short for some SLOs. | Platform Eng | Sprint 1 |
| OQ-3 | Does the Huginn feed need authentication (PAT), or is it internal-network-only? | Denis | Gate A |
| OQ-4 | AWS Service Catalog adapter — is this needed for MVP or deferred? (Yggdrasil adapter is sufficient for internal use.) | Denis | Gate A |
| OQ-5 | Blast radius limits for autonomous mode — are the ±50% scaling limits and `heimdall-managed` SSM tag convention acceptable to the platform team? | Platform Eng | Sprint 1 |

---

*Gate A: this document requires explicit approval before DTA (Design & Technical Architecture) begins.*
