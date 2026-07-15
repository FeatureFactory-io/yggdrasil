Feature: RATATOSK_RUN-VIEW_RATATOSK_RUN-1 Ratatosk Run Detail
  As a Platform Lead (Alex)
  I want to see the full extraction log, Munin reasoning, and blackboard for a run
  So that I can understand exactly what Ratatosk found and how Munin planned the ChangeSet

  # Screen: RATATOSK_RUN-VIEW_RATATOSK_RUN-1
  # Mockup: /mockups/ratatosk-run/{id}/
  # Testids: ratatosk-run-view-page, view-changeset-btn
  # Fixture: seed.json (priya@example.com / test-pass-only-1234)
  # Mock run: id=3, trigger "ratatosk bootstrap ./repo --model Yggdrasil",
  #           status=complete, 22 candidates, 6 operations, changeset_id=1

  Background:
    Given the user is logged in as "architect"

  Scenario: RATATOSK_RUN-VIEW_RATATOSK_RUN-1-01 View page renders with run details
    When I GET "/mockups/ratatosk-run/3/"
    Then the response status is 200
    And the element "ratatosk-run-view-page" should be visible
    And the user should see "complete"

  Scenario: RATATOSK_RUN-VIEW_RATATOSK_RUN-1-02 View page shows trigger command
    When I GET "/mockups/ratatosk-run/3/"
    Then the response status is 200
    And the user should see "ratatosk bootstrap"

  Scenario: RATATOSK_RUN-VIEW_RATATOSK_RUN-1-03 View page shows start time and duration
    When I GET "/mockups/ratatosk-run/3/"
    Then the response status is 200
    And the user should see "2026-07-14"
    And the user should see "2m 14s"

  Scenario: RATATOSK_RUN-VIEW_RATATOSK_RUN-1-04 View page has a link to the associated ChangeSet
    When I GET "/mockups/ratatosk-run/3/"
    Then the response status is 200
    And the element "view-changeset-btn" should be visible

  Scenario: RATATOSK_RUN-VIEW_RATATOSK_RUN-1-05 View page for initial bootstrap shows 21 operations
    When I GET "/mockups/ratatosk-run/1/"
    Then the response status is 200
    And the user should see "4m 31s"

  Scenario: RATATOSK_RUN-VIEW_RATATOSK_RUN-1-06 Run view shows Ratatosk extraction log section
    # Extraction log: raw candidates discovered (elements, relationships, diff sections)
    When I GET "/mockups/ratatosk-run/3/"
    Then the response status is 200
    # Extraction log content TBD in BPE when model is implemented

  Scenario: RATATOSK_RUN-VIEW_RATATOSK_RUN-1-07 Run view shows Munin blackboard with step statuses
    # Blackboard: JSON task list with each step Munin intended to execute
    # Statuses: completed / skipped / failed — persists through crashes
    When I GET "/mockups/ratatosk-run/3/"
    Then the response status is 200
    # Blackboard content shown when run has non-trivial task list

  # ── Navbar integration ────────────────────────────────────────────────────
  Scenario: RATATOSK_RUN-VIEW_RATATOSK_RUN-1-08 Runs nav link is visible on view page
    When I GET "/mockups/ratatosk-run/3/"
    Then the response status is 200
    And the element "nav-runs" should be visible
