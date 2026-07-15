Feature: RELATIONSHIP-VIEW_RELATIONSHIP-1 View Relationship Details
  As a Software Architect (Priya)
  I want to see the full details of an architecture relationship
  So that I can understand the edge stereotype, properties, and confidence

  # Screen: RELATIONSHIP-VIEW_RELATIONSHIP-1
  # Mockup: /mockups/relationship/{id}/
  # Testids: relationship-view-page, delete-relationship-btn, edit-relationship-btn,
  #          relationship-delete-modal, relationship-delete-form, confirm-delete-btn
  # Fixture: seed.json (priya@example.com / test-pass-only-1234)
  # Mock relationship: id=1, Mobile App →calls→ Payment API, confidence=0.95

  Background:
    Given the user is logged in as "architect"

  Scenario: RELATIONSHIP-VIEW_RELATIONSHIP-1-01 View page renders with from/edge/to details
    When I GET "/mockups/relationship/1/"
    Then the response status is 200
    And the element "relationship-view-page" should be visible
    And the user should see "Mobile App"
    And the user should see "calls"
    And the user should see "Payment API"

  Scenario: RELATIONSHIP-VIEW_RELATIONSHIP-1-02 View page shows relationship properties
    When I GET "/mockups/relationship/1/"
    Then the response status is 200
    And the user should see "HTTPS"

  Scenario: RELATIONSHIP-VIEW_RELATIONSHIP-1-03 View page shows confidence score
    When I GET "/mockups/relationship/1/"
    Then the response status is 200
    And the user should see "95"

  Scenario: RELATIONSHIP-VIEW_RELATIONSHIP-1-04 View page shows source (ratatosk or human)
    When I GET "/mockups/relationship/1/"
    Then the response status is 200
    And the user should see "ratatosk"

  Scenario: RELATIONSHIP-VIEW_RELATIONSHIP-1-05 Edit and delete buttons are visible for architect
    When I GET "/mockups/relationship/1/"
    Then the response status is 200
    And the element "edit-relationship-btn" should be visible
    And the element "delete-relationship-btn" should be visible

  Scenario: RELATIONSHIP-VIEW_RELATIONSHIP-1-06 Delete modal with confirmation is present
    When I GET "/mockups/relationship/1/"
    Then the response status is 200
    And the element "relationship-delete-modal" should be visible
    And the element "confirm-delete-btn" should be visible

  Scenario: RELATIONSHIP-VIEW_RELATIONSHIP-1-07 View a depends_on relationship (id=2)
    When I GET "/mockups/relationship/2/"
    Then the response status is 200
    And the user should see "Payment API"
    And the user should see "depends_on"
    And the user should see "PostgreSQL"

  # ── Navbar integration ────────────────────────────────────────────────────
  Scenario: RELATIONSHIP-VIEW_RELATIONSHIP-1-08 Navbar is visible on relationship view page
    When I GET "/mockups/relationship/1/"
    Then the response status is 200
    And the element "nav-relationships" should be visible
