@wip
Feature: RELATIONSHIP-LIST+FIND-1 Relationships List with Search and Filter
  As a Software Architect (Priya)
  I want to browse, search, and filter architecture relationships
  So that I can understand how elements connect to each other

  # Screen: RELATIONSHIP-LIST+FIND-1
  # Mockup: /mockups/relationship/
  # Testids: relationship-list-page, create-relationship-btn, relationship-search,
  #          filter-edge-stereotype, filter-rel-source, relationship-row-{id},
  #          view-rel-{id}, edit-rel-{id}, delete-rel-{id},
  #          relationship-delete-modal, confirm-delete-btn
  # Fixture: seed.json (priya@example.com / test-pass-only-1234)
  # Mock data: 6 relationships — Mobile App→calls→Payment API, etc.

  Background:
    Given the user is logged in as "architect"

  Scenario: RELATIONSHIP-LIST+FIND-1-01 List page renders with all 6 mock relationships
    When I GET "/mockups/relationship/"
    Then the response status is 200
    And the element "relationship-list-page" should be visible
    And the user should see "Mobile App"
    And the user should see "Payment API"
    And the user should see "calls"
    And the user should see "depends_on"

  Scenario: RELATIONSHIP-LIST+FIND-1-02 Create relationship button is visible for architect
    When I GET "/mockups/relationship/"
    Then the response status is 200
    And the element "create-relationship-btn" should be visible

  Scenario: RELATIONSHIP-LIST+FIND-1-03 List shows from-element, edge stereotype, to-element, and source
    When I GET "/mockups/relationship/"
    Then the response status is 200
    And the user should see "Order Domain"
    And the user should see "depends_on"
    And the user should see "Fulfillment Worker"
    And the user should see "serves"

  Scenario: RELATIONSHIP-LIST+FIND-1-04 Each relationship row has view, edit, and delete actions
    When I GET "/mockups/relationship/"
    Then the response status is 200
    And the element "view-rel-1" should be visible
    And the element "edit-rel-1" should be visible
    And the element "delete-rel-1" should be visible

  Scenario: RELATIONSHIP-LIST+FIND-1-05 Search input and stereotype/source filters are present
    When I GET "/mockups/relationship/"
    Then the response status is 200
    And the element "relationship-search" should be visible
    And the element "filter-edge-stereotype" should be visible
    And the element "filter-rel-source" should be visible

  Scenario: RELATIONSHIP-LIST+FIND-1-06 Delete modal is present
    When I GET "/mockups/relationship/"
    Then the response status is 200
    And the element "relationship-delete-modal" should be visible
    And the element "confirm-delete-btn" should be visible

  # ── Navbar integration ────────────────────────────────────────────────────
  Scenario: RELATIONSHIP-LIST+FIND-1-07 Relationships nav link is visible
    When I GET "/mockups/relationship/"
    Then the response status is 200
    And the element "nav-relationships" should be visible
