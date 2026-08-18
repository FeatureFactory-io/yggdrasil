Feature: VIEW-BROWSE-1 View Browser — Content via Filters panel (Views v2)
  As a Software Architect (Priya)
  I want visible fields configured alongside browse filters
  So that graph nodes, edges, and table columns show the properties I care about in one Apply action

  # Component: Filters panel field_map · CR: VIEW-BROWSE-1_VIEWS_V2_MOCKUP_RECONCILIATION
  # Prerequisite: W14 Views v1 (BrowseView ORM, save/load)
  # Testids: view-field-sections, view-fields-{stereotype}, view-field-{stereotype}-{path},
  #          filter-package, filter-stereotype, filter-edge-stereotype, apply-filters-btn,
  #          save-view-include-viewport
  # Live URL: repeated field_{stereotype}={path} params
  # Mockup reference: mockups/view/browse.html
  # Fixture: view_browser_explorer_fixture

  Background:
    Given the user is logged in as "architect"
    And the model "yggdrasil" is loaded with the view browser explorer fixture

  # ── AT: Filters-first Content shell ───────────────────────────────────────

  Scenario: VIEW-BROWSE-1-69 Field sections render when stereotypes are selected
    When I GET "/models/yggdrasil/views/?stereotype=component"
    Then the response status is 200
    And the element "view-field-sections" should be visible
    And the element "view-fields-component" should be visible

  Scenario: VIEW-BROWSE-1-72 field query params select visible fields
    When I GET "/models/yggdrasil/views/?stereotype=component&field_component=name&field_component=owner"
    Then the response status is 200
    And the element "view-fields-component" should be visible

  Scenario: VIEW-BROWSE-1-77 Canvas toolbar exposes Filters-first controls
    When I GET "/models/yggdrasil/views/?mode=graph&stereotype=component"
    Then the response status is 200
    And the element "filters-toggle" should be visible
    And the element "apply-filters-btn" should be visible
    And the element "view-field-sections" should be visible

  Scenario: VIEW-BROWSE-1-76 Table mode does not restore graph viewport from saved View
    Given a BrowseView "table-only" exists for model "yggdrasil" with presentation table and a saved viewport
    When I GET "/models/yggdrasil/views/?browse_view=table-only"
    Then the response status is 200
    And the view browser is in table mode
    And the graph canvas controls are hidden

  # ── AT + E2E: field_map rendering (W15) ───────────────────────────────────

  Scenario: VIEW-BROWSE-1-70 Graph node displays Key value lines for visible fields
    Given Priya is on the View Browser in graph mode
    And Priya has applied filters with element stereotype "component" and fields "Name" and "Owner"
    Then graph node "munin" displays label containing "Name: munin"
    And graph node "munin" displays label containing "Owner: platform-team"

  Scenario: VIEW-BROWSE-1-71 Apply Filters updates table columns from field_map
    Given Priya is on the View Browser with element stereotype "component" selected
    And Priya has checked visible fields "Name", "Owner", and "Health"
    When Priya applies browse filters
    And Priya toggles to table mode
    Then the table view is active
    And the table includes column "Owner"

  Scenario: VIEW-BROWSE-1-73 Save View persists field_map in payload
    Given Priya is on the View Browser in graph mode
    And Priya has applied filters with element stereotype "component" and field "Owner" visible
    When Priya saves the current browse session as View "Owners visible"
    Then a BrowseView "owners-visible" exists for model "yggdrasil" owned by Priya
    And the stored View payload includes field_map for stereotype "component"

  Scenario: VIEW-BROWSE-1-74 Load named View restores field_map labels
    Given Priya has saved a View named "Application components" with field_map for "component"
    When Priya selects View "Application components" from the Views dropdown
    Then graph node "auth" displays label containing "Owner: platform-team"

  Scenario: VIEW-BROWSE-1-75 Saved viewport restores after layout fit in graph mode
    Given Priya is on the View Browser in graph mode
    And Priya has panned and zoomed the graph to focus element "munin"
    When Priya saves the current browse session as View "Munin focus" including viewport
    And Priya reloads View "Munin focus"
    Then graph node "munin" is centered in the canvas viewport

  Scenario: VIEW-BROWSE-1-78 Priya toggles visible fields and applies filters
    Given Priya is on the View Browser in graph mode
    When Priya selects element stereotype "component"
    And Priya checks visible field "Jira key" for stereotype "component"
    And Priya applies browse filters
    Then the browser URL includes field_component=
    And graph node "munin" displays label containing "Jira key:"

  Scenario: VIEW-BROWSE-1-79 Package selection narrows stereotype options
    Given Priya is on the View Browser with the filter panel open
    When Priya selects package "application" in the filter panel
    Then the element stereotype filter includes "component"
    And the element stereotype filter does not include "person"
