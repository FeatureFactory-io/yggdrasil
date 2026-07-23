@wip
Feature: ACT-1-SCOUT Ratatosk bounded scout loop
  As a Development Team Lead (Marcus)
  I want Ratatosk update to plan and gather evidence beyond stdin
  So that commit messages and diffs trigger targeted file reads and MCP lookups

  # Update-only: stdin triggers scout; bootstrap uses filesystem scan instead.
  # Bounds (defaults): 10 rounds, 1000 file reads, 50 MCP calls.
  # Reference: docs/features/user_journey.md Act 6; SAO §17.3.

  Scenario: ACT-1-SCOUT-01 Scout plan records evidence intents on blackboard
    Given the Metamodel "c4" exists with C4 stereotypes and packages
    And the Yggdrasil model "Yggdrasil" exists
    And the stdin fixture "pr.diff" is available
    When Marcus pipes the stdin fixture "pr.diff" into ratatosk update with repo "./repo"
    Then the run blackboard contains step "scout_plan"
    And the run blackboard contains key "evidence_plan"

  Scenario: ACT-1-SCOUT-02 Scout reads local files from --repo
    Given the Metamodel "c4" exists with C4 stereotypes and packages
    And the Yggdrasil model "Yggdrasil" exists
    And the fixture repository "sample_webapp" is available
    And the stdin fixture "pr.diff" is available
    When Marcus pipes the stdin fixture "pr.diff" into ratatosk update with repo from fixture "sample_webapp"
    Then the run blackboard tool_calls include source "local"
    And the run blackboard tool_calls include action "read_file"

  Scenario: ACT-1-SCOUT-03 Scout probes Yggdrasil MCP for existing elements
    Given the Metamodel "c4" exists with C4 stereotypes and packages
    And the Yggdrasil model "Yggdrasil" exists with element "Payment API" stereotype "Container"
    And the stdin fixture "pr.diff" is available
    When Marcus pipes the stdin fixture "pr.diff" into ratatosk update with repo "./repo"
    Then an MCP tool call to "search" or "get_element" was recorded on the blackboard

  @wip
  Scenario: ACT-1-SCOUT-04 Scout optionally fetches linked issue via Atlassian MCP
    Given the Metamodel "c4" exists with C4 stereotypes and packages
    And the Yggdrasil model "Yggdrasil" exists
    And Ratatosk config allows connector "mcp.atlassian"
    When Marcus pipes commit message stdin into ratatosk update with repo "./repo":
      """
      feat(llm.planner): add planning #MIM-056
      """
    Then the run blackboard tool_calls include connector "mcp.atlassian"
    And the run blackboard sources include issue key "MIM-056"

  Scenario: ACT-1-SCOUT-05 Element candidates carry provenance from scout sources
    Given the Metamodel "c4" exists with C4 stereotypes and packages
    And the Yggdrasil model "Yggdrasil" exists
    And the stdin fixture "pr.diff" is available
    When Marcus pipes the stdin fixture "pr.diff" into ratatosk update with repo "./repo"
    Then every element candidate has provenance source recorded
    And a ChangeSet with source "ratatosk" exists
