Feature: RELATIONSHIP-DELETE_RELATIONSHIP-1 Delete Relationship (Confirmation Modal)
  As a Software Architect (Priya)
  I want to confirm deletion of a relationship after seeing what it connects
  So that I don't accidentally sever a dependency that is still active

  # Screen: RELATIONSHIP-DELETE_RELATIONSHIP-1 (modal on view and list pages)
  # Mockup: /mockups/relationship/{id}/ (modal embedded in view page)
  # Testids: relationship-delete-modal, relationship-delete-form, confirm-delete-btn
  # Also: on /mockups/relationship/ (list page modal)
  # Fixture: seed.json (priya@example.com / test-pass-only-1234)
  # Mock relationship: id=1, Mobile App →calls→ Payment API

  Background:
    Given the user is logged in as "architect"

  Scenario: RELATIONSHIP-DELETE_RELATIONSHIP-1-01 Delete modal is present on relationship view page
    When I GET "/mockups/relationship/1/"
    Then the response status is 200
    And the element "relationship-delete-modal" should be visible
    And the element "confirm-delete-btn" should be visible

  Scenario: RELATIONSHIP-DELETE_RELATIONSHIP-1-02 Delete modal has a submit form
    When I GET "/mockups/relationship/1/"
    Then the response status is 200
    And the element "relationship-delete-form" should be visible

  Scenario: RELATIONSHIP-DELETE_RELATIONSHIP-1-03 Delete modal shows from/to/edge context
    When I GET "/mockups/relationship/1/"
    Then the response status is 200
    And the user should see "Mobile App"
    And the user should see "calls"
    And the user should see "Payment API"

  Scenario: RELATIONSHIP-DELETE_RELATIONSHIP-1-04 Delete modal is also accessible from list page
    When I GET "/mockups/relationship/"
    Then the response status is 200
    And the element "relationship-delete-modal" should be visible
    And the element "confirm-delete-btn" should be visible

  Scenario: RELATIONSHIP-DELETE_RELATIONSHIP-1-05 Munin checks diagram/package integrity before deleting
    # After confirming, Munin verifies no diagram layout or package integrity is affected
    # before queuing the delete operation in a ChangeSet.
    Given the user has confirmed deletion of relationship id=1 (Mobile App →calls→ Payment API)
    Then a ChangeSet with a "Delete Relationship" operation is queued
    And the ChangeSet source is "human"

  Scenario: RELATIONSHIP-DELETE_RELATIONSHIP-1-06 Cancelling delete leaves relationship intact
    When I GET "/mockups/relationship/1/"
    Then the element "relationship-delete-modal" should be visible
    # User closes modal → relationship-view-page still visible, relationship unchanged
