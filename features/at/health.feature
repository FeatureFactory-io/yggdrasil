Feature: Health check
  As an operator
  I want the /health/ endpoint to respond with {"status": "ok"}
  So that the load balancer can confirm the application is alive

  Scenario: Liveness probe returns ok
    Given the application is running
    When I GET "/health/"
    Then the response status is 200
    And the response body contains "status": "ok"
