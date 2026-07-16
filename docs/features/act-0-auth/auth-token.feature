Feature: AUTH-TOKEN-1 API Token Management
  As a Software Architect (Priya)
  I want to generate and manage personal access tokens
  So that I can authenticate Ratatosk CLI and MCP clients without a browser session

  # Screen: AUTH-TOKEN-1
  # Mockup: /mockups/auth/token/
  # Testids: auth-token-page, generate-token-btn, token-row-{id}, revoke-token-{id},
  #          token-name-input, token-value, create-token-submit
  # Fixture: seed.json (priya@example.com / test-pass-only-1234)
  # Mock data: 2 existing tokens — laptop-ratatosk (read-write), cursor-mcp (read-only)

  Background:
    Given the user is logged in as "architect"

  Scenario: AUTH-TOKEN-1-01 Token page renders with existing tokens and generate button
    When I GET "/mockups/auth/token/"
    Then the response status is 200
    And the element "auth-token-page" should be visible
    And the element "generate-token-btn" should be visible
    And the user should see "laptop-ratatosk"
    And the user should see "cursor-mcp"
    And the user should see "read-write"
    And the user should see "read-only"

  Scenario: AUTH-TOKEN-1-02 Token table shows 2 existing tokens with all required columns
    When I GET "/mockups/auth/token/"
    Then the response status is 200
    And the element "token-row-1" should be visible
    And the element "token-row-2" should be visible
    And the user should see "laptop-ratatosk"
    And the user should see "2026-06-01"
    And the user should see "2026-07-14"

  Scenario: AUTH-TOKEN-1-03 Each token row has a revoke action
    When I GET "/mockups/auth/token/"
    Then the response status is 200
    And the element "revoke-token-1" should be visible
    And the element "revoke-token-2" should be visible

  Scenario: AUTH-TOKEN-1-04 Generate token modal has name and scope fields
    When I GET "/mockups/auth/token/"
    Then the response status is 200
    And the element "token-name-input" should be visible
    And the element "create-token-submit" should be visible
    And the user should see "laptop-ratatosk"
    And the user should see "read-write"
    And the user should see "read-only"

  Scenario: AUTH-TOKEN-1-05 Generate token form requires a name
    When I GET "/mockups/auth/token/"
    Then the response status is 200
    And the element "token-name-input" should be visible
    # Required attribute enforced in HTML; TFK-07 for validation scenario when form ships

  Scenario: AUTH-TOKEN-1-06 Page shows CLI usage snippets for Ratatosk and MCP
    When I GET "/mockups/auth/token/"
    Then the response status is 200
    And the user should see "pip install ratatosk"
    And the user should see "YGGDRASIL_TOKEN"

  # ── Navbar integration ─────────────────────────────────────────────────────
  # AUTH-TOKEN-1 is reached via Settings → API Access from user menu.
  Scenario: AUTH-TOKEN-1-07 Settings nav link is visible in user menu
    When I GET "/mockups/auth/token/"
    Then the response status is 200
    And the element "nav-settings" should be visible
    And the element "user-menu" should be visible
