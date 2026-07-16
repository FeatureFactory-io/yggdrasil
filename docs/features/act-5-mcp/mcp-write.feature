@wip
Feature: ACT-5-MCP-WRITE MCP Write Tools — Modify Graph via AI Client
  As a Software Architect (Priya) or a CI agent (Marcus)
  I want to create, update, and delete elements and relationships via MCP
  So that the model stays current without requiring a browser

  # Act 5: All writes go through the Munin/ChangeSet pipeline.
  # Auto-apply vs Manual-review is a per-Model setting.
  # Reference: docs/features/user_journey.md Act 5, lines 394–441.
  # Note: MCP step definitions require TFK-07 (mcp_steps.py) in BPE.

  Scenario: ACT-5-MCP-WRITE-01 create_element queues an Add Element operation in a ChangeSet
    Given Priya has a valid read-write token
    And the model "Yggdrasil" is in auto-approval mode
    When Priya calls MCP tool "create_element" with:
      | param      | value                |
      | name       | Notification Service |
      | stereotype | Container            |
      | package    | Technology           |
    Then Munin produces a ChangeSet with an "Add Element" operation for "Notification Service"
    And in auto-approval mode the operation is applied directly
    And the ChangeSet is retained as an audit trail

  Scenario: ACT-5-MCP-WRITE-02 create_element in manual-review mode queues for human approval
    Given Priya has a valid read-write token
    And the model "Yggdrasil" is in manual-review mode
    When Priya calls MCP tool "create_element" with:
      | param      | value     |
      | name       | API Gateway |
      | stereotype | Container |
      | package    | Technology |
    Then a ChangeSet with status "pending" is created
    And the ChangeSet contains 1 operation with status "pending"

  Scenario: ACT-5-MCP-WRITE-03 update_element changes a specific field
    Given the model contains element "Order Domain" with owner "payments-team"
    When Priya calls MCP tool "update_element" with:
      | param | value            |
      | id    | 3                |
      | owner | fulfillment-team |
    Then a ChangeSet with an "Update Element" operation is produced
    And the operation detail contains "owner → fulfillment-team"

  Scenario: ACT-5-MCP-WRITE-04 delete_element triggers Munin blast-radius check
    Given the model contains element "Payment API" (id=1) with 10 relationships
    When Priya calls MCP tool "delete_element" with:
      | param | value |
      | id    | 1     |
    Then Munin checks the blast-radius of deleting "Payment API"
    And a ChangeSet with a "Delete Element" operation is queued

  Scenario: ACT-5-MCP-WRITE-05 create_relationship adds a new edge via Munin
    Given the model contains "Mobile App" and "Notification Service"
    When Priya calls MCP tool "create_relationship" with:
      | param      | value                |
      | from_id    | 6                    |
      | stereotype | calls                |
      | to_id      | 2                    |
    Then Munin validates the edge rule for "calls" on System→Container
    And a ChangeSet with an "Add Relationship" operation is produced

  Scenario: ACT-5-MCP-WRITE-06 update_relationships_batch plans one ChangeSet for 12 operations
    Given Marcus has a Python script to wire a new service's relationships
    When Marcus calls MCP tool "update_relationships_batch" with 12 create-relationship operations
    Then Munin plans exactly 1 ChangeSet containing 12 "Add Relationship" operations
    And the ChangeSet can be inspected via get_changeset before approval

  Scenario: ACT-5-MCP-WRITE-07 set_model_mode toggles between auto and manual review
    Given the model "Yggdrasil" is currently in manual-review mode
    When Priya calls MCP tool "set_model_mode" with:
      | param    | value     |
      | model_id | Yggdrasil |
      | mode     | auto      |
    Then subsequent create_element calls apply directly without queuing

  Scenario: ACT-5-MCP-WRITE-08 Write tool with read-only token is rejected
    Given Priya has a read-only token
    When Priya calls MCP tool "create_element" with name "API Gateway"
    Then the response status is 403
    And the error message contains "permission"
