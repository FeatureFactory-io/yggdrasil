Feature: VIEW-BROWSE-1 View Browser — saved viewport restore (E2E)
  As a Software Architect (Priya)
  I want a saved View to restore my graph zoom and pan
  So that I can return to the same canvas focus after reload

  Background:
    Given Priya is logged in for View Browser E2E
    And the view browser explorer fixture is seeded for E2E

  Scenario: VIEW-BROWSE-1-75 Saved viewport restores after layout fit in graph mode
    Given Priya is on the View Browser for model "yggdrasil"
    When she focuses graph element "munin" with zoom and pan
    And she saves the current view as "Munin focus" including viewport
    And she reloads saved view "Munin focus"
    Then graph element "munin" is visible in the canvas viewport
