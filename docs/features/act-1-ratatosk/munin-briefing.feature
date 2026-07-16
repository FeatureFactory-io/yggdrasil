@wip
Feature: MUNIN-BRIEFING-1 Post-Run Briefing
  As a Software Architect (Priya)
  I want to see Munin's summary after a Ratatosk run
  So that I understand what was discovered and what needs my review

  # Screen: MUNIN-BRIEFING-1
  # Mockup: /mockups/munin/briefing/
  # Testids: munin-briefing-page, review-changeset-btn, explore-graph-btn,
  #          next-review-changeset, next-explore-graph, next-run-again, c4-primer-got-it
  # Fixture: seed.json (priya@example.com / test-pass-only-1234)

  Background:
    Given the user is logged in as "architect"

  Scenario: MUNIN-BRIEFING-1-01 Briefing page renders after Ratatosk run
    When I GET "/mockups/munin/briefing/"
    Then the response status is 200
    And the element "munin-briefing-page" should be visible

  Scenario: MUNIN-BRIEFING-1-02 Briefing shows Munin's auto-generated narrative summary
    When I GET "/mockups/munin/briefing/"
    Then the response status is 200
    And the user should see "I analysed"
    And the user should see "elements"
    And the user should see "relationships"

  Scenario: MUNIN-BRIEFING-1-03 Confidence distribution shows auto-applied, queued, and skipped counts
    When I GET "/mockups/munin/briefing/"
    Then the response status is 200
    And the user should see "auto-applied"
    And the user should see "queued for review"
    And the user should see "below threshold"

  Scenario: MUNIN-BRIEFING-1-04 Briefing shows key findings with links to elements or ChangeSets
    When I GET "/mockups/munin/briefing/"
    Then the response status is 200
    And the user should see "Payment API"

  Scenario: MUNIN-BRIEFING-1-05 Suggested next steps: Review ChangeSet, Explore graph, Run again
    When I GET "/mockups/munin/briefing/"
    Then the response status is 200
    And the element "next-review-changeset" should be visible
    And the element "next-explore-graph" should be visible
    And the element "next-run-again" should be visible

  Scenario: MUNIN-BRIEFING-1-06 Direct action buttons reach ChangeSet review and View Browser
    When I GET "/mockups/munin/briefing/"
    Then the response status is 200
    And the element "review-changeset-btn" should be visible
    And the element "explore-graph-btn" should be visible

  Scenario: MUNIN-BRIEFING-1-07 C4 primer overlay is visible on first bootstrap run
    When I GET "/mockups/munin/briefing/"
    Then the response status is 200
    And the user should see "C4 in 60 seconds"
    And the element "c4-primer-got-it" should be visible

  Scenario: MUNIN-BRIEFING-1-08 C4 primer explains Context, Container, Component, Code levels
    When I GET "/mockups/munin/briefing/"
    Then the response status is 200
    And the user should see "Context"
    And the user should see "Container"
    And the user should see "Component"
    And the user should see "Code"

  Scenario: MUNIN-BRIEFING-1-09 Raw run log is present and links to RATATOSK_RUN-VIEW_RATATOSK_RUN-1
    When I GET "/mockups/munin/briefing/"
    Then the response status is 200
    And the user should see "run"

  # ── Navbar integration ─────────────────────────────────────────────────────
  Scenario: MUNIN-BRIEFING-1-10 Navbar is visible with View Browser link
    When I GET "/mockups/munin/briefing/"
    Then the response status is 200
    And the element "nav-view-browser" should be visible
    And the element "nav-elements" should be visible
