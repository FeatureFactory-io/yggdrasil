# @pending-mockup — No mockup template exists for Act 10 screens yet.
# Testids are TBD; behavior spec from user_journey.md and IA_guidelines.md.

@wip
Feature: PACKAGE-LIST+FIND-1 Package Hierarchy
  As an Enterprise Architect (Elena)
  I want to see and manage the package hierarchy
  So that I can organise elements into logical views (Business, Application, Technology, Code)

  # Screen: PACKAGE-LIST+FIND-1
  # Part II — Post-MVP (Elena's governance workflow)
  # No mockup yet. Behavior spec from user_journey.md Act 10, line 578.
  # C4 default packages: Context, Technology, Application, Code.

  Background:
    Given the user is logged in as "architect"

  Scenario: PACKAGE-LIST+FIND-1-01 Package list renders with all defined packages
    When Elena browses to the Package list screen
    Then she sees a list of packages in the model
    And the list contains "Context"
    And the list contains "Technology"
    And the list contains "Application"
    And the list contains "Code"

  Scenario: PACKAGE-LIST+FIND-1-02 Package shows its slug and element count
    When Elena views the "Technology" package
    Then she sees the package slug "technology"
    And she sees the count of elements assigned to Technology

  Scenario: PACKAGE-LIST+FIND-1-03 C4 packages are seeded automatically on bootstrap
    Given a new model is created with metamodel=c4
    When Elena browses to the Package list
    Then the 4 C4 default packages exist without manual entry

  Scenario: PACKAGE-LIST+FIND-1-04 Elements can be filtered by package in View Browser
    # Package filter in VIEW-BROWSE-1 uses the same package list as defined here.
    Given the model has packages Context, Technology, Application, Code
    When Priya selects "Technology" in the View Browser package filter
    Then only elements assigned to the Technology package are shown

  Scenario: PACKAGE-LIST+FIND-1-05 Governance role required to create new packages
    Given Marcus is logged in as architect (not governance)
    When Marcus browses to the Package list
    Then he can view packages but cannot create new packages
