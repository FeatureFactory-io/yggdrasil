Feature: CHAT-ASSIST-1 AI chat grounded in live graph
  As a development team lead
  I want to ask questions about the architecture
  So that I get answers based on ground truth not guesses

  Background:
    Given I am logged in as "marcus@example.com"
    And element "Payment API" exists with owner "payments-team"

  Scenario: CHAT-ASSIST-01 Ask about element ownership
    When I navigate to the AI chat page
    Then I should see the page "CHAT-ASSIST-1"
    When I send message "Who owns Payment API?"
    Then I should see a response mentioning "payments-team"
    And the response should link to element "Payment API"
