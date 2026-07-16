@wip
Feature: CHANGESET-VIEW_CHANGESET-1 Review ChangeSet Operations
  As a Development Team Lead (Marcus)
  I want to review each planned graph operation and accept, reject, or redirect it
  So that only accurate changes are applied to the architecture model

  # Screen: CHANGESET-VIEW_CHANGESET-1
  # Mockup: /mockups/changeset/{id}/
  # Testids: changeset-view-page, accept-high-confidence-btn, reject-all-btn, accept-all-btn,
  #          rollback-btn, op-row-{id}, accept-op-{id}, reject-op-{id}, do-other-op-{id},
  #          do-other-input-{id}, do-other-submit-{id}
  # Fixture: seed.json (priya@example.com / test-pass-only-1234)
  # Mock data: ChangeSet id=1 (run-003, pending, 6 ops):
  #   op1: Add Element "Notification Service" → Container/Technology (confidence 0.92)
  #   op2: Link Element Notification Service →depends_on→ Payment API (0.91)
  #   op3: Add to Diagram Notification Service → Container Diagram C1 (0.65)
  #   op4: Update Element Order Domain: owner → fulfillment-team (0.88)
  #   op5: Delete Element LegacyBatch (0.95)
  #   op6: Add Relationship Mobile App →calls→ Notification Service (0.78)

  Background:
    Given the user is logged in as "architect"

  Scenario: CHANGESET-VIEW_CHANGESET-1-01 View page renders with header and operations list
    When I GET "/mockups/changeset/1/"
    Then the response status is 200
    And the element "changeset-view-page" should be visible
    And the user should see "run-003"
    And the user should see "ratatosk"
    And the user should see "pending"

  Scenario: CHANGESET-VIEW_CHANGESET-1-02 Page shows Munin's summary reasoning
    When I GET "/mockups/changeset/1/"
    Then the response status is 200
    And the user should see "I analysed 3 services"
    And the user should see "16 elements"
    And the user should see "24 relationships"

  Scenario: CHANGESET-VIEW_CHANGESET-1-03 All 6 operation rows are visible
    When I GET "/mockups/changeset/1/"
    Then the response status is 200
    And the element "op-row-1" should be visible
    And the element "op-row-2" should be visible
    And the element "op-row-3" should be visible
    And the element "op-row-4" should be visible
    And the element "op-row-5" should be visible
    And the element "op-row-6" should be visible

  Scenario: CHANGESET-VIEW_CHANGESET-1-04 Each operation row shows op type and detail
    When I GET "/mockups/changeset/1/"
    Then the response status is 200
    And the user should see "Add Element"
    And the user should see "Notification Service"
    And the user should see "Container / Technology"
    And the user should see "Delete Element"
    And the user should see "LegacyBatch"

  Scenario: CHANGESET-VIEW_CHANGESET-1-05 Each operation row has Accept, Reject, Do Other actions
    When I GET "/mockups/changeset/1/"
    Then the response status is 200
    And the element "accept-op-1" should be visible
    And the element "reject-op-1" should be visible
    And the element "do-other-op-1" should be visible

  Scenario: CHANGESET-VIEW_CHANGESET-1-06 Bulk action buttons are present
    When I GET "/mockups/changeset/1/"
    Then the response status is 200
    And the element "accept-all-btn" should be visible
    And the element "reject-all-btn" should be visible
    And the element "accept-high-confidence-btn" should be visible

  Scenario: CHANGESET-VIEW_CHANGESET-1-07 Do Other inline input and submit are present per operation
    When I GET "/mockups/changeset/1/"
    Then the response status is 200
    And the element "do-other-input-3" should be visible
    And the element "do-other-submit-3" should be visible

  Scenario: CHANGESET-VIEW_CHANGESET-1-08 Marcus accepts op 1 and 2, uses Do Other on op 3
    When I GET "/mockups/changeset/1/"
    Then the response status is 200
    And the element "accept-op-1" should be visible
    And the element "accept-op-2" should be visible
    And the element "do-other-op-3" should be visible
    # Full flow (AT):
    # When the user clicks "accept-op-1"
    # And the user clicks "accept-op-2"
    # And the user clicks "do-other-op-3"
    # And the user enters "Code diagram is for repository structure, not runtime services"
    #   into "do-other-input-3"
    # And the user clicks "do-other-submit-3"
    # Then Munin re-processes op 3 with the instruction
    # And a replacement ChangeSet is created with the corrected operation

  Scenario: CHANGESET-VIEW_CHANGESET-1-09 Applied ChangeSet shows Rollback button
    When I GET "/mockups/changeset/2/"
    Then the response status is 200
    And the element "rollback-btn" should be visible
    And the user should see "applied"

  Scenario: CHANGESET-VIEW_CHANGESET-1-10 Auto-approval ChangeSet shows operations as already applied
    When I GET "/mockups/changeset/2/"
    Then the response status is 200
    And the user should see "auto"
    And the user should see "accepted"

  Scenario: CHANGESET-VIEW_CHANGESET-1-11 Rollback creates a new ChangeSet with source=rollback
    Given ChangeSet id=2 is applied with 2 accepted operations
    When Marcus clicks [Roll Back Entire Run]
    Then a new ChangeSet is created with source "rollback"
    And the rollback ChangeSet reverses all 2 operations from ChangeSet id=2

  # ── Navbar integration ────────────────────────────────────────────────────
  Scenario: CHANGESET-VIEW_CHANGESET-1-12 Changesets nav link is visible on view page
    When I GET "/mockups/changeset/1/"
    Then the response status is 200
    And the element "nav-changesets" should be visible
