@wip
Feature: ELEMENT-DELETE_ELEMENT-1 Delete Element (Confirmation Modal)
  As a Software Architect (Priya)
  I want to confirm or cancel deletion of an element with a blast-radius preview
  So that I don't accidentally delete an element with active relationships

  # Screen: ELEMENT-DELETE_ELEMENT-1 (modal on ELEMENT-VIEW_ELEMENT-1 and ELEMENT-LIST+FIND-1)
  # Mockup: /mockups/element/{id}/ (modal embedded in view page)
  # Testids: element-delete-modal, blast-radius-panel, element-delete-form, confirm-delete-btn
  # Fixture: seed.json (priya@example.com / test-pass-only-1234)
  # Mock element: id=1, Payment API — 4 relationships_in, 6 relationships_out

  Background:
    Given the user is logged in as "architect"

  Scenario: ELEMENT-DELETE_ELEMENT-1-01 Delete modal is present on element view page
    When I GET "/mockups/element/1/"
    Then the response status is 200
    And the element "element-delete-modal" should be visible
    And the element "confirm-delete-btn" should be visible

  Scenario: ELEMENT-DELETE_ELEMENT-1-02 Delete modal shows blast-radius panel
    When I GET "/mockups/element/1/"
    Then the response status is 200
    And the element "blast-radius-panel" should be visible

  Scenario: ELEMENT-DELETE_ELEMENT-1-03 Delete modal has a submit form for confirmed deletion
    When I GET "/mockups/element/1/"
    Then the response status is 200
    And the element "element-delete-form" should be visible

  Scenario: ELEMENT-DELETE_ELEMENT-1-04 Delete modal is also accessible from element list
    When I GET "/mockups/element/"
    Then the response status is 200
    And the element "element-delete-modal" should be visible
    And the element "confirm-delete-btn" should be visible

  Scenario: ELEMENT-DELETE_ELEMENT-1-05 Delete trigger on view page opens modal
    When I GET "/mockups/element/1/"
    Then the element "delete-element-btn" should be visible
    # Clicking delete-element-btn shows element-delete-modal (Bootstrap modal toggle)

  Scenario: ELEMENT-DELETE_ELEMENT-1-06 Delete trigger on list opens modal
    When I GET "/mockups/element/"
    Then the element "delete-el-1" should be visible
    # Clicking delete-el-1 shows element-delete-modal

  Scenario: ELEMENT-DELETE_ELEMENT-1-07 Deletion goes through Munin blast-radius check
    # After confirming, Munin checks affected relationships before queuing delete operation.
    # Deletion enters the ChangeSet pipeline; it does not bypass Munin.
    Given the user has confirmed deletion of "Payment API" (id=1)
    Then a ChangeSet with a "Delete Element" operation for "Payment API" is queued
    And the ChangeSet summary contains blast-radius information

  Scenario: ELEMENT-DELETE_ELEMENT-1-08 Cancelling delete leaves element intact
    # Cancelling the modal: no form submission, element remains in list
    When I GET "/mockups/element/1/"
    Then the element "element-delete-modal" should be visible
    # User clicks backdrop or cancel → modal closes, element-view-page still visible
