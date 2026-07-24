Feature: AUTH-TOKEN-1 API Token Management
  As a Software Architect (Priya)
  I want to generate and manage personal access tokens
  So that I can authenticate Ratatosk CLI and MCP clients without a browser session

  # Screen: AUTH-TOKEN-1
  # Real URL: /auth/tokens/
  # Testids: auth-token-page, generate-token-btn, token-row-{pk}, revoke-token-{pk},
  #          token-name-input, token-value, create-token-submit
  # Fixture: factories (tokens created per-scenario via TokenService)

  Background:
    Given the user is logged in as "architect"

  Scenario: AUTH-TOKEN-1-01 Token page renders with generate button
    When I GET "/auth/tokens/"
    Then the response status is 200
    And the element "auth-token-page" should be visible
    And the element "generate-token-btn" should be visible

  Scenario: AUTH-TOKEN-1-02 Token page shows existing tokens
    Given the user has a token named "laptop-ratatosk" with scope "read-write"
    And the user has a token named "cursor-mcp" with scope "read-only"
    When I GET "/auth/tokens/"
    Then the response status is 200
    And the user should see "laptop-ratatosk"
    And the user should see "cursor-mcp"
    And the user should see "read-write"
    And the user should see "read-only"

  Scenario: AUTH-TOKEN-1-03 Each token row has a revoke action
    Given the user has a token named "laptop-ratatosk" with scope "read-write"
    When I GET "/auth/tokens/"
    Then the response status is 200
    And the user should see "revoke-token-"

  Scenario: AUTH-TOKEN-1-04 Generate token modal has name and scope fields
    When I GET "/auth/tokens/"
    Then the response status is 200
    And the element "token-name-input" should be visible
    And the element "create-token-submit" should be visible

  Scenario: AUTH-TOKEN-1-05 Generating a token shows the raw value once
    When I POST "/auth/tokens/create/" with name "ci-bot" and scope "read-write"
    Then the response status is 200
    And the element "new-token-banner" should be visible
    And the element "token-value" should be visible
    And the user should see "ci-bot"

  Scenario: AUTH-TOKEN-1-06 Page shows CLI usage snippets for Ratatosk and MCP
    When I GET "/auth/tokens/"
    Then the response status is 200
    And the user should see "pip install ratatosk"
    And the user should see "YGGDRASIL_TOKEN"

  Scenario: AUTH-TOKEN-1-07 User menu is visible with API Access link
    When I GET "/auth/tokens/"
    Then the response status is 200
    And the element "user-menu" should be visible
    And the element "nav-settings" should be visible

  Scenario: AUTH-TOKEN-1-08 Unauthenticated access redirects to login
    Given the user is not authenticated
    When I GET "/auth/tokens/"
    Then the response status is 302

  Scenario: AUTH-TOKEN-1-09 Each usage snippet block has a copy-to-clipboard button
    When I GET "/auth/tokens/"
    Then the response status is 200
    And the element "snippet-copy-shell" should be visible
    And the element "snippet-copy-ratatosk" should be visible
    And the element "snippet-copy-ratatosk-remote" should be visible
    And the element "snippet-copy-mcp-stdio" should be visible

  Scenario: AUTH-TOKEN-1-10 After generating a token, snippets show the real token value
    When I POST "/auth/tokens/create/" with name "ci-bot" and scope "read-write"
    Then the response status is 200
    And the element "new-token-banner" should be visible
    And the element "snippet-copy-shell" should be visible
    And the user should see "export YGGDRASIL_TOKEN="
