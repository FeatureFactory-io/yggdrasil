@wip
Feature: ACT-6-CICD Ratatosk CI/CD Update
  As a Development Team Lead (Marcus)
  I want Ratatosk to run automatically on every merge and update the model with the diff
  So that the architecture model stays current without manual intervention

  # Act 6: Pipeline-triggered incremental update (stdin triggers bounded scout).
  # Pattern: ratatosk update — scout loop reads --repo + Yggdrasil MCP + connector MCPs.
  # Update never wipes the graph. Reference: docs/features/user_journey.md Act 6.
  # Stdin fixtures: tests/fixtures/repos/sample_stdin/

  Scenario: ACT-6-CICD-01 ratatosk update on a PR diff produces an incremental ChangeSet
    Given a GitHub Actions workflow with YGGDRASIL_TOKEN configured
    And the Metamodel "c4" exists with C4 stereotypes and packages
    And the Yggdrasil model "Yggdrasil" exists
    And the stdin fixture "pr.diff" is available
    When Marcus pipes the stdin fixture "pr.diff" into:
      """
      ratatosk update --model Yggdrasil --token=$YGGDRASIL_TOKEN
      """
    Then the exit code is 0
    And the output contains "building ModelSummary"
    And a ChangeSet with source "ratatosk" exists

  Scenario: ACT-6-CICD-02 ratatosk update with instructions focuses analysis on changed interfaces
    Given the Metamodel "c4" exists with C4 stereotypes and packages
    And the Yggdrasil model "Yggdrasil" exists
    And the stdin fixture "pr.diff" is available
    When Marcus pipes the stdin fixture "pr.diff" into:
      """
      ratatosk update --model Yggdrasil --token=$YGGDRASIL_TOKEN \
        --instructions "Focus on interface changes — any API contracts added, removed, or modified?"
      """
    Then the exit code is 0
    And the output contains "to_add:" or "to_update:"
    And unchanged elements are never sent to Munin

  Scenario: ACT-6-CICD-03 Ratatosk builds ModelSummary before scout gather
    Given the Metamodel "c4" exists with C4 stereotypes and packages
    And the Yggdrasil model "Yggdrasil" exists with 31 elements and 44 relationships
    And the stdin fixture "pr.diff" is available
    When Marcus pipes the stdin fixture "pr.diff" into ratatosk update with repo "./repo"
    Then the output contains "building ModelSummary"
    And the ChangeSet only includes elements affected by the diff
    And the output does not include "unchanged" elements in the operations list

  Scenario: ACT-6-CICD-04 Incremental update produces delta buckets without wiping graph
    Given the Metamodel "c4" exists with C4 stereotypes and packages
    And the Yggdrasil model "Yggdrasil" exists with 31 elements and 44 relationships
    And the stdin fixture "pr.diff" is available
    When Marcus pipes the stdin fixture "pr.diff" into ratatosk update with repo "./repo"
    Then the output does not contain "wiping"
    And the delta buckets contain:
      | bucket    | min_count |
      | to_add    | 0         |
      | to_update | 0         |
      | to_delete | 0         |
    And unchanged elements are never sent to Munin

  Scenario: ACT-6-CICD-05 CI pipeline links to the run result URL on completion
    Given the Metamodel "c4" exists with C4 stereotypes and packages
    And the Yggdrasil model "Yggdrasil" exists
    And the stdin fixture "pr.diff" is available
    When Marcus pipes the stdin fixture "pr.diff" into ratatosk update
    Then the exit code is 0
    And the output contains a URL to the run result
    And the URL points to RATATOSK_RUN-VIEW_RATATOSK_RUN-1 for the new run

  Scenario: ACT-6-CICD-06 Update run result is visible in RATATOSK_RUN-LIST+FIND-1
    Given a successful CI update run has just completed
    When Marcus browses to /mockups/ratatosk-run/
    Then the response status is 200
    And the most recent run shows trigger "ratatosk update"

  Scenario: ACT-6-CICD-07 ratatosk update with no relevant changes produces an empty ChangeSet
    Given the Metamodel "c4" exists with C4 stereotypes and packages
    And the Yggdrasil model "Yggdrasil" exists
    And the stdin fixture "noise-only.diff" is available
    When Marcus pipes the stdin fixture "noise-only.diff" into ratatosk update
    Then the ChangeSet has 0 operations
    And the output contains "no architecture changes detected"

  Scenario: ACT-6-CICD-08 README prose on stdin produces a delta
    Given the Metamodel "c4" exists with C4 stereotypes and packages
    And the Yggdrasil model "Yggdrasil" exists
    And the stdin fixture "architecture-notes.md" is available
    When Marcus pipes the stdin fixture "architecture-notes.md" into:
      """
      ratatosk update --model Yggdrasil --token=$YGGDRASIL_TOKEN
      """
    Then the exit code is 0
    And the run blackboard has input_mode "stdin"
    And the run blackboard has stdin kind "prose"
    And a ChangeSet with source "ratatosk" exists

  Scenario: ACT-6-CICD-09 Empty stdin yields no architecture changes
    Given the Metamodel "c4" exists with C4 stereotypes and packages
    And the Yggdrasil model "Yggdrasil" exists
    When Marcus pipes empty stdin into ratatosk update
    Then the exit code is 0
    And the output contains "no architecture changes detected"

  Scenario: ACT-6-CICD-10 Stdin over size cap fails without inventing Elements
    Given the Metamodel "c4" exists with C4 stereotypes and packages
    And the Yggdrasil model "Yggdrasil" exists
    When Marcus pipes stdin larger than the size cap into ratatosk update
    Then the exit code is not 0
    And the output contains "limit"
    And there are no orphan Elements without a ChangeSetItem

  Scenario: ACT-6-CICD-11 Missing token on update fails like bootstrap
    When Marcus pipes the stdin fixture "pr.diff" into:
      """
      ratatosk update --model Yggdrasil
      """
    Then the exit code is not 0
    And the output contains "token"

  Scenario: ACT-6-CICD-12 MCP snapshot failure mid-update creates no ChangeSet
    Given the Metamodel "c4" exists with C4 stereotypes and packages
    And the Yggdrasil model "Yggdrasil" exists
    And the stdin fixture "pr.diff" is available
    And the MCP snapshot endpoint is unreachable
    When Marcus pipes the stdin fixture "pr.diff" into ratatosk update
    Then the exit code is not 0
    And the output contains "MCP"
    And no ChangeSet with source "ratatosk" was created for this run

  Scenario: ACT-6-CICD-13 Update never writes Elements outside a ChangeSet
    Given the Metamodel "c4" exists with C4 stereotypes and packages
    And Priya has a Yggdrasil personal access token with read-write scope
    And the Yggdrasil model "Yggdrasil" exists with no elements
    And the stdin fixture "pr.diff" is available
    When Marcus pipes the stdin fixture "pr.diff" into ratatosk update
    Then a ChangeSet with source "ratatosk" exists
    And every new Element is referenced by an operation on that ChangeSet
    And there are no orphan Elements without a ChangeSetItem

  Scenario: ACT-6-CICD-14 Diff with only test-file noise yields zero ops
    Given the Metamodel "c4" exists with C4 stereotypes and packages
    And the Yggdrasil model "Yggdrasil" exists
    And the stdin fixture "noise-only.diff" is available
    When Marcus pipes the stdin fixture "noise-only.diff" into ratatosk update
    Then the ChangeSet has 0 operations
    And the output contains "no architecture changes detected"

  @wip
  Scenario: ACT-6-CICD-15 Diff removing a mapped service auto-proposes to_delete
    Given the Metamodel "c4" exists with C4 stereotypes and packages
    And the Yggdrasil model "Yggdrasil" exists with element "Legacy Service" stereotype "Container"
    And the stdin fixture "pr.diff" removes "Legacy Service" from the codebase
    When Marcus pipes the stdin fixture "pr.diff" into ratatosk update with repo "./repo"
    Then the delta buckets contain bucket "to_delete" with count at least 1
    And a ChangeSet with source "ratatosk" exists

  @wip
  Scenario: ACT-6-CICD-16 Noise-only diff must not delete existing elements
    Given the Metamodel "c4" exists with C4 stereotypes and packages
    And the Yggdrasil model "Yggdrasil" exists with 10 elements
    And the stdin fixture "noise-only.diff" is available
    When Marcus pipes the stdin fixture "noise-only.diff" into ratatosk update with repo "./repo"
    Then the delta buckets contain bucket "to_delete" with count 0
    And the ChangeSet has 0 operations

  @wip
  Scenario: ACT-6-CICD-17 Commit log triggers scout with repo reads
    Given the Metamodel "c4" exists with C4 stereotypes and packages
    And the Yggdrasil model "Yggdrasil" exists
    When Marcus pipes commit message stdin into ratatosk update with repo "./repo":
      """
      feat(llm.planner): add planning to the agent #MIM-056
      """
    Then the run blackboard contains step "scout_plan"
    And the run blackboard scout_plan includes path "src/llm/planner"
    And a ChangeSet with source "ratatosk" exists

  @wip
  Scenario: ACT-6-CICD-18 ModelSummary overflow triggers MCP drill-down during scout
    Given the Metamodel "c4" exists with C4 stereotypes and packages
    And the Yggdrasil model "Yggdrasil" exists with 200 elements
    And the stdin fixture "pr.diff" is available
    When Marcus pipes the stdin fixture "pr.diff" into ratatosk update with repo "./repo"
    Then the run blackboard contains key "model_summary_chars"
    And an MCP tool call to "list_elements" was recorded on the blackboard

  @wip
  Scenario: ACT-6-CICD-19 Update never wipes the graph
    Given the Metamodel "c4" exists with C4 stereotypes and packages
    And the Yggdrasil model "Yggdrasil" exists with 31 elements and 44 relationships
    And the stdin fixture "pr.diff" is available
    When Marcus pipes the stdin fixture "pr.diff" into ratatosk update with repo "./repo"
    Then the output does not contain "wiping"
    And the Yggdrasil model "Yggdrasil" still has 31 elements
