# Mockup: src/yggdrasil/web/templates/mockups/diagram/list.html (delete modal)
# Reconciliation: docs/plans/DIAGRAM_EDITOR_CHANGE_RECONCILIATION.md

@wip
Feature: DIAGRAM-DELETE_DIAGRAM-1 Delete diagram confirmation
  As an Enterprise Architect (Elena)
  I want to delete a curated diagram with clear blast-radius messaging
  So that I remove presentation views without accidentally deleting graph elements

  Background:
    Given the user is logged in as "architect"

  Scenario: DIAGRAM-DELETE_DIAGRAM-1-01 Delete modal shows diagram identity and preserved graph note
    Given Elena is on DIAGRAM-LIST+FIND-1
    When Elena hovers the row for "Container Diagram C1"
    And Elena clicks Delete for "Container Diagram C1"
    Then the delete diagram modal is visible
    And the modal states that Elements and Relationships remain in the graph

  Scenario: DIAGRAM-DELETE_DIAGRAM-1-02 Confirm delete removes diagram via ChangeSet
    Given Elena is on DIAGRAM-LIST+FIND-1
    When Elena deletes diagram "Container Diagram C1" with confirmation
    Then diagram "Container Diagram C1" is removed from the list
    And graph elements that were on the diagram still exist

  Scenario: DIAGRAM-DELETE_DIAGRAM-1-03 Cancel closes modal without changes
    Given Elena opened the delete modal for "Container Diagram C1"
    When Elena cancels delete
    Then diagram "Container Diagram C1" remains in the list
