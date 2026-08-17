Feature: VIEW-BROWSE-1 View Browser — Graph Canvas (centre panel)
  As a Software Architect (Priya)
  I want a full-size graph canvas with table fallback
  So that I can explore filtered subgraphs visually and switch to tabular data when needed

  # Component: centre canvas · Pattern: Mimir FOB-CONTENT-BROWSER-03, 07
  # Production: /models/{slug}/views/ · graph data: GET /models/{slug}/views/graph.json
  # Testids: graph-cy-container, toggle-table, toggle-graph, results-container,
  #          graph-replot-btn, graph-zoom-in, graph-zoom-out, graph-zoom-fit,
  #          graph-node-count, browser-canvas-controls
  # Fixture: view_browser_explorer_fixture

  Background:
    Given the user is logged in as "architect"
    And the model "yggdrasil" is loaded with the view browser explorer fixture

  # ── AT: graph JSON, mode SSR, canvas controls ─────────────────────────────

  Scenario: VIEW-BROWSE-1-35 Graph JSON endpoint returns nodes and edges for current filters
    When I GET "/models/yggdrasil/views/graph.json?package=application"
    Then the response status is 200
    And the user should see "elements"
    And the user should see "edges"

  Scenario: VIEW-BROWSE-1-36 View-mode toggles and results container render in canvas toolbar
    When I GET "/models/yggdrasil/views/"
    Then the response status is 200
    And the element "toggle-table" should be visible
    And the element "toggle-graph" should be visible
    And the element "results-container" should be visible

  Scenario: VIEW-BROWSE-1-37 Table mode shows element rows inside the canvas panel
    When I GET "/models/yggdrasil/views/?view=table"
    Then the response status is 200
    And the view browser is in table mode
    And the table view is active
    And the user should see "auth"
    And the user should see "graph"
    And the user should see "element-row-"

  Scenario: VIEW-BROWSE-1-45 Table mode hides graph canvas and explorer chrome
    When I GET "/models/yggdrasil/views/?view=table"
    Then the response status is 200
    And the view browser is in table mode
    And the graph-only panels are hidden
    And the element "graph-cy-container" should not be visible
    And the element "graph-replot-btn" should not be visible
    And the element "browser-canvas-controls" should not be visible

  Scenario: VIEW-BROWSE-1-46 Graph mode shows canvas controls and cytoscape container
    When I GET "/models/yggdrasil/views/"
    Then the response status is 200
    And the view browser is in graph mode
    And the graph view is active
    And the page uses the full-height view browser layout
    And the element "graph-cy-container" should be visible
    And the graph canvas controls are visible

  # ── E2E: cytoscape interactions ─────────────────────────────────────────

  @wip
  Scenario: VIEW-BROWSE-1-38 Graph mode is the default view on first load
    Given Priya is on the View Browser
    Then the graph view is active
    And the cytoscape canvas is visible
    And the table view is hidden

  @wip
  Scenario: VIEW-BROWSE-1-39 Toggling to graph mode shows cytoscape and hides table rows
    Given Priya is on the View Browser
    When she clicks the graph view toggle
    Then the graph view is active
    And the cytoscape canvas is visible
    And the table view is hidden

  @wip
  Scenario: VIEW-BROWSE-1-40 Clicking a graph node selects the element and opens the inspector
    Given Priya is on the View Browser in graph mode
    When she clicks the graph node "graph"
    Then the graph node "graph" is selected
    And the inspector shows element "graph"
    And the navigator row for "graph" is highlighted

  @wip
  Scenario: VIEW-BROWSE-1-41 Clicking a graph edge selects the relationship in the inspector
    Given Priya is on the View Browser in graph mode
    When she clicks the graph edge "changeset" depends_on "graph"
    Then the inspector shows relationship "changeset" to "graph"

  @wip
  Scenario: VIEW-BROWSE-1-42 Zoom and replot controls fit and resize the graph viewport
    Given Priya is on the View Browser in graph mode
    When she clicks the graph replot control
    Then the cytoscape canvas is visible
    When she clicks the graph zoom fit control
    Then all visible graph nodes are within the canvas viewport
    When she clicks the graph zoom in control
    Then the graph zoom level increases

  @wip
  Scenario: VIEW-BROWSE-1-43 Applying a package filter reloads graph JSON and navigator scope
    Given Priya is on the View Browser in graph mode
    When she applies package filter "technology"
    Then she sees "Redis" in the navigator
    And she does not see "munin" in the navigator
    And the graph shows "Redis"
    And the graph does not show "munin"
    And the URL contains "package=technology"

  @wip
  Scenario: VIEW-BROWSE-1-44 Empty filter result shows empty state in table and graph
    Given Priya is on the View Browser
    When she applies stereotype filter "Person" and package filter "technology"
    Then she sees "No elements match the current filters"
    And the graph shows an empty-state message

  # ── Depth traversal (CR: VIEW-BROWSE-1 depth BFS) ─────────────────────────

  Scenario: VIEW-BROWSE-1-55 Depth slider renders in graph mode canvas toolbar
    When I GET "/models/yggdrasil/views/?view=graph"
    Then the response status is 200
    And the element "browser-depth-slider" should be visible
    And the element "browser-depth-value" should be visible

  Scenario: VIEW-BROWSE-1-56 Graph JSON respects depth parameter
    Given the model "yggdrasil" is loaded with the view browser explorer fixture
    When I GET "/models/yggdrasil/views/graph.json?stereotype=component&depth=1"
    Then the response status is 200
    And the user should see "auth"
    And the user should not see "Redis"
    When I GET "/models/yggdrasil/views/graph.json?stereotype=component&depth=2"
    Then the response status is 200
    And the user should see "llm"
    And the user should not see "Redis"
    When I GET "/models/yggdrasil/views/graph.json?stereotype=component&depth=3"
    Then the response status is 200
    And the user should see "Redis"

  Scenario: VIEW-BROWSE-1-57 Depth query param syncs with slider default
    When I GET "/models/yggdrasil/views/?view=graph&depth=3"
    Then the response status is 200
    And the depth slider value is 3

  Scenario: VIEW-BROWSE-1-58 Table rows match depth-scoped node set
    When I GET "/models/yggdrasil/views/?stereotype=component&depth=1"
    Then the response status is 200
    And the user should see "auth"
    And the user should not see "Redis"
