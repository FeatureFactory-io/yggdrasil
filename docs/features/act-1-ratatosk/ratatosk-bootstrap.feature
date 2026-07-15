Feature: ACT-1-CLI Ratatosk Bootstrap
  As a Software Architect (Priya)
  I want to run ratatosk bootstrap against my repository
  So that an initial C4 architecture model is built without manual data entry

  # Act 1: CLI-only in MVP — no GUI trigger screen.
  # The GUI shows run results (MUNIN-BRIEFING-1, RATATOSK_RUN-LIST+FIND-1).
  # Fixture: seed.json (priya@example.com / test-pass-only-1234)
  # CLI reference: docs/features/user_journey.md Act 1
  # Note: CLI step definitions require TFK-07 (subprocess/MCP steps) in BPE.

  Scenario: ACT-1-CLI-01 Generic bootstrap creates a ChangeSet from repository scan
    Given Priya has a Yggdrasil personal access token with read-write scope
    And the Yggdrasil model "Yggdrasil" exists with no elements
    When Priya runs:
      """
      ratatosk bootstrap ./repo --token=$YGGDRASIL_TOKEN --model Yggdrasil --metamodel=c4
      """
    Then the exit code is 0
    And the output contains "run complete"
    And the output contains "ChangeSet #"
    And the output contains "pending"
    And a link to the run result is printed

  Scenario: ACT-1-CLI-02 Bootstrap with instructions focuses analysis on specified layer
    Given Priya has a Yggdrasil personal access token with read-write scope
    And the Yggdrasil model "Yggdrasil" exists with 31 elements and 44 relationships
    When Priya runs:
      """
      ratatosk bootstrap ./repo --token=$YGGDRASIL_TOKEN --model Yggdrasil --metamodel=c4 \
        --instructions "Do an extra pass on the business logic layer — check whether any Domain objects have drifted out of sync with their model representations."
      """
    Then the exit code is 0
    And the output contains "fetching existing model state via MCP"
    And the output contains "found 31 existing elements"
    And the output contains "found 44 relationships"

  Scenario: ACT-1-CLI-03 Bootstrap output shows delta buckets before ChangeSet creation
    Given Priya has run a bootstrap with new candidates discovered
    Then the output contains "to_add:"
    And the output contains "to_update:"
    And the output contains "to_delete:"
    And the output contains "unchanged:"

  Scenario: ACT-1-CLI-04 Munin receives pre-bucketed delta from Ratatosk
    Given Ratatosk has produced delta buckets:
      | bucket    | count |
      | to_add    | 6     |
      | to_update | 3     |
      | to_delete | 1     |
      | unchanged | 22    |
    Then Munin produces ChangeSet with 10 planned operations
    And the ChangeSet summary contains "6 add-element ops"
    And the ChangeSet summary contains "3 update-element ops"
    And the ChangeSet summary contains "1 delete-element op"

  Scenario: ACT-1-CLI-05 High-confidence operations auto-apply; below-threshold ops queue for review
    Given a ChangeSet with 11 operations where 2 are below confidence threshold
    Then 9 operations are auto-applied to the model
    And 2 operations are queued for review in the ChangeSet
    And the output contains "below threshold"

  Scenario: ACT-1-CLI-06 Bootstrap with missing token fails with clear error
    When Priya runs:
      """
      ratatosk bootstrap ./repo --model Yggdrasil --metamodel=c4
      """
    Then the exit code is not 0
    And the output contains "token"

  # ── C4 metamodel default ───────────────────────────────────────────────────
  Scenario: ACT-1-CLI-07 Bootstrap seeds C4 structure automatically
    Given a successful bootstrap run on a Python web application repository
    Then the model contains elements with stereotypes from:
      | stereotype |
      | Container  |
      | Component  |
      | System     |
    And the model contains packages from:
      | package     |
      | Context     |
      | Technology  |
      | Application |
