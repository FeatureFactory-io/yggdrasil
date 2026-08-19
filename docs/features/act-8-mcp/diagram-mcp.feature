# Spec reconciliation: docs/plans/DIAGRAM_EDITOR_CHANGE_RECONCILIATION.md
# REST parity: docs/architecture/API_MCP_RECONCILIATION.md

@wip
Feature: MCP diagram draft and save tools
  As an MCP client (Marcus)
  I want two-phase diagram editing via draft patch and save commit
  So that GUI-free clients match the diagram editor draft model

  Background:
    Given an authenticated MCP client for model "yggdrasil"

  Scenario: diagram-mcp-01 list_diagrams returns has_draft indicator
    Given diagram "Container Diagram C1" has an unsaved server-side draft
    When Marcus calls list_diagrams for model "yggdrasil"
    Then the result for "Container Diagram C1" includes has_draft true

  Scenario: diagram-mcp-02 get_diagram returns committed presentation only
    Given diagram "Container Diagram C1" has an unsaved server-side draft
    When Marcus calls get_diagram for "Container Diagram C1"
    Then the response matches committed presentation
    And the response does not include draft-only pending elements

  Scenario: diagram-mcp-03 get_diagram_draft returns active draft
    Given diagram "Container Diagram C1" has an unsaved server-side draft
    When Marcus calls get_diagram_draft for "Container Diagram C1"
    Then the response includes draft presentation and pending blocks

  Scenario: diagram-mcp-04 update_diagram_draft patches without ChangeSet
    When Marcus calls update_diagram_draft with a node position patch for "Container Diagram C1"
    Then no ChangeSet is created
    And get_diagram_draft reflects the patched position

  Scenario: diagram-mcp-05 save_diagram commits via Munin and clears draft
    Given Marcus patched diagram "Container Diagram C1" via update_diagram_draft
    When Marcus calls save_diagram for "Container Diagram C1"
    Then Munin produces a ChangeSet
    And get_diagram_draft returns not found
    And list_diagrams shows has_draft false for "Container Diagram C1"

  Scenario: diagram-mcp-06 discard_diagram_draft drops draft without ChangeSet
    Given diagram "Container Diagram C1" has an unsaved server-side draft
    When Marcus calls discard_diagram_draft for "Container Diagram C1"
    Then get_diagram_draft returns not found
    And get_diagram matches the prior committed presentation

  Scenario: diagram-mcp-07 delete_diagram removes diagram and any draft
    When Marcus calls delete_diagram for "Container Diagram C1" with confirm true
    Then diagram "Container Diagram C1" is not in list_diagrams
    And get_diagram_draft returns not found

  Scenario: diagram-mcp-08 move_diagram updates package via ChangeSet
    When Marcus calls move_diagram for "Container Diagram C1" to package Application
    Then list_diagrams shows "Container Diagram C1" under Application
