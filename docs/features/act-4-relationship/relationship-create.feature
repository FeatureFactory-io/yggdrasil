@wip
Feature: RELATIONSHIP-CREATE_RELATIONSHIP-1 Create New Relationship
  As a Software Architect (Priya)
  I want to create a new relationship between two elements
  So that the model accurately reflects how components depend on or call each other

  # Screen: RELATIONSHIP-CREATE_RELATIONSHIP-1
  # Mockup: /mockups/relationship/create/
  # Testids: relationship-create-page, relationship-create-form, from-element-input,
  #          edge-stereotype-select, to-element-input, relationship-submit-btn
  # Fixture: seed.json (priya@example.com / test-pass-only-1234)
  # Edge stereotype options: calls, depends_on, serves, reads_from, contains

  Background:
    Given the user is logged in as "architect"

  Scenario: RELATIONSHIP-CREATE_RELATIONSHIP-1-01 Create form renders with all required fields
    When I GET "/mockups/relationship/create/"
    Then the response status is 200
    And the element "relationship-create-page" should be visible
    And the element "from-element-input" should be visible
    And the element "edge-stereotype-select" should be visible
    And the element "to-element-input" should be visible
    And the element "relationship-submit-btn" should be visible

  Scenario: RELATIONSHIP-CREATE_RELATIONSHIP-1-02 Edge stereotype dropdown shows all options
    When I GET "/mockups/relationship/create/"
    Then the response status is 200
    And the user should see "calls"
    And the user should see "depends_on"
    And the user should see "serves"
    And the user should see "reads_from"
    And the user should see "contains"

  Scenario: RELATIONSHIP-CREATE_RELATIONSHIP-1-03 Happy path — create Mobile App calls Notification Service
    When I GET "/mockups/relationship/create/"
    Then the response status is 200
    And the element "relationship-create-form" should be visible
    # Full submission flow (AT):
    # When the user enters "Mobile App" into "from-element"
    # And the user selects "calls" from "edge-stereotype"
    # And the user enters "Notification Service" into "to-element"
    # And the user submits the form
    # Then the relationship enters the Munin/ChangeSet pipeline

  Scenario: RELATIONSHIP-CREATE_RELATIONSHIP-1-04 From-element field is required
    When I GET "/mockups/relationship/create/"
    Then the response status is 200
    And the element "from-element-input" should be visible
    # HTML required enforced; TFK-07 for server-side validation scenario

  Scenario: RELATIONSHIP-CREATE_RELATIONSHIP-1-05 To-element field is required
    When I GET "/mockups/relationship/create/"
    Then the response status is 200
    And the element "to-element-input" should be visible

  Scenario: RELATIONSHIP-CREATE_RELATIONSHIP-1-06 Entry from relationship list via create button
    When I GET "/mockups/relationship/"
    Then the element "create-relationship-btn" should be visible
    # Clicking create-relationship-btn navigates to RELATIONSHIP-CREATE_RELATIONSHIP-1

  # ── Navbar integration ────────────────────────────────────────────────────
  Scenario: RELATIONSHIP-CREATE_RELATIONSHIP-1-07 Navbar is visible on create page
    When I GET "/mockups/relationship/create/"
    Then the response status is 200
    And the element "nav-relationships" should be visible
