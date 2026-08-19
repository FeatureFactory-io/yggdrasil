Feature: VIEW-BROWSE-1 View Browser — Element Navigator (left panel)
  As a Software Architect (Priya)
  I want a left panel to browse the depth-scoped element tree
  So that I can jump to any node without relying on the graph alone

  # Component: left panel · Pattern: Mimir Content Browser FOB-CONTENT-BROWSER-20..27
  # Production: /models/{slug}/views/ · alias GET /views/ 302s to default model
  # Mockup reference: /mockups/view/browse/ (DEBUG only — not an AT target)
  # Testids: browser-nav-panel, browser-model-name, browser-model-switcher,
  #          browser-model-menu, browser-model-option-{slug},
  #          browser-search-input, browser-element-tree, nav-toggle-{slug},
  #          nav-element-{slug}, browser-toggle-nav-panel
  # Fixture: view_browser_model (pytest) · extend via TFK-07 for AT behave load
  # Depends: VIEW-BROWSE-1-16 three-panel shell

  Background:
    Given the user is logged in as "architect"
    And the model "yggdrasil" is loaded with the view browser explorer fixture

  # ── AT: shell + static HTML ───────────────────────────────────────────────

  Scenario: VIEW-BROWSE-1-17 Navigator panel renders with model name and element tree
    When I GET "/models/yggdrasil/views/?mode=graph"
    Then the response status is 200
    And the element "browser-nav-panel" should be visible
    And the element "browser-model-name" should be visible
    And the element "browser-element-tree" should be visible

  Scenario: VIEW-BROWSE-1-25 Default navigator groups elements under top-level packages
    When I GET "/models/yggdrasil/views/?mode=graph"
    Then the response status is 200
    And the element "package-toggle-application" should be visible
    And the element "nav-element-auth" should be visible
    And the element "browser-search-input" should be visible
    And the user should see "Yggdrasil"

  Scenario: VIEW-BROWSE-1-25b Package navigator lists diagrams as normal tree nodes
    When Elena opens the View Browser mockup in graph mode
    And she expands the Technology package in the navigator
    Then she sees diagram "Container Diagram C1" under Technology
    And the diagram row uses the same layout as element rows
    When she clicks diagram "Container Diagram C1" in the navigator
    Then DIAGRAM-EDITOR-1 opens for that diagram

  Scenario: VIEW-BROWSE-1-18 Traversal tree at depth 1 shows filter roots only
    When I GET "/models/yggdrasil/views/?mode=graph&stereotype=component&depth=1"
    Then the response status is 200
    And the element "nav-element-auth" should be visible
    And the element "nav-element-graph" should be visible
    And the element "nav-element-munin" should be visible
    And the element "nav-element-redis" should not be visible

  Scenario: VIEW-BROWSE-1-19 Depth 2 expands navigator with one-hop dependents
    When I GET "/models/yggdrasil/views/?mode=graph&stereotype=component&depth=2"
    Then the response status is 200
    And the user should see "auth"
    And the user should see "graph"
    And the user should see "munin"
    And the user should see "llm"

  Scenario: VIEW-BROWSE-1-19b Depth 3 reaches infrastructure dependents
    When I GET "/models/yggdrasil/views/?mode=graph&stereotype=component&depth=3"
    Then the response status is 200
    And the user should see "Redis"

  Scenario: VIEW-BROWSE-1-20 Navigator collapse toggle control is present
    When I GET "/models/yggdrasil/views/?mode=graph"
    Then the response status is 200
    And the element "browser-toggle-nav-panel" should be visible

  # ── E2E: interaction (Playwright) ─────────────────────────────────────────

  @wip
  Scenario: VIEW-BROWSE-1-21 Clicking a navigator chevron expands and collapses child nodes
    # TFK-07: step `When the user toggles navigator node "{slug}" in the view browser`
    Given Priya is on the View Browser in graph mode with depth 3
    When she toggles the "munin" node in the navigator
    Then she sees "llm" in the navigator
    When she toggles the "munin" node in the navigator again
    Then "llm" is hidden in the navigator element list

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

  # ── Model switcher (CR: VIEW-BROWSE-1 model switcher) ─────────────────────
  # Canonical URL: /models/{slug}/views/ · alias GET /views/ 302s to default
  # Scenarios 17–20 use canonical URLs; 49/53 exercise the /views/ alias.

  Scenario: ✅ VIEW-BROWSE-1-48 Model switcher lists Models the user can read
    Given the models "yggdrasil" and "payments" exist and the architect can read both
    When I GET "/models/yggdrasil/views/?mode=graph"
    Then the response status is 200
    And the element "browser-model-switcher" should be visible
    And the element "browser-model-name" should be visible
    And the element "browser-model-option-yggdrasil" should be visible
    And the element "browser-model-option-payments" should be visible
    And the user should see "Yggdrasil"

  Scenario: ✅ VIEW-BROWSE-1-49 Unscoped /views/ redirects to the default Model
    When I GET "/views/"
    Then the response status is 302
    And the Location header starts with "/models/yggdrasil/views/"

  Scenario: ✅ VIEW-BROWSE-1-50 Canonical browse URL includes the Model slug
    When I GET "/models/yggdrasil/views/?mode=graph"
    Then the response status is 200
    And the element "browser-nav-panel" should be visible
    And the user should see "Yggdrasil"

  Scenario: ✅ VIEW-BROWSE-1-51 Selecting another Model reloads the navigator for that graph
    Given the models "yggdrasil" and "payments" exist and the architect can read both
    And Priya is on the View Browser for model "yggdrasil"
    When she selects model "payments" in the model switcher
    Then she is on "/models/payments/views/"
    And the element "browser-model-name" shows "Payments"
    And she does not see "munin" in the navigator

  Scenario: ✅ VIEW-BROWSE-1-52 Unknown Model slug returns 404
    Given the user is logged in as "architect"
    When I GET "/models/does-not-exist/views/"
    Then the response status is 404

  Scenario: ✅ VIEW-BROWSE-1-53 Zero Models shows empty state and disables the switcher
    Given the architect can read no models
    When I GET "/views/"
    Then the response status is 200
    And the user should see "No models yet"
    And the element "browser-model-switcher" is disabled

  Scenario: ✅ VIEW-BROWSE-1-54 Model switcher has no create-model action
    Given the models "yggdrasil" and "payments" exist and the architect can read both
    When I GET "/models/yggdrasil/views/?mode=graph"
    Then the response status is 200
    And the user should not see "Create model"

  # ── Depth traversal (CR: VIEW-BROWSE-1 depth BFS) ─────────────────────────

  @wip
  Scenario: VIEW-BROWSE-1-59 Navigator chevron toggle does not change URL depth
    # TFK-07: local disclosure only
    Given Priya is on the View Browser in graph mode with depth 2
    When she toggles the "auth" node in the navigator
    Then the URL does not contain a changed depth parameter

  @wip
  Scenario: VIEW-BROWSE-1-60 Traversal tree nests children under root nodes
    When I GET "/views/?mode=graph&stereotype=container&depth=2"
    Then the response status is 200
    And the element "browser-element-tree" should be visible
    And the navigator nests "auth" under a root container node
