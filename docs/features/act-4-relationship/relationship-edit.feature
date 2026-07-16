@wip
Feature: RELATIONSHIP-EDIT_RELATIONSHIP-1 Edit Relationship
  As a Software Architect (Priya)
  I want to edit the edge stereotype or properties of a relationship
  So that the model reflects updated architectural decisions

  # Screen: RELATIONSHIP-EDIT_RELATIONSHIP-1
  # Mockup: /mockups/relationship/{id}/edit/
  # Testids: relationship-edit-page, relationship-edit-form, from-element-input,
  #          edge-stereotype-select, to-element-input, relationship-save-btn
  # Fixture: seed.json (priya@example.com / test-pass-only-1234)
  # Mock relationship: id=1, Mobile App →calls→ Payment API

  Background:
    Given the user is logged in as "architect"

  Scenario: RELATIONSHIP-EDIT_RELATIONSHIP-1-01 Edit form renders with current values pre-populated
    When I GET "/mockups/relationship/1/edit/"
    Then the response status is 200
    And the element "relationship-edit-page" should be visible
    And the element "from-element-input" should be visible
    And the element "edge-stereotype-select" should be visible
    And the element "to-element-input" should be visible
    And the element "relationship-save-btn" should be visible

  Scenario: RELATIONSHIP-EDIT_RELATIONSHIP-1-02 Edit form pre-fills from-element
    When I GET "/mockups/relationship/1/edit/"
    Then the response status is 200
    And the user should see "Mobile App"

  Scenario: RELATIONSHIP-EDIT_RELATIONSHIP-1-03 Edit form pre-selects current edge stereotype
    When I GET "/mockups/relationship/1/edit/"
    Then the response status is 200
    And the user should see "calls"

  Scenario: RELATIONSHIP-EDIT_RELATIONSHIP-1-04 Edit form pre-fills to-element
    When I GET "/mockups/relationship/1/edit/"
    Then the response status is 200
    And the user should see "Payment API"

  Scenario: RELATIONSHIP-EDIT_RELATIONSHIP-1-05 Happy path — change edge stereotype from calls to depends_on
    When I GET "/mockups/relationship/1/edit/"
    Then the response status is 200
    And the element "relationship-edit-form" should be visible
    # Full edit flow (AT):
    # When the user selects "depends_on" from "edge-stereotype"
    # And the user submits the form
    # Then the change enters the Munin/ChangeSet pipeline

  Scenario: RELATIONSHIP-EDIT_RELATIONSHIP-1-06 Edit is reachable from relationship view page
    When I GET "/mockups/relationship/1/"
    Then the element "edit-relationship-btn" should be visible

  Scenario: RELATIONSHIP-EDIT_RELATIONSHIP-1-07 Edit is reachable from relationship list row
    When I GET "/mockups/relationship/"
    Then the element "edit-rel-1" should be visible

  # ── Navbar integration ────────────────────────────────────────────────────
  Scenario: RELATIONSHIP-EDIT_RELATIONSHIP-1-08 Navbar is visible on edit page
    When I GET "/mockups/relationship/1/edit/"
    Then the response status is 200
    And the element "nav-relationships" should be visible
