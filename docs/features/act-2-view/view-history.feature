Feature: VIEW-HISTORY-1 Model History and Snapshot Comparison
  As a Software Architect (Priya)
  I want to compare two historical snapshots of the model
  So that I can see what changed between any two points in time

  # Screen: VIEW-HISTORY-1
  # Mockup: /mockups/view/history/
  # Testids: view-history-page, snapshot-a, snapshot-b, compare-btn,
  #          timeline-item-{id}, open-snapshot-a, open-snapshot-b
  # Fixture: seed.json (priya@example.com / test-pass-only-1234)
  # Mock data: 3 ChangeSets forming the timeline (ids 1, 2, 3)
  # Entry point: VIEW-BROWSE-1 → [History →] button

  Background:
    Given the user is logged in as "architect"

  Scenario: VIEW-HISTORY-1-01 History page renders with snapshot pickers and compare button
    When I GET "/mockups/view/history/"
    Then the response status is 200
    And the element "view-history-page" should be visible
    And the element "snapshot-a" should be visible
    And the element "snapshot-b" should be visible
    And the element "compare-btn" should be visible

  Scenario: VIEW-HISTORY-1-02 History page shows timeline of ChangeSets
    When I GET "/mockups/view/history/"
    Then the response status is 200
    And the element "timeline-item-1" should be visible
    And the element "timeline-item-2" should be visible
    And the element "timeline-item-3" should be visible

  Scenario: VIEW-HISTORY-1-03 Timeline shows ChangeSet sources (ratatosk, human)
    When I GET "/mockups/view/history/"
    Then the response status is 200
    And the user should see "ratatosk"
    And the user should see "human"

  Scenario: VIEW-HISTORY-1-04 Each timeline item has links to open snapshot in View Browser
    When I GET "/mockups/view/history/"
    Then the response status is 200
    And the element "open-snapshot-a" should be visible
    And the element "open-snapshot-b" should be visible

  Scenario: VIEW-HISTORY-1-05 History page is reachable from View Browser history button
    When I GET "/mockups/view/browse/"
    Then the element "history-btn" should be visible
    # Clicking history-btn navigates to VIEW-HISTORY-1

  # ── Navbar integration ────────────────────────────────────────────────────
  Scenario: VIEW-HISTORY-1-06 Navbar is visible on history page
    When I GET "/mockups/view/history/"
    Then the response status is 200
    And the element "nav-view-browser" should be visible
