# @pending-mockup — No mockup template exists for Act 10 screens yet.
# Testids are TBD; behavior spec from user_journey.md and IA_guidelines.md.

Feature: DIAGRAM-LIST+FIND-1 Diagrams per Package
  As an Enterprise Architect (Elena)
  I want to see all Cytoscape diagrams grouped by package
  So that I can open the layout editor and manage how elements are visualised

  # Screen: DIAGRAM-LIST+FIND-1
  # Part II — Post-MVP (Elena's governance workflow)
  # No mockup yet. Behavior spec from user_journey.md Act 10, line 582.
  # Diagram types: Context, Container, Component, Code (C4 levels).

  Background:
    Given the user is logged in as "architect"

  Scenario: DIAGRAM-LIST+FIND-1-01 Diagram list renders with diagrams grouped by package
    When Elena browses to the Diagram list screen
    Then she sees diagrams grouped by package
    And the Technology package has a "Container Diagram" entry

  Scenario: DIAGRAM-LIST+FIND-1-02 Each diagram shows its type (Context/Container/Component/Code)
    When Elena views the Diagram list
    Then each entry shows a type from:
      | type      |
      | Context   |
      | Container |
      | Component |
      | Code      |

  Scenario: DIAGRAM-LIST+FIND-1-03 Open in Graph Editor launches Cytoscape layout editor
    When Elena clicks [Open in Graph Editor] for the Container Diagram
    Then the Cytoscape layout editor opens for that diagram
    And Elena can rearrange element positions

  Scenario: DIAGRAM-LIST+FIND-1-04 C4 diagrams are created automatically on bootstrap
    Given a new model is created with metamodel=c4
    When Elena browses to the Diagram list
    Then at least one diagram of each C4 type is present

  Scenario: DIAGRAM-LIST+FIND-1-05 Diagram list is filterable by package
    Given the model has diagrams in Technology, Application, and Context packages
    When Elena selects "Technology" from the package filter
    Then only diagrams in the Technology package are shown

  Scenario: DIAGRAM-LIST+FIND-1-06 Diagram membership is managed via create-element diagram hints
    # When creating an element, diagram_hints specify which C4 diagrams it appears in.
    # ELEMENT-CREATE_ELEMENT-1 diagram-C1 checkbox maps to the Container Diagram.
    Given Priya creates "Notification Service" with diagram hint "Container Diagram C1"
    Then "Notification Service" appears in the Container Diagram C1 element list
    And the Container Diagram membership count increases by 1
