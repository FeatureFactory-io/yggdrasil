# Mockup: src/yggdrasil/web/templates/mockups/diagram/list.html
# Reconciliation: docs/plans/DIAGRAM_EDITOR_CHANGE_RECONCILIATION.md

@wip
Feature: DIAGRAM-LIST+FIND-1 Diagrams per Package
  As an Enterprise Architect (Elena)
  I want to see all curated diagrams grouped by package with lifecycle actions
  So that I can open the editor and manage diagram inventory

  # Screen: DIAGRAM-LIST+FIND-1
  # Diagram kinds come from the Model's Metamodel catalog (C4 example below).

  Background:
    Given the user is logged in as "architect"

  Scenario: DIAGRAM-LIST+FIND-1-01 Diagram list renders with diagrams grouped by package
    When Elena browses to the Diagram list screen
    Then she sees diagrams grouped by package
    And the Technology package has a "Container Diagram C1" entry

  Scenario: DIAGRAM-LIST+FIND-1-02 Each diagram shows its kind from the metamodel catalog
    When Elena views the Diagram list
    Then each entry shows a diagram kind from the metamodel catalog
    And C4 metamodel entries may include:
      | kind      |
      | Context   |
      | Container |
      | Component |
      | Code      |

  Scenario: DIAGRAM-LIST+FIND-1-03 Hover Edit opens DIAGRAM-EDITOR-1
    When Elena hovers the row for "Container Diagram C1"
    And Elena clicks Edit for "Container Diagram C1"
    Then DIAGRAM-EDITOR-1 opens for "Container Diagram C1"

  Scenario: DIAGRAM-LIST+FIND-1-04 Draft pill visible when unsaved draft exists
    Given "Container Diagram C1" has an unsaved server-side draft
    When Elena views the Diagram list
    Then Elena sees the Draft pill on "Container Diagram C1"

  Scenario: DIAGRAM-LIST+FIND-1-05 Hover actions include Edit Delete and Move
    When Elena hovers the row for "Container Diagram C1"
    Then Elena sees Edit Delete and Move actions for "Container Diagram C1"

  Scenario: DIAGRAM-LIST+FIND-1-06 Diagram instances may be created during bootstrap
    Given the Metamodel "c4" exists with C4 stereotypes and packages
    And a new model is created with metamodel=c4
    When Elena browses to the Diagram list
    Then at least one diagram of each C4 kind is present

  Scenario: DIAGRAM-LIST+FIND-1-07 Diagram list is filterable by package
    Given the model has diagrams in Technology, Application, and Context packages
    When Elena selects "Technology" from the package filter
    Then only diagrams in the Technology package are shown

  Scenario: DIAGRAM-LIST+FIND-1-08 Row shows Munin summary and tags after save
    Given diagram "Container Diagram C1" was saved with Munin enrichment
    When Elena views the Diagram list
    Then "Container Diagram C1" shows a summary line
    And "Container Diagram C1" shows searchable tags
