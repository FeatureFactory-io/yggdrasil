@wip
Feature: RATATOSK_RUN-LIST+FIND-1 Ratatosk Run History List
  As a Platform Lead (Alex)
  I want to see a list of all Ratatosk runs with their status and outcomes
  So that I can track model update history and diagnose failures

  # Screen: RATATOSK_RUN-LIST+FIND-1
  # Mockup: /mockups/ratatosk-run/
  # Testids: ratatosk-run-list-page, run-row-{id}, view-run-{id}
  # Fixture: seed.json (priya@example.com / test-pass-only-1234)
  # Mock data: 3 runs — run id=3 (bootstrap, 2m14s), run id=2 (manual GUI, 8s), run id=1 (initial bootstrap, 4m31s)

  Background:
    Given the user is logged in as "architect"

  Scenario: RATATOSK_RUN-LIST+FIND-1-01 List page renders with all 3 mock runs
    When I GET "/mockups/ratatosk-run/"
    Then the response status is 200
    And the element "ratatosk-run-list-page" should be visible
    And the element "run-row-1" should be visible
    And the element "run-row-2" should be visible
    And the element "run-row-3" should be visible

  Scenario: RATATOSK_RUN-LIST+FIND-1-02 List shows Run ID, Connector, Started, Duration, Operations, Status columns
    When I GET "/mockups/ratatosk-run/"
    Then the response status is 200
    And the user should see "complete"
    And the user should see "2026-07-14"
    And the user should see "2m 14s"
    And the user should see "4m 31s"

  Scenario: RATATOSK_RUN-LIST+FIND-1-03 Each run row has a View action link
    When I GET "/mockups/ratatosk-run/"
    Then the response status is 200
    And the element "view-run-1" should be visible
    And the element "view-run-2" should be visible
    And the element "view-run-3" should be visible

  Scenario: RATATOSK_RUN-LIST+FIND-1-04 Run list shows trigger descriptions
    When I GET "/mockups/ratatosk-run/"
    Then the response status is 200
    And the user should see "ratatosk bootstrap"
    And the user should see "manual GUI create"

  Scenario: RATATOSK_RUN-LIST+FIND-1-05 Run list shows ChangeSet counts
    When I GET "/mockups/ratatosk-run/"
    Then the response status is 200
    And the user should see "6"
    And the user should see "21"

  # ── Navbar integration ────────────────────────────────────────────────────
  Scenario: RATATOSK_RUN-LIST+FIND-1-06 Runs nav link is visible
    When I GET "/mockups/ratatosk-run/"
    Then the response status is 200
    And the element "nav-runs" should be visible
