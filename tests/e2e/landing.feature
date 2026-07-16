Feature: Landing page
  As a visitor
  I want to see the Yggdrasil landing page
  So that I know the application is running

  Scenario: Visitor sees the landing page
    Given the user is on the "landing" page
    Then the user should see "Yggdrasil"
