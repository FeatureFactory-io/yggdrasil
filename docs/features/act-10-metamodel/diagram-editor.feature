# Mockup: src/yggdrasil/web/templates/mockups/diagram/editor.html
# Reconciliation: docs/plans/DIAGRAM_EDITOR_CHANGE_RECONCILIATION.md

@wip
Feature: DIAGRAM-EDITOR-1 Cytoscape diagram editor
  As an Enterprise Architect (Elena)
  I want a full-screen diagram editor with draft-first editing
  So that I can curate membership and presentation before committing via Munin

  # Screen: DIAGRAM-EDITOR-1
  # Draft-first: GUI/MCP/chat patch draft; Save → Munin → ChangeSet

  Background:
    Given the user is logged in as "architect"
    And the model "yggdrasil" uses metamodel "c4"

  Scenario: DIAGRAM-EDITOR-1-01 Create mode opens empty canvas after create modal
    Given Elena is on VIEW-BROWSE-1 for model "yggdrasil"
    When Elena clicks "Add Diagram"
    And Elena fills the create diagram modal with:
      | field         | value              |
      | name          | Payment Containers |
      | package       | Technology         |
      | diagram kind  | Container          |
    And Elena confirms create diagram
    Then DIAGRAM-EDITOR-1 opens in Create mode
    And the canvas has zero nodes
    And the header shows "Payment Containers"
    And the Draft pill is not shown

  Scenario: DIAGRAM-EDITOR-1-02 Edit mode loads committed presentation when no draft
    Given a committed Container diagram "Container Diagram C1" exists in Technology
    When Elena opens DIAGRAM-EDITOR-1 for "Container Diagram C1" via Edit
    Then the canvas shows committed element positions
    And the Draft pill is not shown

  Scenario: DIAGRAM-EDITOR-1-03 Edit mode loads draft when unsaved draft exists
    Given "Container Diagram C1" has an unsaved server-side draft
    When Elena opens DIAGRAM-EDITOR-1 for "Container Diagram C1" via Edit
    Then the canvas shows draft positions
    And Elena sees the Draft pill on the editor header

  Scenario: DIAGRAM-EDITOR-1-04 Drag from model tree adds element to draft
    Given Elena is editing diagram "Container Diagram C1" in DIAGRAM-EDITOR-1
    When Elena drags "Payment API" from the model tree onto the canvas
    Then "Payment API" appears on the canvas
    And the draft membership includes Payment API
    And no ChangeSet is created

  Scenario: DIAGRAM-EDITOR-1-05 Tools palette greys disallowed relationship stereotypes
    Given Elena is editing diagram "Container Diagram C1" in DIAGRAM-EDITOR-1
    And Elena selects node "Payment API" on the canvas
    When Elena opens the Relationships section of the Tools palette
    Then allowed edge stereotypes for Payment API are enabled
    And disallowed edge stereotypes are greyed out

  Scenario: DIAGRAM-EDITOR-1-06 On-canvas plus creates pending relationship in draft
    Given Elena is editing diagram "Container Diagram C1" in DIAGRAM-EDITOR-1
    And "Payment API" and "PostgreSQL" are on the canvas
    When Elena clicks the plus control on "Payment API"
    And Elena draws a relationship to "PostgreSQL" with stereotype "depends_on"
    Then a pending relationship exists in the draft
    And no ChangeSet is created

  Scenario: DIAGRAM-EDITOR-1-07 Discard drops draft and leaves committed diagram unchanged
    Given "Container Diagram C1" has an unsaved server-side draft
    When Elena clicks Discard on DIAGRAM-EDITOR-1
    And Elena confirms discard
    Then the draft is deleted
    And the committed diagram presentation is unchanged

  Scenario: DIAGRAM-EDITOR-1-08 Save commits draft via Munin and clears draft pill
    Given Elena is editing diagram "Container Diagram C1" in DIAGRAM-EDITOR-1
    And Elena has unsaved canvas changes in the draft
    When Elena clicks Save on DIAGRAM-EDITOR-1
    Then Munin produces a ChangeSet for the diagram draft
    And the diagram receives summary and tags enrichment
    And the Draft pill is cleared on list and editor
