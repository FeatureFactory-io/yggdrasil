@wip
Feature: ACT-5-MCP-QUERY MCP Read Tools — Browse Graph from Any AI Client
  As a Software Architect (Priya) or Enterprise Architect (Elena)
  I want to query the architecture graph via MCP tools from Cursor or Claude Desktop
  So that I can get ground-truth answers without opening the browser

  # Act 5: No GUI screen — FastMCP server exposes same service layer as REST API.
  # Client: Cursor Agent, Claude Desktop, or custom MCP script.
  # Auth: Bearer token (from AUTH-TOKEN-1).
  # Note: MCP step definitions require TFK-07 (mcp_steps.py) in BPE.
  # Reference: docs/features/user_journey.md Act 5, lines 374–440.

  Scenario: ACT-5-MCP-QUERY-01 list_elements returns paginated element list
    Given Priya has a valid read-write token configured in mcp_config.json
    And the model "Yggdrasil" contains 6 elements
    When Priya calls MCP tool "list_elements" with:
      | param | value     |
      | model | Yggdrasil |
    Then the response contains 6 elements
    And element "Payment API" is in the response with stereotype "Container"
    And element "Mobile App" is in the response with stereotype "System"

  Scenario: ACT-5-MCP-QUERY-02 search returns matching elements by name
    Given Priya has a valid read-write token
    When Priya calls MCP tool "search" with:
      | param | value      |
      | query | Payment    |
      | model | Yggdrasil  |
    Then the response contains "Payment API"
    And the response does not contain "Order Domain"

  Scenario: ACT-5-MCP-QUERY-03 get_element returns element with properties and relationships
    Given Priya has a valid read-write token
    When Priya calls MCP tool "get_element" with:
      | param      | value       |
      | id_or_name | Payment API |
    Then the response contains:
      | field       | value         |
      | name        | Payment API   |
      | stereotype  | Container     |
      | package     | Technology    |
      | owner       | payments-team |
    And the response contains a "properties" field with "framework": "FastAPI"
    And the response contains a "confidence" field

  Scenario: ACT-5-MCP-QUERY-04 traverse returns incoming dependencies of Payment API
    Given Priya is in Cursor and wants to know what depends on Payment API
    When Priya calls MCP tool "traverse" with:
      | param     | value       |
      | from      | payment-api |
      | direction | incoming    |
    Then the response contains "Mobile App"
    And the response contains "Order Domain"
    And each entry includes the element owner and confidence

  Scenario: ACT-5-MCP-QUERY-05 list_elements with stereotype filter returns only matching elements
    Given Priya has a valid read-write token
    When Priya calls MCP tool "list_elements" with:
      | param      | value     |
      | model      | Yggdrasil |
      | stereotype | Container |
    Then the response contains "Payment API"
    And the response contains "Notification Service"
    And the response does not contain "Mobile App"
    And the response does not contain "PostgreSQL"

  Scenario: ACT-5-MCP-QUERY-06 list_elements with as_of returns historical snapshot
    Given Elena wants to see the domain model as of 2026-01-01
    When Elena calls MCP tool "list_elements" with:
      | param      | value      |
      | model      | Yggdrasil  |
      | stereotype | Component  |
      | as_of      | 2026-01-01 |
    Then the response reflects the model state as of 2026-01-01
    And the response header or metadata indicates the historical timestamp

  Scenario: ACT-5-MCP-QUERY-07 list_changesets returns pending and applied ChangeSets
    Given Priya has a valid read-write token
    When Priya calls MCP tool "list_changesets" with no params
    Then the response contains a ChangeSet with status "pending"
    And the response contains ChangeSets with status "applied"

  Scenario: ACT-5-MCP-QUERY-08 get_changeset returns operations list with Munin reasoning
    Given the model has ChangeSet id=1 (run-003, pending, 6 operations)
    When Priya calls MCP tool "get_changeset" with:
      | param | value |
      | id    | 1     |
    Then the response contains 6 operations
    And the response contains "Notification Service" in an Add Element operation
    And the response contains a "munin_reasoning" field

  Scenario: ACT-5-MCP-QUERY-09 list_stereotypes returns metamodel stereotype definitions
    Given Priya has a valid read-write token
    When Priya calls MCP tool "list_stereotypes" with:
      | param | value     |
      | model | Yggdrasil |
    Then the response contains stereotype "Container"
    And the response contains stereotype "Component"
    And each entry includes the property_schema

  Scenario: ACT-5-MCP-QUERY-10 list_ratatosk_runs returns run history
    Given the model has 3 completed Ratatosk runs
    When the CI agent calls MCP tool "list_ratatosk_runs" with:
      | param | value     |
      | model | Yggdrasil |
    Then the response contains 3 runs
    And run id=3 has status "complete" and changeset_id=1
