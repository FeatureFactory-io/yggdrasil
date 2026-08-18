Feature: VIEW-BROWSE-1 View Browser — Named Views (Filters + Levels + Content)
  As a Software Architect (Priya)
  I want to save and reload browse snapshots
  So that I can return to a scoped subgraph without re-entering filters and depth

  # Component: Views dropdown + save dialog · CR: VIEW-BROWSE-1_VIEWS_V1 (+ v2 Content/viewport in W15)
  # Production: /models/{slug}/views/ · persistence: graph.BrowseView (ORM, per user+model)
  # Testids: views-dropdown, save-view-btn, save-view-confirm-btn, save-view-name-input,
  #          view-option-{slug}, delete-view-btn, save-view-include-viewport (W15)
  # Live URL: package, stereotype, edge_stereotype, field_{st}, depth, mode=graph|table
  # Named View: ?browse_view={slug} — expands filters, depth, mode, content.field_map, optional viewport
  # Content scenarios: view-browse-content.feature (69–79) · mockup: Filters-first field_map
  # Fixture: view_browser_model (pytest) · view_browser_explorer_fixture (depth scenarios)

  Background:
    Given the user is logged in as "architect"
    And the model "yggdrasil" is loaded with the view browser fixture

  # ── AT: shell ─────────────────────────────────────────────────────────────

  Scenario: VIEW-BROWSE-1-61 Views dropdown and save affordances render
    When I GET "/models/yggdrasil/views/"
    Then the response status is 200
    And the element "views-dropdown" should be visible
    And the element "save-view-btn" should be visible
    And the element "filters-toggle" should be visible

  Scenario: VIEW-BROWSE-1-67 Clear filters does not remove named Views from catalog
    Given Priya has saved a View named "Tech stack" for model "yggdrasil"
    When I GET "/models/yggdrasil/views/?package=technology"
    And Priya clears all browse filters in the View Browser
    Then the element "view-option-tech-stack" should be visible

  # ── AT + E2E: persistence (W14) ───────────────────────────────────────────

  Scenario: VIEW-BROWSE-1-62 Save current View persists filters and depth
    Given Priya is on the View Browser in graph mode with depth 2
    And Priya has applied package filter "technology"
    When Priya saves the current browse session as View "Tech only"
    Then a BrowseView "tech-only" exists for model "yggdrasil" owned by Priya
    And the stored View payload includes package "technology" and depth 2
    # W15: same step also asserts content preset and optional viewport when checked

  Scenario: VIEW-BROWSE-1-63 Load named View restores URL params and depth badge
    Given Priya has saved a View named "App components" with stereotype "component" and depth 3
    When Priya selects View "App components" from the Views dropdown
    Then the browser URL includes stereotype=component
    And the browser URL includes depth=3
    And the element "browser-depth-value" should be visible
    # W15: restores content preset labels and viewport when saved with include-viewport

  Scenario: VIEW-BROWSE-1-64 browse_view slug expands to equivalent query string
    Given Priya has saved a View named "Payment review" with package "technology" and depth 2
    When I GET "/models/yggdrasil/views/?browse_view=payment-review"
    Then the response status is 200
    And the user should see "Payment API"

  Scenario: VIEW-BROWSE-1-65 View catalog is scoped to current Model
    Given Priya has saved a View named "Ygg view" for model "yggdrasil"
    And a View named "Payments view" exists for model "payments"
    When Priya is on the View Browser for model "yggdrasil"
    Then the element "view-option-ygg-view" should be visible
    And the element "view-option-payments-view" should not be visible

  Scenario: VIEW-BROWSE-1-66 Owner can delete a saved View
    Given Priya has saved a View named "Temporary" for model "yggdrasil"
    When Priya deletes View "Temporary"
    Then the element "view-option-temporary" should not be visible

  Scenario: VIEW-BROWSE-1-68 Viewer can load but not save or delete Views
    Given the user is logged in as "viewer"
    And an architect has saved a View named "Shared review" for model "yggdrasil"
    When the viewer loads View "Shared review" from the Views dropdown
    Then the response status is 200
    And the element "save-view-btn" should not be visible
    And the element "save-view-confirm-btn" should not be visible
