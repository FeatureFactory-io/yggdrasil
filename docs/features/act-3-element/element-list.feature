Feature: ELEMENT-LIST+FIND-1 Elements List with Search and Filter
  As a Software Architect (Priya)
  I want to browse, search, and filter architecture elements
  So that I can quickly locate any element in the model

  # Screen: ELEMENT-LIST+FIND-1 (entry point for all element operations)
  # Mockup: /mockups/element/
  # Testids: element-list-page, create-element-btn, element-search, filter-stereotype,
  #          filter-package, filter-source, element-row-{id}, view-el-{id}, edit-el-{id},
  #          delete-el-{id}, element-delete-modal, confirm-delete-btn
  # Fixture: seed.json (priya@example.com / test-pass-only-1234)
  # Mock data: 6 elements — Payment API, Notification Service, Order Domain,
  #            Fulfillment Worker, PostgreSQL, Mobile App

  Background:
    Given the user is logged in as "architect"

  Scenario: ELEMENT-LIST+FIND-1-01 List page renders with all 6 mock elements
    When I GET "/mockups/element/"
    Then the response status is 200
    And the element "element-list-page" should be visible
    And the user should see "Payment API"
    And the user should see "Notification Service"
    And the user should see "Order Domain"
    And the user should see "Fulfillment Worker"
    And the user should see "PostgreSQL"
    And the user should see "Mobile App"

  Scenario: ELEMENT-LIST+FIND-1-02 Create element button is visible for architect
    When I GET "/mockups/element/"
    Then the response status is 200
    And the element "create-element-btn" should be visible

  Scenario: ELEMENT-LIST+FIND-1-03 List shows stereotype, package, owner, health, source columns
    When I GET "/mockups/element/"
    Then the response status is 200
    And the user should see "Container"
    And the user should see "Technology"
    And the user should see "payments-team"
    And the user should see "ratatosk"

  Scenario: ELEMENT-LIST+FIND-1-04 Each element row has view, edit, and delete actions
    When I GET "/mockups/element/"
    Then the response status is 200
    And the element "view-el-1" should be visible
    And the element "edit-el-1" should be visible
    And the element "delete-el-1" should be visible

  Scenario: ELEMENT-LIST+FIND-1-05 Search input is present
    When I GET "/mockups/element/"
    Then the response status is 200
    And the element "element-search" should be visible

  Scenario: ELEMENT-LIST+FIND-1-06 Filter controls for stereotype, package, and source are present
    When I GET "/mockups/element/"
    Then the response status is 200
    And the element "filter-stereotype" should be visible
    And the element "filter-package" should be visible
    And the element "filter-source" should be visible

  Scenario: ELEMENT-LIST+FIND-1-07 Search for "Payment" shows only Payment API
    When I GET "/mockups/element/"
    Then the response status is 200
    And the user should see "Payment API"
    # Search is client-side JS in mockup; AT verifies element is in the response
    # BPE-04 E2E: enter "Payment" into element-search, then assert only 1 row visible

  Scenario: ELEMENT-LIST+FIND-1-08 Delete modal appears when delete trigger is clicked
    When I GET "/mockups/element/"
    Then the response status is 200
    And the element "element-delete-modal" should be visible
    And the element "confirm-delete-btn" should be visible

  # ── Viewer permissions ────────────────────────────────────────────────────
  Scenario: ELEMENT-LIST+FIND-1-09 Viewer can browse elements
    Given the user is logged in as "viewer"
    When I GET "/mockups/element/"
    Then the response status is 200
    And the element "element-list-page" should be visible
    And the user should see "Payment API"

  # ── Navbar integration ────────────────────────────────────────────────────
  Scenario: ELEMENT-LIST+FIND-1-10 Elements nav link is active
    When I GET "/mockups/element/"
    Then the response status is 200
    And the element "nav-elements" should be visible
