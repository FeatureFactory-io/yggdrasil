Feature: CHANGESET-LIST+FIND-1 Change review queue
  As an enterprise architect
  I want to review Ratatosk-proposed changes before they apply
  So that low-confidence discoveries do not corrupt the graph

  Background:
    Given I am logged in as "elena@example.com"
    And a pending changeset exists from Ratatosk run "run-001"

  Scenario: CHANGESET-LIST+FIND-01 View pending changesets
    When I navigate to the changesets list page
    Then I should see the page "CHANGESET-LIST+FIND-1"
    And I should see changeset "run-001" with status "Pending"

  Scenario: CHANGESET-VIEW-01 Approve high-confidence items
    When I open changeset "run-001"
    And I click "Approve All High Confidence"
    Then high-confidence items should be applied to the graph
    And low-confidence items should remain in the queue
