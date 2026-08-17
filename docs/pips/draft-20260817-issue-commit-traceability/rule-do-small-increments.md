# Rule: Small Increments

Work in method-by-method steps.
- Implement small vertical slices.
- After every change: write → run → test → evaluate → fix.
- No large PRs or 1000-line commits.

## When GitHub issue #N is active

Small increments apply to **git commits and issue updates together** (see rule `do-github-issues`):
- One commit per **plan slice** — not one commit per wave or feature.
- After each slice commit: `gh issue comment N` with short SHA, what changed, next slice.
- Commit footer: **`Refs #N`** on every slice; **`Closes #N`** only on the final slice.
- Do not start slice N+1 until commit + issue comment for slice N are done.
