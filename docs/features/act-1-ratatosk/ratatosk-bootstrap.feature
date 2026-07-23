@wip
Feature: ACT-1-CLI Ratatosk Bootstrap
  As a Software Architect (Priya)
  I want to run ratatosk bootstrap against my repository
  So that an initial C4 architecture model is built without manual data entry

  # Act 1: CLI-only in MVP — no GUI trigger screen.
  # MVP-W1: first real bootstrap (empty model, local server, sample_webapp fixture).
  # CLI reference: docs/features/user_journey.md Act 1

  # ── MVP-W1: first bootstrap ────────────────────────────────────────────────

  Scenario: ACT-1-CLI-01 Generic bootstrap creates a ChangeSet from repository scan
    Given Priya has a Yggdrasil personal access token with read-write scope
    And the Yggdrasil model "Yggdrasil" exists with no elements
    And the fixture repository "sample_webapp" is available
    And the environment variable "YGGDRASIL_SERVER_URL" is set to "http://localhost:8000"
    When Priya runs:
      """
      ratatosk bootstrap ./repo --token=$YGGDRASIL_TOKEN --model Yggdrasil --metamodel=c4 \
        --server $YGGDRASIL_SERVER_URL
      """
    Then the exit code is 0
    And the output contains "building ModelSummary"
    And the output contains "scanning"
    And the output contains "to_add:"
    And the output contains "run complete"
    And the output contains "ChangeSet #"
    And the output contains "pending"
    And a link to the run result is printed

  Scenario: ACT-1-CLI-08 Empty model bootstrap runs wipe no-op then scan
    Given Priya has a Yggdrasil personal access token with read-write scope
    And the Yggdrasil model "Yggdrasil" exists with no elements
    And the fixture repository "sample_webapp" is available
    When Priya runs:
      """
      ratatosk bootstrap ./repo --token=$YGGDRASIL_TOKEN --model Yggdrasil --metamodel=c4
      """
    Then the exit code is 0
    And the output contains wipe no-op for empty graph
    And the output contains "building ModelSummary"
    And the output contains "to_add:"

  Scenario: ACT-1-CLI-09 Bootstrap uses local server URL from environment
    Given Priya has a Yggdrasil personal access token with read-write scope
    And the Yggdrasil model "Yggdrasil" exists with no elements
    And the fixture repository "sample_webapp" is available
    And the environment variable "YGGDRASIL_SERVER_URL" is set to "http://localhost:8000"
    When Priya runs:
      """
      ratatosk bootstrap ./repo --token=$YGGDRASIL_TOKEN --model Yggdrasil --metamodel=c4 \
        --server http://localhost:8000
      """
    Then the exit code is 0
    And the output contains "run complete"

  Scenario: ACT-1-CLI-06 Bootstrap with missing token fails with clear error
    When Priya runs:
      """
      ratatosk bootstrap ./repo --model Yggdrasil --metamodel=c4
      """
    Then the exit code is not 0
    And the output contains "token"

  Scenario: ACT-1-CLI-07 Bootstrap uses existing C4 Metamodel ontology
    Given the Metamodel "c4" exists with C4 stereotypes and packages
    And a successful bootstrap run on a Python web application repository
    Then the model's metamodel is "c4"
    And the model contains elements with stereotypes from:
      | stereotype |
      | Container  |
      | Component  |
      | System     |
    And the model's metamodel contains packages from:
      | package     |
      | Context     |
      | Technology  |
      | Application |

  # ── MVP-W2: re-bootstrap / Munin handoff ───────────────────────────────────

  @wip
  Scenario: ACT-1-CLI-02 Re-bootstrap wipes graph then scans with instructions
    Given Priya has a Yggdrasil personal access token with read-write scope
    And the Yggdrasil model "Yggdrasil" exists with 31 elements and 44 relationships
    When Priya runs:
      """
      ratatosk bootstrap ./repo --token=$YGGDRASIL_TOKEN --model Yggdrasil --metamodel=c4 \
        --instructions "Do an extra pass on the business logic layer — check whether any Domain objects have drifted out of sync with their model representations."
      """
    Then the exit code is 0
    And the output contains "wiping 31 elements and 44 relationships"
    And the output contains "scanning ./repo with instructions"
    And the output does not contain "unchanged:"

  @wip
  Scenario: ACT-1-CLI-03 Bootstrap output shows add-heavy buckets after wipe
    Given Priya has run a bootstrap with new candidates discovered
    Then the output contains "to_add:"
    And the output does not contain "unchanged:"
    And the output does not contain "to_update:"

  @wip
  Scenario: ACT-1-CLI-04 Munin receives element candidates from bootstrap and plans relationships
    Given Ratatosk has produced bootstrap buckets:
      | bucket | count |
      | to_add | 27    |
    Then Munin produces ChangeSet with at least 27 planned operations
    And the ChangeSet summary contains "add-element ops"
    And the ChangeSet summary contains "add-relationship ops"

  @wip
  Scenario: ACT-1-CLI-05 High-confidence operations auto-apply; below-threshold ops queue for review
    Given a ChangeSet with 11 operations where 2 are below confidence threshold
    Then 9 operations are auto-applied to the model
    And 2 operations are queued for review in the ChangeSet
    And the output contains "below threshold"
