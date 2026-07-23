@wip
Feature: ACT-1-MSUM Ratatosk ModelSummary
  As a Software Architect (Priya)
  I want Ratatosk to inject a token-budget graph summary into prompts
  So that the LLM has model context without unbounded graph-in-prompt

  # Default budget: 8000 tokens (config: model_summary_token_budget).
  # Algorithm: depth-expanded levels until budget exhausted; drill-down via MCP tools.
  # Full snapshot remains in code for reconcile — not copied into prompt field.

  Scenario: ACT-1-MSUM-01 Bootstrap builds ModelSummary before extract
    Given the Metamodel "c4" exists with C4 stereotypes and packages
    And the Yggdrasil model "Yggdrasil" exists with 50 elements
    And the fixture repository "sample_webapp" is available
    When Priya runs ratatosk bootstrap against the fixture repository "sample_webapp"
    Then the run blackboard contains key "model_summary_chars"
    And the prompt stack does not contain full graph JSON

  Scenario: ACT-1-MSUM-02 ModelSummary includes L0 totals and L1 package rollups
    Given the Metamodel "c4" exists with C4 stereotypes and packages
    And the Yggdrasil model "Yggdrasil" exists with elements in packages "Technology" and "Application"
    When Ratatosk builds ModelSummary for model "Yggdrasil" with budget 8000
    Then the ModelSummary contains level "L0" totals
    And the ModelSummary contains package rollup "Technology"

  Scenario: ACT-1-MSUM-03 Budget exhaustion stops before L3 detail
    Given the Metamodel "c4" exists with C4 stereotypes and packages
    And the Yggdrasil model "Yggdrasil" exists with 500 elements
    When Ratatosk builds ModelSummary for model "Yggdrasil" with budget 8000
    Then the ModelSummary stops before all element names are listed
    And the prompt guidance mentions "list_elements"

  Scenario: ACT-1-MSUM-04 Scout uses list_elements when summary is insufficient
    Given the Metamodel "c4" exists with C4 stereotypes and packages
    And the Yggdrasil model "Yggdrasil" exists with 200 elements
    And the stdin fixture "pr.diff" is available
    When Marcus pipes the stdin fixture "pr.diff" into ratatosk update with repo "./repo"
    Then an MCP tool call to "list_elements" was recorded on the blackboard
    And the run blackboard prompt_field "model_summary" length is less than full snapshot size
