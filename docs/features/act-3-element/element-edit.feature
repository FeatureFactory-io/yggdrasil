Feature: ELEMENT-EDIT_ELEMENT-1 Edit Element
  As a Software Architect (Priya)
  I want to edit an existing element's name, stereotype, package, or owner
  So that the model stays accurate as the architecture evolves

  # Screen: ELEMENT-EDIT_ELEMENT-1
  # Mockup: /mockups/element/{id}/edit/
  # Testids: element-edit-page, element-edit-form, element-name-input,
  #          element-stereotype-select, element-package-select, element-owner-input,
  #          element-save-btn
  # Fixture: seed.json (priya@example.com / test-pass-only-1234)
  # Mock element: id=1, Payment API, Container, Technology, payments-team

  Background:
    Given the user is logged in as "architect"

  Scenario: ELEMENT-EDIT_ELEMENT-1-01 Edit form renders with current values pre-populated
    When I GET "/mockups/element/1/edit/"
    Then the response status is 200
    And the element "element-edit-page" should be visible
    And the element "element-name-input" should be visible
    And the element "element-stereotype-select" should be visible
    And the element "element-package-select" should be visible
    And the element "element-owner-input" should be visible
    And the element "element-save-btn" should be visible

  Scenario: ELEMENT-EDIT_ELEMENT-1-02 Edit form pre-fills name from current element value
    When I GET "/mockups/element/1/edit/"
    Then the response status is 200
    And the user should see "Payment API"

  Scenario: ELEMENT-EDIT_ELEMENT-1-03 Edit form pre-selects current stereotype
    When I GET "/mockups/element/1/edit/"
    Then the response status is 200
    And the user should see "Container"

  Scenario: ELEMENT-EDIT_ELEMENT-1-04 Edit form pre-selects current package
    When I GET "/mockups/element/1/edit/"
    Then the response status is 200
    And the user should see "Technology"

  Scenario: ELEMENT-EDIT_ELEMENT-1-05 Edit form pre-fills current owner
    When I GET "/mockups/element/1/edit/"
    Then the response status is 200
    And the user should see "payments-team"

  Scenario: ELEMENT-EDIT_ELEMENT-1-06 Happy path — update owner of Order Domain
    When I GET "/mockups/element/3/edit/"
    Then the response status is 200
    And the user should see "Order Domain"
    And the user should see "fulfillment-team"
    # Full edit flow (AT):
    # When the user enters "new-team" into "element-owner"
    # And the user submits the form
    # Then the change enters the Munin/ChangeSet pipeline

  Scenario: ELEMENT-EDIT_ELEMENT-1-07 Name field is required
    When I GET "/mockups/element/1/edit/"
    Then the response status is 200
    And the element "element-name-input" should be visible
    # HTML required attribute enforced; TFK-07 for empty-name validation scenario

  Scenario: ELEMENT-EDIT_ELEMENT-1-08 Edit is reachable from element view page
    When I GET "/mockups/element/1/"
    Then the element "edit-element-btn" should be visible
    # Clicking edit-element-btn navigates to ELEMENT-EDIT_ELEMENT-1

  Scenario: ELEMENT-EDIT_ELEMENT-1-09 Edit is reachable from element list row
    When I GET "/mockups/element/"
    Then the element "edit-el-1" should be visible
    # Clicking edit-el-1 navigates to ELEMENT-EDIT_ELEMENT-1 for id=1

  # ── Navbar integration ────────────────────────────────────────────────────
  Scenario: ELEMENT-EDIT_ELEMENT-1-10 Navbar is visible on edit page
    When I GET "/mockups/element/1/edit/"
    Then the response status is 200
    And the element "nav-elements" should be visible
