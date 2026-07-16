# Cursor Hooks

## sync-feature-spec

Enforces the **Spec vs Runner** policy (`docs/architecture/test-architecture.md` §4).

| Event | Behavior |
|---|---|
| `afterFileEdit` / `afterTabFileEdit` | After editing a `.feature` in `docs/features/` or `features/at|e2e/`, checks whether a **promoted twin** exists and drifted |
| `postToolUse` (Write/StrReplace/EditNotebook) | Same check; also returns `additional_context` when drift is detected (Cursor 3.9.8+) |
| `stop` | If drift was recorded this session, auto-submits a `followup_message` asking the agent to sync both copies |

**Warn-only:** no auto-copy. Specs without a promoted runner are ignored.

Runtime state: `.cursor/hooks/.feature-sync-state.json` (gitignored).
