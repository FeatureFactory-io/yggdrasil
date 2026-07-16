@wip
Feature: ELEMENT-VIEW_ELEMENT-1 View Element Details
  As a Software Architect (Priya)
  I want to see the full details of an architecture element
  So that I can understand its properties, relationships, and change history

  # Screen: ELEMENT-VIEW_ELEMENT-1
  # Mockup: /mockups/element/{id}/
  # Testids: element-view-page, delete-element-btn, edit-element-btn,
  #          element-delete-modal, blast-radius-panel, element-delete-form, confirm-delete-btn
  # Fixture: seed.json (priya@example.com / test-pass-only-1234)
  # Mock element: id=1, Payment API, Container, Technology, payments-team

  Background:
    Given the user is logged in as "architect"

  Scenario: ELEMENT-VIEW_ELEMENT-1-01 View page renders with element details
    When I GET "/mockups/element/1/"
    Then the response status is 200
    And the element "element-view-page" should be visible
    And the user should see "Payment API"

  Scenario: ELEMENT-VIEW_ELEMENT-1-02 View page shows stereotype, package, and owner
    When I GET "/mockups/element/1/"
    Then the response status is 200
    And the user should see "Container"
    And the user should see "Technology"
    And the user should see "payments-team"

  Scenario: ELEMENT-VIEW_ELEMENT-1-03 View page shows element properties
    When I GET "/mockups/element/1/"
    Then the response status is 200
    And the user should see "FastAPI"
    And the user should see "2.3.1"

  Scenario: ELEMENT-VIEW_ELEMENT-1-04 View page shows confidence score
    When I GET "/mockups/element/1/"
    Then the response status is 200
    And the user should see "92"

  Scenario: ELEMENT-VIEW_ELEMENT-1-05 View page shows health status
    When I GET "/mockups/element/1/"
    Then the response status is 200
    And the user should see "green"

  Scenario: ELEMENT-VIEW_ELEMENT-1-06 View page shows relationship counts
    When I GET "/mockups/element/1/"
    Then the response status is 200
    And the user should see "4"
    And the user should see "6"

  Scenario: ELEMENT-VIEW_ELEMENT-1-07 Edit button is visible for architect
    When I GET "/mockups/element/1/"
    Then the response status is 200
    And the element "edit-element-btn" should be visible

  Scenario: ELEMENT-VIEW_ELEMENT-1-08 Delete button opens confirmation modal with blast-radius info
    When I GET "/mockups/element/1/"
    Then the response status is 200
    And the element "delete-element-btn" should be visible
    And the element "element-delete-modal" should be visible
    And the element "blast-radius-panel" should be visible
    And the element "confirm-delete-btn" should be visible

  Scenario: ELEMENT-VIEW_ELEMENT-1-09 Viewing a different element (Order Domain) shows its data
    When I GET "/mockups/element/3/"
    Then the response status is 200
    And the user should see "Order Domain"
    And the user should see "Component"
    And the user should see "Application"
    And the user should see "fulfillment-team"

  # ── Navbar integration ────────────────────────────────────────────────────
  Scenario: ELEMENT-VIEW_ELEMENT-1-10 Navbar is visible on element view page
    When I GET "/mockups/element/1/"
    Then the response status is 200
    And the element "nav-elements" should be visible
    And the element "nav-view-browser" should be visible
