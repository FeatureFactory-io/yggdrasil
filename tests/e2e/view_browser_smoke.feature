@wip
Feature: View Browser E2E smoke
  As Priya the architect
  I want the three-panel View Browser to load in a real browser
  So that E2E can verify the navigator shell

  # Blocked on E2E auth (gap #5) — run once login page ships

  Scenario: Priya opens View Browser and sees navigator panel
    Given Priya is on the View Browser
    Then the element "browser-nav-panel" should be visible
