@wip
Feature: CHANGESET-LIST+FIND-1 ChangeSet Queue
  As a Development Team Lead (Marcus)
  I want to see all pending and applied ChangeSets in a filterable list
  So that I can choose which ones to review and apply

  # Screen: CHANGESET-LIST+FIND-1
  # Mockup: /mockups/changeset/
  # Testids: changeset-list-page, filter-status, filter-source,
  #          changeset-row-{id}, review-changeset-{id}
  # Fixture: seed.json (priya@example.com / test-pass-only-1234)
  # Mock data: 3 ChangeSets — pending (run-003, 6 ops), applied (run-002, 2 ops), applied (run-001, 21 ops)

  Background:
    Given the user is logged in as "architect"

  Scenario: CHANGESET-LIST+FIND-1-01 List page renders with all 3 mock ChangeSets
    When I GET "/mockups/changeset/"
    Then the response status is 200
    And the element "changeset-list-page" should be visible
    And the element "changeset-row-1" should be visible
    And the element "changeset-row-2" should be visible
    And the element "changeset-row-3" should be visible

  Scenario: CHANGESET-LIST+FIND-1-02 List shows Run ID, Source, Submitted, Operations, Mode, Status columns
    When I GET "/mockups/changeset/"
    Then the response status is 200
    And the user should see "run-003"
    And the user should see "ratatosk"
    And the user should see "pending"
    And the user should see "applied"
    And the user should see "manual"
    And the user should see "auto"

  Scenario: CHANGESET-LIST+FIND-1-03 Pending ChangeSet has a Review action link
    When I GET "/mockups/changeset/"
    Then the response status is 200
    And the element "review-changeset-1" should be visible

  Scenario: CHANGESET-LIST+FIND-1-04 Status filter is present
    When I GET "/mockups/changeset/"
    Then the response status is 200
    And the element "filter-status" should be visible

  Scenario: CHANGESET-LIST+FIND-1-05 Source filter is present
    When I GET "/mockups/changeset/"
    Then the response status is 200
    And the element "filter-source" should be visible

  Scenario: CHANGESET-LIST+FIND-1-06 ChangeSet from human source is shown
    When I GET "/mockups/changeset/"
    Then the response status is 200
    And the user should see "human"
    And the element "changeset-row-2" should be visible

  Scenario: CHANGESET-LIST+FIND-1-07 Initial bootstrap ChangeSet (21 operations) is visible
    When I GET "/mockups/changeset/"
    Then the response status is 200
    And the user should see "run-001"
    And the user should see "21"

  # ── Navbar integration ────────────────────────────────────────────────────
  Scenario: CHANGESET-LIST+FIND-1-08 Changesets nav link is visible
    When I GET "/mockups/changeset/"
    Then the response status is 200
    And the element "nav-changesets" should be visible
