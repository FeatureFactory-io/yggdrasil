# Yggdrasil — MIN Execution Guide

This file is read by the MIN (implementation) agent at the start of every
session. It configures how MIN implements scenarios from the active iteration
manifest. AGENTS.md is the permanent project guide; this file is the
iteration-scoped execution contract.

---

## Iteration Protocol

1. At session start, read the active manifest:
   `docs/plans/iterations/ITER-*.yaml` (most recent by filename date).
2. Find the first scenario with `status-queued` on its GitHub issue (Milestone #N).
3. Apply BPE-02 → BPE-05 for that scenario (context map → skeleton → red → green → refactor).
4. Mark the issue `status-in-progress` by adding the label via `gh issue edit`.
5. On checkpoint PASS, close the issue with `status-done` label and post a comment.
6. On checkpoint FAIL (first attempt): retry once with a targeted fix (absorbed drift).
7. On checkpoint FAIL (second attempt): post a comment with `status-blocked` label and stop.
8. Repeat from step 2 until all `status-queued` issues in the milestone are closed.

<!-- MANIFEST -->
Active manifest: docs/plans/iterations/ITER-20260717-1300-act-0-agents-mcp.yaml
Milestone: #2 — ITER-20260717 | Agents + MCP
Branch: iteration/20260717-agents-mcp
<!-- /MANIFEST -->

---

## Drift Handling

| Drift type           | Action                                                                 |
|---------------------|------------------------------------------------------------------------|
| checkpoint_fail     | Retry once with targeted fix; escalate if second attempt also fails    |
| footprint_violation | STOP — post `status-blocked`; do not add files outside the footprint   |
| method_explosion    | STOP — extract helpers first, get human approval, then continue         |
| sao_violation       | STOP — post `status-blocked`; surface the SAO section violated          |
| checkpoint_fail_after_retry | STOP — post detailed `status-blocked` comment with failure log |

---

## Session Resume Protocol

At session start:
1. Run `git status` — confirm on branch `iteration/YYYYMMDD-*`.
2. Check for any `status-in-progress` issues on the active milestone.
3. If found: re-run the checkpoint for that scenario.
   - PASS: close issue (`status-done`), continue.
   - FAIL: treat as first retry (absorbed); if fails again, escalate.
4. If no in-progress found: pick next `status-queued` issue and proceed.

---

## Authority Model

MIN has authority to:
- Write/edit files within the declared `codebase_footprint` of the active scenario.
- Run `uv run`, `git`, `gh` commands.
- Create migrations, add/remove imports.

MIN does NOT have authority to:
- Add new Django apps (new top-level app directories).
- Modify `pyproject.toml`, `settings.py`, or `urls.py` (root) without first
  posting a `status-blocked` comment and awaiting human approval.
- Remove or rename existing tests.
- Skip the checkpoint — every scenario must pass its checkpoint before closing.
