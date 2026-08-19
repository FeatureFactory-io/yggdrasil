# Mockup: src/yggdrasil/web/templates/mockups/diagram/list.html (move modal)
# Reconciliation: docs/plans/DIAGRAM_EDITOR_CHANGE_RECONCILIATION.md

@wip
Feature: DIAGRAM-MOVE_DIAGRAM-1 Move diagram to package
  As an Enterprise Architect (Elena)
  I want to move a diagram to another package within the same metamodel
  So that diagram inventory stays aligned with package governance

  Background:
    Given the user is logged in as "architect"

  Scenario: DIAGRAM-MOVE_DIAGRAM-1-01 Move modal shows current and target package
    Given Elena is on DIAGRAM-LIST+FIND-1
    When Elena hovers the row for "Container Diagram C1"
    And Elena clicks Move for "Container Diagram C1"
    Then the move diagram modal is visible
    And the current package is shown as read-only

  Scenario: DIAGRAM-MOVE_DIAGRAM-1-02 Confirm move updates diagram package
    Given diagram "Container Diagram C1" is in package Technology
    When Elena moves "Container Diagram C1" to package Application
    Then "Container Diagram C1" appears under Application on the diagram list

  Scenario: DIAGRAM-MOVE_DIAGRAM-1-03 Cancel closes modal without changes
    Given Elena opened the move modal for "Container Diagram C1"
    When Elena cancels move
    Then "Container Diagram C1" remains in package Technology
