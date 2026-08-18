Feature: VIEW-BROWSE-1 View Browser — Property Inspector (right panel)
  As a Software Architect (Priya)
  I want a right panel to read element and relationship properties
  So that I can inspect the graph without leaving the View Browser

  # Component: right inspector · Pattern: Mimir Content Browser FOB-CONTENT-BROWSER-08..10
  # Production: /models/{slug}/views/ · Mockup: /mockups/view/browse/
  # Testids: browser-inspector-panel, browser-toggle-inspector-panel,
  #          inspector-empty, inspector-content, inspector-element-{id},
  #          inspector-relationship-{id}, inspector-open-full-{id}
  # Inspector partials: GET /models/{slug}/views/inspector/element/<pk>/ · relationship/<pk>/
  # Fixture: view_browser_explorer_fixture (TFK-07)

  Background:
    Given the user is logged in as "architect"
    And the model "yggdrasil" is loaded with the view browser explorer fixture

  # ── AT: shell ─────────────────────────────────────────────────────────────

  Scenario: VIEW-BROWSE-1-25 Inspector panel renders with empty-state prompt in graph mode
    When I GET "/models/yggdrasil/views/?mode=graph"
    Then the response status is 200
    And the element "browser-inspector-panel" should be visible
    And the element "inspector-empty" should be visible
    And the user should see "Select an element or relationship"

  Scenario: VIEW-BROWSE-1-26 Inspector collapse toggle control is present in graph mode
    When I GET "/models/yggdrasil/views/?mode=graph"
    Then the response status is 200
    And the element "browser-toggle-inspector-panel" should be visible

  Scenario: VIEW-BROWSE-1-47 Inspector panel is visible in default graph mode
    When I GET "/models/yggdrasil/views/"
    Then the response status is 200
    And the view browser is in graph mode
    And the element "browser-inspector-panel" should be visible

  Scenario: VIEW-BROWSE-1-47b Inspector panel is hidden in table mode
    When I GET "/models/yggdrasil/views/?mode=table"
    Then the response status is 200
    And the view browser is in table mode
    And the element "browser-inspector-panel" should not be visible

  # ── AT: embed partials (no navbar — IA § inspector embed mode) ────────────

  Scenario: VIEW-BROWSE-1-27 Element inspector partial returns properties without page chrome
    When I GET the view browser inspector element partial for "auth"
    Then the response status is 200
    And the user should see "Properties"
    And the user should not see "nav-view-browser"
    And the response is an embed partial

  Scenario: VIEW-BROWSE-1-28 Relationship inspector partial returns endpoints without page chrome
    When I GET the view browser inspector relationship partial from "munin" to "llm"
    Then the response status is 200
    And the user should see "depends_on"
    And the user should not see "nav-view-browser"
    And the response is an embed partial

  # ── E2E: inspector behaviour ────────────────────────────────────────────

  @wip
  Scenario: VIEW-BROWSE-1-29 Selecting an element shows properties and provenance in inspector
    Given Priya is on the View Browser in graph mode
    When she selects "munin" in the navigator
    Then the inspector shows element "munin"
    And the inspector shows stereotype "Component"
    And the inspector shows package "Application"
    And the inspector shows confidence for "munin"
    And the inspector lists connected relationships for "munin"

  @wip
  Scenario: VIEW-BROWSE-1-30 Selecting a relationship shows endpoints and edge stereotype
    Given Priya is on the View Browser in graph mode
    When she selects the relationship "munin" depends_on "llm" in the graph
    Then the inspector shows relationship "munin" to "llm"
    And the inspector shows edge stereotype "depends_on"
    And the inspector links to endpoint "munin"
    And the inspector links to endpoint "llm"

  @wip
  Scenario: VIEW-BROWSE-1-31 Clicking a relationship row in the inspector selects that edge
    Given Priya is on the View Browser in graph mode
    And she has selected element "munin" in the navigator
    When she clicks the relationship row "munin" depends_on "llm" in the inspector
    Then the inspector shows relationship "munin" to "llm"
    And the graph edge "munin" depends_on "llm" is selected

  @wip
  Scenario: VIEW-BROWSE-1-32 Open full view navigates to ELEMENT-VIEW_ELEMENT-1
    Given Priya is on the View Browser in graph mode
    When she selects "auth" in the navigator
    And she clicks "Open full view" in the inspector
    Then she is on the element detail page for "auth"

  @wip
  Scenario: VIEW-BROWSE-1-33 Clearing selection resets inspector to empty state
    Given Priya is on the View Browser in graph mode
    And she has selected element "web" in the navigator
    When she clears the view browser selection
    Then the inspector shows the empty-state prompt
    And no graph node is selected

  @wip
  Scenario: VIEW-BROWSE-1-34 Collapsing the inspector panel hides it and expands the canvas
    Given Priya is on the View Browser with the inspector expanded
    When she clicks the inspector collapse toggle
    Then the element "browser-inspector-panel" is collapsed
    And the graph canvas fills the freed horizontal space
