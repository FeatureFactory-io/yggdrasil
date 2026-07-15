Feature: ACT-6-CICD Ratatosk CI/CD Update
  As a Development Team Lead (Marcus)
  I want Ratatosk to run automatically on every merge and update the model with the diff
  So that the architecture model stays current without manual intervention

  # Act 6: Pipeline-triggered incremental update.
  # Pattern: ratatosk update on the git diff since previous merge.
  # Same Ratatosk/Munin pipeline as Act 1 — incremental (diff) instead of full scan.
  # Reference: docs/features/user_journey.md Act 6, lines 448–464.
  # Note: CLI and pipeline step definitions require TFK-07 in BPE.

  Scenario: ACT-6-CICD-01 ratatosk update on a PR diff produces an incremental ChangeSet
    Given a GitHub Actions workflow with YGGDRASIL_TOKEN configured
    When a pull request is merged adding a new downstream service call
    And the CI pipeline runs:
      """
      git log -p $BEFORE..$SHA | ratatosk update --model Yggdrasil --token=$YGGDRASIL_TOKEN
      """
    Then the exit code is 0
    And the output contains "fetching existing model state via MCP"
    And a ChangeSet is produced containing only the delta from the diff

  Scenario: ACT-6-CICD-02 ratatosk update with instructions focuses analysis on changed interfaces
    Given a PR that modifies API contracts in the payment service
    When the CI pipeline runs:
      """
      git log -p $BEFORE..$SHA | ratatosk update --model Yggdrasil --token=$YGGDRASIL_TOKEN \
        --instructions "Focus on interface changes — any API contracts added, removed, or modified?"
      """
    Then the output contains the targeted analysis results
    And unchanged elements are not included in the ChangeSet

  Scenario: ACT-6-CICD-03 Ratatosk fetches current model state before analysing diff
    Given the model contains 31 elements and 44 relationships
    When ratatosk update runs on a new PR diff
    Then the output contains "fetching existing model state via MCP"
    And the ChangeSet only includes elements and relationships affected by the diff
    And the output does not include "unchanged" elements in the operations list

  Scenario: ACT-6-CICD-04 Incremental update produces delta buckets just like bootstrap
    Given a diff containing 2 new functions, 1 modified interface, and 1 removed module
    When ratatosk update processes the diff
    Then the delta buckets contain:
      | bucket    | min_count |
      | to_add    | 0         |
      | to_update | 0         |
      | to_delete | 0         |
    And unchanged elements are never sent to Munin

  Scenario: ACT-6-CICD-05 CI pipeline links to the run result URL on completion
    When ratatosk update completes successfully
    Then the output contains a URL to the run result
    And the URL points to RATATOSK_RUN-VIEW_RATATOSK_RUN-1 for the new run

  Scenario: ACT-6-CICD-06 Update run result is visible in RATATOSK_RUN-LIST+FIND-1
    Given a successful CI update run has just completed
    When Marcus browses to /mockups/ratatosk-run/
    Then the response status is 200
    And the most recent run shows trigger "ratatosk update"

  Scenario: ACT-6-CICD-07 ratatosk update with no relevant changes produces an empty ChangeSet
    Given a PR that only changes test files with no architecture impact
    When ratatosk update processes the diff
    Then the ChangeSet has 0 operations
    And the output contains "no architecture changes detected"
