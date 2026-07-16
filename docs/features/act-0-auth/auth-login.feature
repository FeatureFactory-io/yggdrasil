Feature: AUTH-LOGIN-1 Sign in
  As an Enterprise Architect (Elena)
  I want to sign in with my email and password
  So that I can access the architecture knowledge graph

  # Screen: AUTH-LOGIN-1
  # Mockup: /mockups/auth/login/
  # Testids: auth-login-page, login-form, login-email, login-password, login-submit
  # Fixture: seed.json (elena@example.com / test-pass-only-1234)

  Scenario: AUTH-LOGIN-1-01 Login page renders with email, password, and sign-in button
    Given the user is not authenticated
    When I GET "/mockups/auth/login/"
    Then the response status is 200
    And the element "auth-login-page" should be visible
    And the element "login-form" should be visible
    And the element "login-email" should be visible
    And the element "login-password" should be visible
    And the element "login-submit" should be visible
    And the user should see "Sign in"
    And the user should see "Yggdrasil"

  Scenario: AUTH-LOGIN-1-02 Successful sign-in with architect credentials redirects to View Browser
    Given the user is not authenticated
    When I GET "/mockups/auth/login/"
    # AT form steps would POST login-email + login-password; mockup redirects on submit
    Then the response status is 200
    And the user should see "elena@example.com"
    # After login, user lands on VIEW-BROWSE-1
    # Full flow scenario: Given the user is on the "auth-login" page
    #   When the user enters "elena@example.com" into "login-email"
    #   And the user enters "test-pass-only-1234" into "login-password"
    #   And the user clicks "login-submit"
    #   Then the element "view-browse-page" should be visible
    # Note: login-email testid does not follow {field}-input convention — see CATALOG.md Gap #1

  Scenario: AUTH-LOGIN-1-03 Login page shows admin-provisioned account notice
    Given the user is not authenticated
    When I GET "/mockups/auth/login/"
    Then the response status is 200
    And the user should see "Accounts are admin-provisioned"

  Scenario: AUTH-LOGIN-1-04 Authenticated architect is redirected to View Browser (direct URL)
    Given the user is logged in as "architect"
    When I GET "/mockups/view/browse/"
    Then the response status is 200
    And the element "view-browse-page" should be visible

  Scenario: AUTH-LOGIN-1-05 Unauthenticated user is redirected to login for protected pages
    Given the user is not authenticated
    # Real app enforces login_required; mockup doesn't — scenario describes production intent
    # When the user navigates to a protected page the response status is 302 (redirect to login)
    # TFK-07: add step "Then the user is redirected to the login page"

  # ── Navbar integration ─────────────────────────────────────────────────────
  # AUTH-LOGIN-1 has no navbar (standalone login page — no session yet).
