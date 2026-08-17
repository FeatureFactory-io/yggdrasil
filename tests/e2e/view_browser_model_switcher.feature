Feature: View Browser model switcher E2E
  As Priya the architect
  I want to switch Models from the navigator dropdown
  So that I can browse a different graph without leaving the explorer

  Scenario: VIEW-BROWSE-1-51 Selecting another Model reloads the navigator for that graph
    Given Priya is logged in for View Browser E2E
    And the E2E models "yggdrasil" and "payments" are seeded
    And Priya is on the View Browser for model "yggdrasil"
    When she selects model "payments" in the model switcher
    Then she is on "/models/payments/views/"
    And the element "browser-model-name" shows "Payments"
    And she does not see "munin" in the navigator
