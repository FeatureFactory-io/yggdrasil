## Orient Summary — 2026-07-16

### Target
Act: act-0-auth
Feature files:
- docs/features/act-0-auth/auth-login.feature
- docs/features/act-0-auth/auth-token.feature

### Scenarios in Scope
- S01: AUTH-LOGIN-1-01 Login page renders with email, password, and sign-in button
- S02: AUTH-LOGIN-1-02 Successful sign-in with architect credentials redirects to View Browser
- S03: AUTH-LOGIN-1-03 Login page shows admin-provisioned account notice
- S04: AUTH-LOGIN-1-04 Authenticated architect is redirected to View Browser (direct URL)
- S05: AUTH-LOGIN-1-05 Unauthenticated user is redirected to login for protected pages (spec-only, no executable steps yet)
- S06: AUTH-TOKEN-1-01 Token page renders with existing tokens and generate button
- S07: AUTH-TOKEN-1-02 Token table shows 2 existing tokens with all required columns
- S08: AUTH-TOKEN-1-03 Each token row has a revoke action
- S09: AUTH-TOKEN-1-04 Generate token modal has name and scope fields
- S10: AUTH-TOKEN-1-05 Generate token form requires a name
- S11: AUTH-TOKEN-1-06 Page shows CLI usage snippets for Ratatosk and MCP
- S12: AUTH-TOKEN-1-07 Settings nav link is visible in user menu

### Scenarios Deferred
None

### Velocity Trend
First iteration — no history

### Dominant Drift
None — first iteration

### Scope Validation
- S01–S04, S06–S12: all test mockup views via Django test client (GET + assertion). Mockup
  templates, URL routes, and step library are already implemented. Skeleton work centres on
  the real auth app (models, views, services, admin) and confirming the AT runner can execute
  the scenarios end-to-end once @wip tags are removed.
- S05: no executable When/Then steps (TFK-07 placeholder). Skeleton notes redirect intent;
  scenario passes vacuously until the real login view ships.
- No scope risks. 12 scenarios, simple HTTP GET assertions against mockup. No cross-cutting
  infrastructure beyond Django's built-in auth.
