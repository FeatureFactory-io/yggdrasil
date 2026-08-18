Feature: VIEW-BROWSE-1 View Browser — field_map content (E2E)
  As a Software Architect (Priya)
  I want visible fields to drive table columns and graph labels
  So that saved Views restore the content layout I configured

  Background:
    Given Priya is logged in for View Browser E2E
    And the view browser explorer fixture is seeded for E2E

  Scenario: VIEW-BROWSE-1-71 Apply Filters updates table columns from field_map
    Given Priya is on the View Browser for model "yggdrasil"
    When she selects element stereotype "component" in the filter panel
    And she checks visible field "Owner" for stereotype "component" in the browser
    And she checks visible field "Health" for stereotype "component" in the browser
    And she applies browse filters in the browser
    And she toggles to table mode in the browser
    Then the table view is active in the browser
    And the table includes column "Owner" in the browser

  Scenario: VIEW-BROWSE-1-74 Load named View restores field_map labels
    Given Priya has saved a View named "Application components" with field_map for "component"
    And Priya is on the View Browser for model "yggdrasil"
    When she selects View "Application components" from the Views dropdown
    Then graph node "auth" displays label containing "Owner: platform-team" in the browser
