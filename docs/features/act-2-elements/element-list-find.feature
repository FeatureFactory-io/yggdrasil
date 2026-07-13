Feature: ELEMENT-LIST+FIND-1 Elements list with search and filter
  As an enterprise architect
  I want to browse and filter elements in the graph
  So that I can find what supports a given capability

  Background:
    Given I am logged in as "elena@example.com"
    And the following elements exist:
      | name          | stereotype  | package        | health |
      | Payment API   | Application | Technology View| good   |
      | Order Service | Application | Technology View| warn   |

  Scenario: ELEMENT-LIST+FIND-01 View all elements
    When I navigate to the elements list page
    Then I should see the page "ELEMENT-LIST+FIND-1"
    And I should see "Payment API" in the results table
    And I should see "Order Service" in the results table

  Scenario: ELEMENT-LIST+FIND-02 Filter by stereotype
    When I navigate to the elements list page
    And I filter by stereotype "Application"
    Then I should see "Payment API" in the results table
    And I should not see elements with other stereotypes

  Scenario: ELEMENT-LIST+FIND-03 Search by name
    When I navigate to the elements list page
    And I search for "Payment"
    Then I should see "Payment API" in the results table
    And I should not see "Order Service" in the results table
