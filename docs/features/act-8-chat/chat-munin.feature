@wip
Feature: CHAT-MUNIN-1 Chat with Munin (Embedded Panel in View Browser)
  As a Development Team Lead (Marcus)
  I want to ask Munin questions and give it instructions in natural language
  So that I can query and update the graph without leaving the View Browser

  # Screen: CHAT-MUNIN-1 (collapsible side panel embedded in VIEW-BROWSE-1)
  # Also reachable headlessly via ask_munin MCP tool (Act 5).
  # Mockup: /mockups/view/browse/ (Munin panel is in base.html)
  # Testids: open-munin-btn, munin-input, munin-send (all in base.html)
  # Fixture: seed.json (priya@example.com / test-pass-only-1234)
  # Reference: docs/features/user_journey.md Act 8, lines 517–539.
  # Note: Munin response assertions require TFK-07 (munin step definitions) in BPE.

  Background:
    Given the user is logged in as "architect"

  Scenario: CHAT-MUNIN-1-01 Munin panel toggle button is visible in View Browser
    When I GET "/mockups/view/browse/"
    Then the response status is 200
    And the element "open-munin-btn" should be visible

  Scenario: CHAT-MUNIN-1-02 Munin chat input and send button are present
    When I GET "/mockups/view/browse/"
    Then the response status is 200
    And the element "munin-input" should be visible
    And the element "munin-send" should be visible

  Scenario: CHAT-MUNIN-1-03 Example 1 — Find and navigate: ask who owns Payment API
    # Munin queries the graph for owner, health, and linked elements.
    # Response contains owner and navigates view to /elements/payment-api.
    Given Marcus is on the View Browser
    When Marcus types "Who owns Payment API?" in the Munin panel
    And Marcus clicks [Send]
    Then Munin responds with the owner of "Payment API"
    And the response cites "payments-team"
    And the view is navigated to show Payment API details

  Scenario: CHAT-MUNIN-1-04 Example 2 — Scope a view: show cross-team dependencies of Payment API
    # Munin constructs a traverse query and navigates the surrounding View Browser.
    Given Marcus is on the View Browser
    When Marcus types "Show me everything that depends on Payment API and is owned by another team"
    And Marcus clicks [Send]
    Then Munin constructs a traverse query for incoming dependencies of Payment API
    And the view filters to elements owned by teams other than "payments-team"
    And the response contains a semantic URL reference

  Scenario: CHAT-MUNIN-1-05 Example 3 — Propose an element via clickable prefill link
    # Munin returns a clickable /elements/new?prefill=... link; human reviews and submits.
    Given Marcus is on the View Browser
    When Marcus types "Add Notification Service as a Container under Technology"
    And Marcus clicks [Send]
    Then Munin responds with a prefill link for creating the element
    And the link contains name "Notification Service" and stereotype "Container" and package "Technology"
    And Marcus can click the link to open the pre-filled create form

  Scenario: CHAT-MUNIN-1-06 Example 4 — Tell a story: timeline of Payment API changes
    # Munin reads bitemporal history — every ChangeSet, Ratatosk run, Munin decision.
    Given Marcus is on the View Browser
    When Marcus types "Tell me a story about changes in the model of Payment API"
    And Marcus clicks [Send]
    Then Munin returns a narrative timeline of changes to Payment API
    And the response includes ChangeSet references
    And the response includes diff links

  Scenario: CHAT-MUNIN-1-07 Example 5 — Batch update: link Components in Payment package to API Gateway
    # Munin runs agentic loop: search Components, plan relationships, call update_relationships_batch.
    Given Marcus is on the View Browser
    When Marcus types "Link all Components in the Payment package to the new API Gateway"
    And Marcus clicks [Send]
    Then Munin runs its agentic loop
    And Munin searches for all Components in the Payment package
    And Munin calls update_relationships_batch with the planned relationship additions
    And in manual-review mode a ChangeSet is created for Marcus to review

  Scenario: CHAT-MUNIN-1-08 Example 6 — Generate a Markdown briefing with Mermaid diagrams
    # Munin scopes subgraph, generates Mermaid, writes narrative sections.
    Given Marcus is on the View Browser
    When Marcus types "Generate a Markdown briefing for the Payment System — one section per C4 level, Mermaid diagrams included, written for a non-technical audience"
    And Marcus clicks [Send]
    Then Munin returns a Markdown document in the chat
    And the document contains Mermaid diagram blocks
    And the document contains one section per C4 level

  Scenario: CHAT-MUNIN-1-09 Munin answers from ground truth only, never hallucinates
    # Munin only cites elements and relationships present in the live graph.
    Given the model contains exactly 6 elements
    When Marcus asks "How many elements does the model have?"
    Then Munin responds with exactly "6"
    And the response does not reference elements not in the model

  Scenario: CHAT-MUNIN-1-10 Munin panel is accessible headlessly via ask_munin MCP tool
    # Same Munin, same ground truth — MCP client gets the same answer as the browser panel.
    Given Elena has a valid read-only token in Claude Desktop
    When Elena calls MCP tool "ask_munin" with:
      | param    | value                                          |
      | question | What domain objects have changed since Jan?    |
    Then Munin responds with a list of elements changed since 2026-01-01
    And the response includes cited element links

  # ── Navbar integration ────────────────────────────────────────────────────
  # CHAT-MUNIN-1 is embedded in VIEW-BROWSE-1 — no separate navbar entry.
  # Munin panel is opened by clicking open-munin-btn on the View Browser page.
