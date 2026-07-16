@wip
Feature: EXPORT-BRIEFING-1 Export Briefing
  As a Software Architect (Priya)
  I want to export the current view as Mermaid diagrams, a slide deck, or JSON
  So that I can share architecture context with non-technical stakeholders

  # Screen: EXPORT-BRIEFING-1
  # Mockup: /mockups/view/export/
  # Testids: export-briefing-page, munin-annotate-mermaid, export-mermaid-btn,
  #          munin-annotate-deck, export-deck-btn, export-json-btn
  # Fixture: seed.json (priya@example.com / test-pass-only-1234)
  # Entry point: VIEW-BROWSE-1 → [Export →] button

  Background:
    Given the user is logged in as "architect"

  Scenario: EXPORT-BRIEFING-1-01 Export page renders with all export format options
    When I GET "/mockups/view/export/"
    Then the response status is 200
    And the element "export-briefing-page" should be visible
    And the element "export-mermaid-btn" should be visible
    And the element "export-deck-btn" should be visible
    And the element "export-json-btn" should be visible

  Scenario: EXPORT-BRIEFING-1-02 Mermaid export has a Munin-annotate toggle
    When I GET "/mockups/view/export/"
    Then the response status is 200
    And the element "munin-annotate-mermaid" should be visible

  Scenario: EXPORT-BRIEFING-1-03 Slide deck export has a Munin-annotate toggle
    When I GET "/mockups/view/export/"
    Then the response status is 200
    And the element "munin-annotate-deck" should be visible

  Scenario: EXPORT-BRIEFING-1-04 Export page is reachable from View Browser export button
    When I GET "/mockups/view/browse/"
    Then the element "export-btn" should be visible
    # Clicking export-btn navigates to EXPORT-BRIEFING-1

  # ── Navbar integration ────────────────────────────────────────────────────
  Scenario: EXPORT-BRIEFING-1-05 Navbar is visible on export page
    When I GET "/mockups/view/export/"
    Then the response status is 200
    And the element "nav-view-browser" should be visible
