Feature: ACT-5-MCP-CHANGESET MCP ChangeSet Tools — Review and Apply Graph Operations
  As a Software Architect (Priya) or CI agent (Marcus)
  I want to approve, reject, or redirect ChangeSet operations via MCP
  So that I can manage graph writes without opening the browser

  # Act 5: ChangeSet tools for headless review workflows.
  # Reference: docs/features/user_journey.md Act 5, lines 407–413, 442.
  # Note: MCP step definitions require TFK-07 (mcp_steps.py) in BPE.

  Scenario: ACT-5-MCP-CHANGESET-01 approve_changeset applies all pending operations
    Given ChangeSet id=1 has 6 pending operations
    When the CI agent calls MCP tool "approve_changeset" with:
      | param | value |
      | id    | 1     |
    Then all 6 operations are applied to the model
    And the ChangeSet status changes to "applied"

  Scenario: ACT-5-MCP-CHANGESET-02 approve_changeset with item_ids approves only specified operations
    Given ChangeSet id=1 has operations [1, 2, 3, 4, 5, 6]
    When Priya calls MCP tool "approve_changeset" with:
      | param    | value   |
      | id       | 1       |
      | item_ids | [1, 2]  |
    Then operations 1 and 2 are applied
    And operations 3, 4, 5, 6 remain pending

  Scenario: ACT-5-MCP-CHANGESET-03 reject_changeset rejects all pending operations
    Given ChangeSet id=1 has 6 pending operations
    When Priya calls MCP tool "reject_changeset" with:
      | param | value |
      | id    | 1     |
    Then all 6 operations are rejected
    And the ChangeSet status changes to "rejected"

  Scenario: ACT-5-MCP-CHANGESET-04 reject_changeset with reason appends rule to LEARNED
    Given ChangeSet id=1 has operation id=3 (Add to Diagram)
    When Marcus calls MCP tool "reject_changeset" with:
      | param    | value                                                                   |
      | id       | 1                                                                       |
      | item_ids | [3]                                                                     |
      | reason   | Code diagram is for repository structure, not runtime services          |
    Then operation 3 is rejected
    And a MuninRule is created with the provided reason text
    And the rule is prepended to Munin's BASE prompt on the next run

  Scenario: ACT-5-MCP-CHANGESET-05 do_other_changeset redirects Munin to re-plan a specific operation
    Given ChangeSet id=1 has operation id=3 (Add to Diagram — Notification Service → Container Diagram C1)
    When Marcus calls MCP tool "do_other_changeset" with:
      | param        | value                                                                  |
      | id           | 1                                                                      |
      | item_ids     | [3]                                                                    |
      | instructions | don't add this to the Container diagram, it's an external system       |
    Then operation 3 is rejected
    And Munin re-processes operation 3 with the instructions as context
    And a replacement ChangeSet is produced with the corrected operation
    And the instructions are appended to LEARNED

  Scenario: ACT-5-MCP-CHANGESET-06 CI agent approves high-confidence operations and redirects uncertain ones
    Given a post-merge ChangeSet with 5 operations:
      | id | op               | confidence |
      | 1  | Add Element      | 0.95       |
      | 2  | Add Relationship | 0.92       |
      | 3  | Update Element   | 0.88       |
      | 4  | Add to Diagram   | 0.65       |
      | 5  | Delete Element   | 0.40       |
    When the CI agent approves operations with confidence >= 0.80:
      | item_ids | [1, 2, 3] |
    And calls do_other_changeset for operation 5 with instructions "verify this deletion manually"
    Then operations 1, 2, 3 are applied
    And operation 4 remains pending for human review
    And operation 5 is redirected to Munin for re-planning
