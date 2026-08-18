Feature: VIEW-BROWSE-1 View Browser — Content presets and viewport (Views v2)
  As a Software Architect (Priya)
  I want to control which properties appear on graph nodes, edges, and table columns
  So that I can scan the subgraph for the facts I care about and restore the graph camera in saved Views

  # Component: Content dropdown + extended View payload · CR: VIEW-BROWSE-1_VIEWS_V2
  # Prerequisite: W14 Views v1 (BrowseView ORM, save/load)
  # Testids: content-dropdown, content-option-{slug}, content-editor-*,
  #          save-view-include-viewport
  # Live URL: ?content={preset-slug|custom}
  # Viewport: saved in named View payload when save-view-include-viewport checked (graph mode)
  # Fixture: view_browser_explorer_fixture

  Background:
    Given the user is logged in as "architect"
    And the model "yggdrasil" is loaded with the view browser explorer fixture

  # ── AT: shell ─────────────────────────────────────────────────────────────

  Scenario: VIEW-BROWSE-1-69 Content dropdown renders in graph mode
    When I GET "/models/yggdrasil/views/?mode=graph"
    Then the response status is 200
    And the element "content-dropdown" should be visible

  Scenario: VIEW-BROWSE-1-72 content query param selects built-in preset
    When I GET "/models/yggdrasil/views/?mode=graph&content=current-state"
    Then the response status is 200
    And the element "content-dropdown" should be visible

  Scenario: VIEW-BROWSE-1-77 Content editor panel is available from toolbar
    When I GET "/models/yggdrasil/views/?mode=graph"
    Then the response status is 200
    And the element "content-editor-toggle" should be visible
    And the element "content-editor-panel" should exist
    And the element "content-editor-graph-section" should be visible
    And the element "content-editor-table-section" should not be visible

  @wip
  Scenario: VIEW-BROWSE-1-76 Table mode does not restore graph viewport from saved View
    Given a BrowseView "table-only" exists for model "yggdrasil" with presentation table and a saved viewport
    When I GET "/models/yggdrasil/views/?browse_view=table-only"
    Then the response status is 200
    And the view browser is in table mode
    And the graph canvas controls are hidden

  # ── AT + E2E: content bindings (W15 — @wip until step defs ship) ─────────

  @wip
  Scenario: VIEW-BROWSE-1-70 Minimal preset shows element name on graph nodes
    Given Priya is on the View Browser in graph mode
    When Priya selects content preset "Minimal"
    Then graph node "munin" displays label "munin"
    And graph node "munin" does not display secondary property text

  @wip
  Scenario: VIEW-BROWSE-1-71 Current State preset shows owner on nodes and table columns
    Given Priya is on the View Browser in graph mode
    When Priya selects content preset "Current State"
    Then graph node "auth" displays secondary text containing "platform-team"
    When Priya toggles to table mode
    Then the table view is active
    And the table includes column "Owner"

  @wip
  Scenario: VIEW-BROWSE-1-73 Save View persists content preset in payload
    Given Priya is on the View Browser in graph mode
    And Priya has selected content preset "Current State"
    When Priya saves the current browse session as View "Owners visible"
    Then a BrowseView "owners-visible" exists for model "yggdrasil" owned by Priya
    And the stored View payload includes content preset "current-state"

  @wip
  Scenario: VIEW-BROWSE-1-74 Load named View restores content annotations
    Given Priya has saved a View named "Owners visible" with content preset "current-state"
    When Priya selects View "Owners visible" from the Views dropdown
    Then graph node "auth" displays secondary text containing "platform-team"

  @wip
  Scenario: VIEW-BROWSE-1-75 Saved viewport restores zoom and center on graph load
    Given Priya is on the View Browser in graph mode
    And Priya has panned and zoomed the graph to focus element "munin"
    When Priya saves the current browse session as View "Munin focus" including viewport
    And Priya reloads View "Munin focus"
    Then graph node "munin" is centered in the canvas viewport

  @wip
  Scenario: VIEW-BROWSE-1-78 Priya customizes node secondary fields and applies
    Given Priya is on the View Browser in graph mode
    When Priya opens the Content editor
    And Priya sets node secondary fields to include "Owner" and "Version"
    And Priya applies content bindings
    Then graph node "munin" displays secondary text containing "platform-team"
    And the browser URL includes content=custom

  @wip
  Scenario: VIEW-BROWSE-1-79 Save View persists custom content bindings
    Given Priya is on the View Browser in graph mode
    And Priya has applied custom content with table column "Version"
    When Priya saves the current browse session as View "Version column"
    Then a BrowseView "version-column" exists for model "yggdrasil" owned by Priya
    And the stored View payload includes custom content bindings
