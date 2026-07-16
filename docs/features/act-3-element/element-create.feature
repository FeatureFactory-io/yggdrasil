@wip
Feature: ELEMENT-CREATE_ELEMENT-1 Create New Element
  As a Software Architect (Priya)
  I want to create a new architecture element with name, stereotype, package, and owner
  So that it enters the model via the Munin/ChangeSet pipeline

  # Screen: ELEMENT-CREATE_ELEMENT-1
  # Mockup: /mockups/element/create/
  # Testids: element-create-page, element-create-form, element-name-input,
  #          element-stereotype-select, element-package-select, element-owner-input,
  #          add-property-btn, add-relationship-btn, diagram-C1, element-submit-btn
  # Fixture: seed.json (priya@example.com / test-pass-only-1234)
  # Stereotype options: System, Container, Component, Person, External
  # Package options: Context, Technology, Application, Code

  Background:
    Given the user is logged in as "architect"

  Scenario: ELEMENT-CREATE_ELEMENT-1-01 Create form renders with all required fields
    When I GET "/mockups/element/create/"
    Then the response status is 200
    And the element "element-create-page" should be visible
    And the element "element-name-input" should be visible
    And the element "element-stereotype-select" should be visible
    And the element "element-package-select" should be visible
    And the element "element-owner-input" should be visible
    And the element "element-submit-btn" should be visible

  Scenario: ELEMENT-CREATE_ELEMENT-1-02 Create form has add-property and add-relationship controls
    When I GET "/mockups/element/create/"
    Then the response status is 200
    And the element "add-property-btn" should be visible
    And the element "add-relationship-btn" should be visible

  Scenario: ELEMENT-CREATE_ELEMENT-1-03 Stereotype dropdown shows all C4 options
    When I GET "/mockups/element/create/"
    Then the response status is 200
    And the user should see "System"
    And the user should see "Container"
    And the user should see "Component"
    And the user should see "Person"
    And the user should see "External"

  Scenario: ELEMENT-CREATE_ELEMENT-1-04 Package dropdown shows all C4 package options
    When I GET "/mockups/element/create/"
    Then the response status is 200
    And the user should see "Context"
    And the user should see "Technology"
    And the user should see "Application"
    And the user should see "Code"

  Scenario: ELEMENT-CREATE_ELEMENT-1-05 Happy path — create Notification Service as Container in Technology
    When I GET "/mockups/element/create/"
    Then the response status is 200
    And the element "element-create-form" should be visible
    # Full submission flow (AT):
    # When the user enters "Notification Service" into "element-name"
    # And the user selects "Container" from "element-stereotype"
    # And the user selects "Technology" from "element-package"
    # And the user enters "platform-team" into "element-owner"
    # And the user submits the form
    # Then the user should see "Notification Service"

  Scenario: ELEMENT-CREATE_ELEMENT-1-06 Form has diagram assignment checkboxes
    When I GET "/mockups/element/create/"
    Then the response status is 200
    And the element "diagram-C1" should be visible

  Scenario: ELEMENT-CREATE_ELEMENT-1-07 Name field is required
    When I GET "/mockups/element/create/"
    Then the response status is 200
    And the element "element-name-input" should be visible
    # HTML required attribute enforced; TFK-07 for server-side validation scenario

  Scenario: ELEMENT-CREATE_ELEMENT-1-08 Entry from element list via create button
    When I GET "/mockups/element/"
    Then the element "create-element-btn" should be visible
    # Clicking create-element-btn navigates to ELEMENT-CREATE_ELEMENT-1

  # ── Navbar integration ────────────────────────────────────────────────────
  Scenario: ELEMENT-CREATE_ELEMENT-1-09 Navbar is visible on create page
    When I GET "/mockups/element/create/"
    Then the response status is 200
    And the element "nav-elements" should be visible
