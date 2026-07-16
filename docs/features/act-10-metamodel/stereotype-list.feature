# @pending-mockup — No mockup template exists for Act 10 screens yet.
# Testids are TBD; specify behavior from user_journey.md and IA_guidelines.md.
# Mockup to be created in ESM-06 extension when Elena's governance workflow is designed.

@wip
Feature: STEREOTYPE-LIST+FIND-1 Stereotype Definitions List
  As an Enterprise Architect (Elena)
  I want to see all stereotype definitions with their property schemas and allowed edge rules
  So that I can govern the metamodel and understand what element types exist

  # Screen: STEREOTYPE-LIST+FIND-1
  # Part II — Post-MVP (Elena's governance workflow)
  # No mockup yet. Behavior spec from user_journey.md Act 10, line 574.
  # Reference: docs/features/user_journey.md Act 10.

  Background:
    Given the user is logged in as "architect"

  Scenario: STEREOTYPE-LIST+FIND-1-01 Stereotype list renders with all defined stereotypes
    # In MVP the stereotypes are: System, Container, Component, Person, External
    When Elena browses to the Stereotype list screen
    Then she sees a list of stereotype definitions
    And the list contains "System"
    And the list contains "Container"
    And the list contains "Component"
    And the list contains "Person"
    And the list contains "External"

  Scenario: STEREOTYPE-LIST+FIND-1-02 Each stereotype shows its property schema
    When Elena views the "Container" stereotype
    Then she sees the allowed properties for Container elements
    And the property schema includes at least "version" and "language" fields

  Scenario: STEREOTYPE-LIST+FIND-1-03 Each stereotype shows allowed edge rules
    When Elena views the "Container" stereotype
    Then she sees the allowed outbound edge stereotypes for Container
    And the edge rules include "calls" and "depends_on"

  Scenario: STEREOTYPE-LIST+FIND-1-04 Metamodel changes require Elena's governance role
    # Only users in the Elena (governance) role can add/edit stereotypes.
    Given Marcus is logged in as an architect (not governance)
    When Marcus browses to the Stereotype list screen
    Then he can view stereotypes but cannot create or edit them

  Scenario: STEREOTYPE-LIST+FIND-1-05 C4 stereotypes are seeded automatically on bootstrap
    Given a new Yggdrasil model is created with metamodel=c4
    When Elena browses to the Stereotype list
    Then the C4 default stereotypes are present without manual entry
