Feature: VIEW-BROWSE-1 View browser with multi-level filters
  As an enterprise architect
  I want to filter the graph by package, stereotype, and properties
  So that I can answer strategic questions in seconds

  Background:
    Given I am logged in as "elena@example.com"

  Scenario: VIEW-BROWSE-01 Apply filters and see table results
    When I navigate to the view browser page
    Then I should see the page "VIEW-BROWSE-1"
    When I select package "Business View"
    And I select stereotype "Capability"
    And I apply filters
    Then I should see filtered results in the table

  Scenario: VIEW-BROWSE-02 Toggle graph visualization
    When I navigate to the view browser page
    And I apply filters
    And I click the "Graph" toggle
    Then I should see the cytoscape graph canvas
    And the graph should display nodes matching my filters
