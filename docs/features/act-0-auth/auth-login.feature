Feature: AUTH-LOGIN-1 Sign in
  As an Enterprise Architect (Elena)
  I want to sign in with my email and password
  So that I can access the architecture knowledge graph

  # Screen: AUTH-LOGIN-1
  # Real URL: /auth/login/
  # Testids: auth-login-page, login-form, login-email, login-password, login-submit
  # Post-login default: / (web:index → auth:token_list when authenticated)

  Scenario: AUTH-LOGIN-1-01 Login page renders with email, password, and sign-in button
    Given the user is not authenticated
    When I GET "/auth/login/"
    Then the response status is 200
    And the element "auth-login-page" should be visible
    And the element "login-form" should be visible
    And the element "login-email" should be visible
    And the element "login-password" should be visible
    And the element "login-submit" should be visible
    And the user should see "Sign in"
    And the user should see "Yggdrasil"

  Scenario: AUTH-LOGIN-1-02 Successful sign-in redirects away from login
    Given a user exists with email "elena@example.com" and password "test-pass-only-1234"
    And the user is not authenticated
    When I POST "/auth/login/" with email "elena@example.com" and password "test-pass-only-1234"
    Then the response status is 302
    And the response redirects away from "/auth/login/"

  Scenario: AUTH-LOGIN-1-03 Failed sign-in re-renders login with error
    Given a user exists with email "elena@example.com" and password "test-pass-only-1234"
    And the user is not authenticated
    When I POST "/auth/login/" with email "elena@example.com" and password "wrong-password"
    Then the response status is 200
    And the element "auth-login-page" should be visible
    And the user should see "Invalid email or password"

  Scenario: AUTH-LOGIN-1-04 Login page shows admin-provisioned account notice
    Given the user is not authenticated
    When I GET "/auth/login/"
    Then the response status is 200
    And the user should see "Accounts are admin-provisioned"

  Scenario: AUTH-LOGIN-1-05 Authenticated user is redirected away from login
    Given the user is logged in as "architect"
    When I GET "/auth/login/"
    Then the response status is 302

  Scenario: AUTH-LOGIN-1-06 Unauthenticated user is redirected to login for protected pages
    Given the user is not authenticated
    When I GET "/auth/tokens/"
    Then the response status is 302
    And the response Location contains "/auth/login/"
