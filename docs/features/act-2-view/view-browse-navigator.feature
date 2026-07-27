Feature: VIEW-BROWSE-1 View Browser — Package & Element Navigator (left panel)
  As a Software Architect (Priya)
  I want a left panel to browse packages and elements in the model
  So that I can jump to any node without relying on the graph alone

  # Component: left panel · Pattern: Mimir Content Browser FOB-CONTENT-BROWSER-20..27
  # Production: /views/ · Mockup reference: /mockups/view/browse/ (DEBUG only — not an AT target)
  # Testids: browser-nav-panel, browser-model-name, browser-search-input,
  #          browser-package-tree, package-toggle-{slug}, nav-element-{id},
  #          browser-toggle-nav-panel
  # Fixture: view_browser_model (pytest) · extend via TFK-07 for AT behave load
  # Depends: VIEW-BROWSE-1-16 three-panel shell

  Background:
    Given the user is logged in as "architect"
    And the model "yggdrasil" is loaded with the view browser explorer fixture

  # ── AT: shell + static HTML ───────────────────────────────────────────────

  Scenario: VIEW-BROWSE-1-17 Navigator panel renders with model name and package tree
    When I GET "/views/?view=graph"
    Then the response status is 200
    And the element "browser-nav-panel" should be visible
    And the element "browser-model-name" should be visible
    And the element "browser-package-tree" should be visible
    And the element "browser-search-input" should be visible
    And the user should see "Yggdrasil"

  Scenario: VIEW-BROWSE-1-18 Package tree lists Context, Application, and Technology with counts
    When I GET "/views/?view=graph"
    Then the response status is 200
    And the element "package-toggle-context" should be visible
    And the element "package-toggle-application" should be visible
    And the element "package-toggle-technology" should be visible
    And the user should see "Application"

  Scenario: VIEW-BROWSE-1-19 Navigator lists elements under expanded Application package
    When I GET "/views/"
    Then the response status is 200
    And the user should see "auth"
    And the user should see "graph"
    And the user should see "munin"
    And the user should see "web"

  Scenario: VIEW-BROWSE-1-20 Navigator collapse toggle control is present
    When I GET "/views/?view=graph"
    Then the response status is 200
    And the element "browser-toggle-nav-panel" should be visible

  # ── E2E: interaction (Playwright) ─────────────────────────────────────────

  @wip
  Scenario: VIEW-BROWSE-1-21 Clicking a package chevron expands and collapses its elements
    # TFK-07: step `When the user toggles package "{slug}" in the view browser navigator`
    Given Priya is on the View Browser
    When she toggles the "technology" package in the navigator
    Then she sees "Redis" in the navigator
    When she toggles the "technology" package in the navigator again
    Then "Redis" is hidden in the navigator element list

  @wip
  Scenario: VIEW-BROWSE-1-22 Navigator search filters visible element rows by name
    # TFK-07: step `When the user searches the view browser navigator for "{query}"`
    Given Priya is on the View Browser
    When she searches the navigator for "mun"
    Then she sees "munin" in the navigator
    And she does not see "auth" in the navigator
    When she clears the navigator search
    Then she sees "auth" in the navigator

  @wip
  Scenario: VIEW-BROWSE-1-23 Clicking a navigator element row selects it across panels
    # TFK-07: steps for cross-panel selection sync (navigator + graph + inspector)
    Given Priya is on the View Browser
    When she selects "munin" in the navigator
    Then the navigator row for "munin" is highlighted
    And the inspector shows element "munin"
    And the graph node "munin" is selected

  @wip
  Scenario: VIEW-BROWSE-1-24 Collapsing the navigator panel hides it and expands the canvas
    Given Priya is on the View Browser with the navigator expanded
    When she clicks the navigator collapse toggle
    Then the element "browser-nav-panel" is collapsed
    And the graph canvas fills the freed horizontal space
