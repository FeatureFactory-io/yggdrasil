@wip
Feature: VIEW-BROWSE-1 View Browser
  As a Software Architect (Priya)
  I want to filter and explore the architecture graph
  So that I can find elements by stereotype, package, health, and time

  # Screen: VIEW-BROWSE-1 (central hub after login)
  # Mockup: /mockups/view/browse/
  # Testids: view-browse-page, filters-toggle, filter-package, filter-stereotype,
  #          filter-health, filter-as-of, apply-filters-btn, clear-filters-btn,
  #          toggle-table, toggle-graph, element-row-{id}, view-element-{id},
  #          export-btn, history-btn, open-munin-btn, saved-views-dropdown
  # Fixture: seed.json (priya@example.com / test-pass-only-1234)
  # Mock data: 6 elements across Context/Technology/Application packages

  Background:
    Given the user is logged in as "architect"

  Scenario: VIEW-BROWSE-1-01 View Browser renders with filter panel and element table
    When I GET "/mockups/view/browse/"
    Then the response status is 200
    And the element "view-browse-page" should be visible
    And the element "filters-toggle" should be visible
    And the element "apply-filters-btn" should be visible
    And the element "toggle-table" should be visible
    And the element "toggle-graph" should be visible

  Scenario: VIEW-BROWSE-1-02 Default view shows all 6 mock elements in table
    When I GET "/mockups/view/browse/"
    Then the response status is 200
    And the user should see "Payment API"
    And the user should see "Notification Service"
    And the user should see "Order Domain"
    And the user should see "Fulfillment Worker"
    And the user should see "PostgreSQL"
    And the user should see "Mobile App"

  Scenario: VIEW-BROWSE-1-03 Each element row shows Name, Stereotype, Owner, Health, Package columns
    When I GET "/mockups/view/browse/"
    Then the response status is 200
    And the user should see "Container"
    And the user should see "payments-team"
    And the user should see "Technology"

  Scenario: VIEW-BROWSE-1-04 Filter panel shows package, stereotype, health, and time-travel controls
    When I GET "/mockups/view/browse/"
    Then the response status is 200
    And the element "filter-package" should be visible
    And the element "filter-stereotype" should be visible
    And the element "filter-health" should be visible
    And the element "filter-as-of" should be visible

  Scenario: VIEW-BROWSE-1-05 Filter panel can be collapsed and expanded
    When I GET "/mockups/view/browse/"
    Then the response status is 200
    And the element "filters-toggle" should be visible

  Scenario: VIEW-BROWSE-1-06 Clear filters button is available
    When I GET "/mockups/view/browse/"
    Then the response status is 200
    And the element "clear-filters-btn" should be visible

  Scenario: VIEW-BROWSE-1-07 Saved views dropdown is visible
    When I GET "/mockups/view/browse/"
    Then the response status is 200
    And the element "saved-views-dropdown" should be visible

  Scenario: VIEW-BROWSE-1-08 View Browser has clickable links to each element's detail view
    When I GET "/mockups/view/browse/"
    Then the response status is 200
    And the element "view-element-1" should be visible
    And the element "view-element-2" should be visible
    And the element "view-element-6" should be visible

  Scenario: VIEW-BROWSE-1-09 Export and History actions are available from View Browser
    When I GET "/mockups/view/browse/"
    Then the response status is 200
    And the element "export-btn" should be visible
    And the element "history-btn" should be visible

  Scenario: VIEW-BROWSE-1-10 Munin panel toggle is available
    When I GET "/mockups/view/browse/"
    Then the response status is 200
    And the element "open-munin-btn" should be visible

  Scenario: VIEW-BROWSE-1-11 Time travel shows "Viewing model as of" banner when date is selected
    # Selecting a past date in filter-as-of appends ?as_of=YYYY-MM-DD to URL
    # and renders "Viewing model as of 2026-01-15" banner with [Compare with now] link
    # TFK-07: add step "When the user sets the time travel date to '{date}'"
    Given the user is on the "view-browse" page with ?as_of=2026-01-15
    Then the user should see "Viewing model as of"
    # And the user should see "Compare with now"

  # ── Viewer permissions ────────────────────────────────────────────────────
  Scenario: VIEW-BROWSE-1-12 Viewer can browse elements but has no create button
    Given the user is logged in as "viewer"
    When I GET "/mockups/view/browse/"
    Then the response status is 200
    And the element "view-browse-page" should be visible
    And the user should not see "Create Element"

  # ── Navbar integration ────────────────────────────────────────────────────
  Scenario: VIEW-BROWSE-1-13 Navbar shows all primary navigation links
    When I GET "/mockups/view/browse/"
    Then the response status is 200
    And the element "nav-view-browser" should be visible
    And the element "nav-elements" should be visible
    And the element "nav-relationships" should be visible
    And the element "nav-changesets" should be visible
    And the element "nav-runs" should be visible
