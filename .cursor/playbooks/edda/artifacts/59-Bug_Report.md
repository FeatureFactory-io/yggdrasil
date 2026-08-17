# Bug Report

**Artifact ID**: 59
**Type**: Document
**Required**: True

## Description

OUTPUT: GitHub Issue created by `report_bug` MCP tool or Feedback UI (`BugReportService.submit_bug`).

Produced when a defect is filed during Check Definition of Done (#101), Finalize Feature (#102), or Acceptance, Bug Reports & Deploy Fixes (#183).

## Issue body structure (authoritative)

```markdown
## Description

{free-text bug description — for MIN-06 include title, steps, expected vs actual, severity, log excerpts}

## Reproduction

- **Source**: `ui` | `mcp`
- **Page URL**: `{url when from UI}`

### Page / assistant context (MCP)

{page_context when from MCP}

### Form / field snapshot (sanitized)

{JSON snapshot or "_No form snapshot provided._"}

## Environment

- **App version**: `{MIMIR_GIT_REVISION}`
- **MIMIR_ENV**: `{env}`
- **Reported at (UTC)**: `{ISO8601 timestamp}`

## Reporter

- **Email**: `{reporter_email}`
```
