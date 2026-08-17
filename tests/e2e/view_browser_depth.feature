Feature: View Browser depth slider in graph mode
  As Priya the architect
  I want the Levels slider to redraw the graph without leaving graph mode
  So that I can explore deeper relationships without losing context

  Scenario: VIEW-BROWSE-1-60 Changing depth in graph mode stays on graph view
    Given Priya is logged in for View Browser E2E
    And the view browser explorer fixture is seeded for E2E
    And Priya is on the View Browser for model "yggdrasil"
    When she sets the view browser depth slider to "3"
    Then the view browser is in graph mode in the browser
    And the graph view is visible in the browser
