@wip
Feature: ACT-1-DISC Ratatosk real discovery
  As a Software Architect (Priya)
  I want Ratatosk to discover architecture from a real repository under Metamodel guidance
  So that candidates come from the codebase and always enter the model via ChangeSet

  # Discovery mechanics for bootstrap (filesystem mode).
  # MVP-W1: sample_webapp + expected_elements.yaml manifest.
  # Fixture repo: tests/fixtures/repos/sample_webapp/

  # ── MVP-W1: happy / core ───────────────────────────────────────────────────

  Scenario: ACT-1-DISC-01 Fixture repo discovers all manifest elements under Metamodel c4
    Given the Metamodel "c4" exists with C4 stereotypes and packages
    And Priya has a Yggdrasil personal access token with read-write scope
    And the Yggdrasil model "Yggdrasil" exists with no elements
    And the fixture repository "sample_webapp" is available
    When Priya runs ratatosk bootstrap against the fixture repository "sample_webapp"
    Then the exit code is 0
    And bootstrap candidates include all manifest elements:
      | name           | stereotype | package     |
      | Payment API    | container  | technology  |
      | Order Service  | container  | technology  |
      | Order Domain   | component  | application |
      | Billing Worker | component  | application |
    And a ChangeSet with source "ratatosk" exists

  Scenario: ACT-1-DISC-02 Blackboard records tree paths before extract
    Given the Metamodel "c4" exists with C4 stereotypes and packages
    And Priya has a Yggdrasil personal access token with read-write scope
    And the fixture repository "sample_webapp" is available
    When Priya runs ratatosk bootstrap against the fixture repository "sample_webapp"
    Then the run blackboard contains step "tree"
    And the run blackboard tree includes "docker-compose.yml"
    And the run blackboard tree includes "src/order_service/app.py"
    And the run blackboard tree includes "src/billing_worker/worker.py"
    And the run blackboard contains step "extract"

  Scenario: ACT-1-DISC-06 Bootstrap never writes Elements outside a ChangeSet
    Given the Metamodel "c4" exists with C4 stereotypes and packages
    And Priya has a Yggdrasil personal access token with read-write scope
    And the Yggdrasil model "Yggdrasil" exists with no elements
    And the fixture repository "sample_webapp" is available
    When Priya runs ratatosk bootstrap against the fixture repository "sample_webapp"
    Then a ChangeSet with source "ratatosk" exists
    And every new Element is referenced by an operation on that ChangeSet
    And there are no orphan Elements without a ChangeSetItem

  @wip
  Scenario: ACT-1-DISC-21 Subprocess bootstrap calls MCP handoff tools
    Given the Metamodel "c4" exists with C4 stereotypes and packages
    And Priya has a Yggdrasil personal access token with read-write scope
    And the Yggdrasil model "Yggdrasil" exists with no elements
    And the fixture repository "sample_webapp" is available
    And the environment variable "YGGDRASIL_SERVER_URL" is set to "http://localhost:8000"
    When Priya runs ratatosk bootstrap against fixture "sample_webapp" via subprocess
    Then MCP tool "ensure_model" was called during bootstrap
    And MCP tool "list_stereotypes" was called during bootstrap
    And MCP tool "propose_changeset" was called during bootstrap
    And MCP tool "record_ratatosk_run" was called during bootstrap

  Scenario: ACT-1-DISC-15 Run blackboard records ModelSummary token budget
    Given the Metamodel "c4" exists with C4 stereotypes and packages
    And Priya has a Yggdrasil personal access token with read-write scope
    And the fixture repository "sample_webapp" is available
    When Priya runs ratatosk bootstrap against the fixture repository "sample_webapp"
    Then the run blackboard contains key "model_summary_chars"
    And the run blackboard model_summary_chars is at most 8000 tokens equivalent

  Scenario: ACT-1-DISC-16 Metamodel guidance step is recorded on blackboard
    Given the Metamodel "c4" exists with C4 stereotypes and packages
    And Priya has a Yggdrasil personal access token with read-write scope
    And the fixture repository "sample_webapp" is available
    When Priya runs ratatosk bootstrap against the fixture repository "sample_webapp"
    Then the run blackboard contains step "metamodel_guidance"
    And the run blackboard metamodel_guidance mentions stereotype "Container"

  # ── ACT-1-LLM — Ollama bootstrap (@ollama optional CI) ─────────────────────

  @wip @ollama
  Scenario: ACT-1-LLM-01 Bootstrap uses Ollama when LLM_PROVIDER is ollama
    Given Ollama is reachable at "http://localhost:11434"
    And the environment variable "LLM_PROVIDER" is set to "ollama"
    And Priya has a Yggdrasil personal access token with read-write scope
    And the Yggdrasil model "Yggdrasil" exists with no elements
    And the fixture repository "sample_webapp" is available
    When Priya runs ratatosk bootstrap against fixture "sample_webapp" via subprocess
    Then the discovery LLM was invoked at least once
    And the output does not contain "scripted-discovery"

  @wip @ollama
  Scenario: ACT-1-LLM-02 Bootstrap fails clearly when Ollama model is not pulled
    Given Ollama is reachable at "http://localhost:11434"
    And Ollama model "qwen3:14b" is not available
    And the environment variable "LLM_PROVIDER" is set to "ollama"
    And Priya has a Yggdrasil personal access token with read-write scope
    And the fixture repository "sample_webapp" is available
    When Priya runs ratatosk bootstrap against fixture "sample_webapp" via subprocess
    Then the exit code is not 0
    And the output contains "model"

  @wip @ollama
  Scenario: ACT-1-LLM-03 Ollama bootstrap discovers all manifest elements
    Given Ollama is reachable at "http://localhost:11434"
    And the environment variable "LLM_PROVIDER" is set to "ollama"
    And Priya has a Yggdrasil personal access token with read-write scope
    And the Yggdrasil model "Yggdrasil" exists with no elements
    And the fixture repository "sample_webapp" is available
    When Priya runs ratatosk bootstrap against fixture "sample_webapp" via subprocess
    Then bootstrap candidates include all manifest elements:
      | name           | stereotype | package     |
      | Payment API    | container  | technology  |
      | Order Service  | container  | technology  |
      | Order Domain   | component  | application |
      | Billing Worker | component  | application |

  @wip @ollama
  Scenario: ACT-1-LLM-04 Markdown-wrapped JSON extract is parsed and constrained
    Given the Metamodel "c4" exists with C4 stereotypes and packages
    And Priya has a Yggdrasil personal access token with read-write scope
    And the fixture repository "sample_webapp" is available
    And the discovery LLM will return a candidate with stereotype "microservice"
    When Priya runs ratatosk bootstrap against the fixture repository "sample_webapp"
    Then no ChangeSet operation references stereotype "microservice"
    And the model does not contain an element with stereotype "microservice"

  # ── ACT-1-LLM — Anthropic bootstrap (@anthropic optional manual cert) ─────

  @wip @anthropic
  Scenario: ACT-1-LLM-05 Bootstrap uses Anthropic when LLM_PROVIDER is anthropic
    Given the environment variable "LLM_PROVIDER" is set to "anthropic"
    And the environment variable "ANTHROPIC_API_KEY" is set
    And Priya has a Yggdrasil personal access token with read-write scope
    And the Yggdrasil model "Yggdrasil" exists with no elements
    And the fixture repository "sample_webapp" is available
    When Priya runs ratatosk bootstrap against fixture "sample_webapp" via subprocess
    Then the discovery LLM was invoked at least once
    And the output does not contain "scripted-discovery"
    And the output does not contain "Ollama request failed"

  @wip @anthropic
  Scenario: ACT-1-LLM-06 Bootstrap fails clearly when Anthropic API key is missing
    Given the environment variable "LLM_PROVIDER" is set to "anthropic"
    And the environment variable "ANTHROPIC_API_KEY" is not set
    And the fixture repository "sample_webapp" is available
    When Priya runs ratatosk bootstrap against fixture "sample_webapp" via subprocess
    Then the exit code is not 0
    And the output contains "ANTHROPIC_API_KEY"

  # ── MVP-W2 / edge cases ────────────────────────────────────────────────────

  @wip
  Scenario: ACT-1-DISC-03 Re-bootstrap bulk-wipes existing graph before rescan
    Given the Metamodel "c4" exists with C4 stereotypes and packages
    And Priya has a Yggdrasil personal access token with read-write scope
    And the Yggdrasil model "Yggdrasil" exists with element "Payment API" stereotype "Container"
    And the fixture repository "sample_webapp" is available
    When Priya runs ratatosk bootstrap against the fixture repository "sample_webapp"
    Then the exit code is 0
    And the output contains "wiping"
    And the output contains "to_add:"
    And the output does not contain "unchanged:"
    And a ChangeSet with source "ratatosk" exists

  Scenario: ACT-1-DISC-04 Cleanup drops unknown stereotype before Munin
    Given the Metamodel "c4" exists with C4 stereotypes and packages
    And Priya has a Yggdrasil personal access token with read-write scope
    And the fixture repository "sample_webapp" is available
    And the discovery LLM will return a candidate with stereotype "microservice"
    When Priya runs ratatosk bootstrap against the fixture repository "sample_webapp"
    Then no ChangeSet operation references stereotype "microservice"
    And the model does not contain an element with stereotype "microservice"

  Scenario: ACT-1-DISC-05 Discovery uses LLM turns not hardcoded Payment API fallback
    Given the Metamodel "c4" exists with C4 stereotypes and packages
    And Priya has a Yggdrasil personal access token with read-write scope
    And the fixture repository "sample_webapp" is available
    When Priya runs ratatosk bootstrap against the fixture repository "sample_webapp" with a scripted discovery LLM
    Then the discovery LLM was invoked at least once
    And the run blackboard contains step "project_map"

  # ── Expected errors ────────────────────────────────────────────────────────

  Scenario: ACT-1-DISC-07 Missing token fails with clear error
    Given the fixture repository "sample_webapp" is available
    When Priya runs:
      """
      ratatosk bootstrap ./repo --model Yggdrasil --metamodel=c4
      """
    Then the exit code is not 0
    And the output contains "token"

  Scenario: ACT-1-DISC-08 Read-only token fails before write handoff
    Given the Metamodel "c4" exists with C4 stereotypes and packages
    And Priya has a Yggdrasil personal access token with read-only scope
    And the fixture repository "sample_webapp" is available
    When Priya runs ratatosk bootstrap against the fixture repository "sample_webapp"
    Then the exit code is not 0
    And the output contains "permission"
    And no ChangeSet with source "ratatosk" was created for this run

  Scenario: ACT-1-DISC-09 Unknown metamodel slug fails
    Given Priya has a Yggdrasil personal access token with read-write scope
    And the fixture repository "sample_webapp" is available
    When Priya runs ratatosk bootstrap against the fixture repository "sample_webapp" with metamodel "no-such-mm"
    Then the exit code is not 0
    And the output contains "metamodel"
    And no Model was created with metamodel "no-such-mm"

  Scenario: ACT-1-DISC-10 Metamodel mismatch on existing Model fails
    Given the Metamodel "c4" exists with C4 stereotypes and packages
    And a Metamodel "other" exists
    And Priya has a Yggdrasil personal access token with read-write scope
    And the Yggdrasil model "Yggdrasil" exists bound to metamodel "c4"
    And the fixture repository "sample_webapp" is available
    When Priya runs ratatosk bootstrap against the fixture repository "sample_webapp" with metamodel "other"
    Then the exit code is not 0
    And the output contains "bound to metamodel"

  Scenario: ACT-1-DISC-11 Missing repo path fails with clear error
    Given Priya has a Yggdrasil personal access token with read-write scope
    When Priya runs:
      """
      ratatosk bootstrap /tmp/yggdrasil-no-such-repo-xyz --token=$YGGDRASIL_TOKEN --model Yggdrasil --metamodel=c4
      """
    Then the exit code is not 0
    And the output contains "path"
    And no ChangeSet with source "ratatosk" was created for this run

  Scenario: ACT-1-DISC-12 Empty repo after ignores yields nothing to scan
    Given the Metamodel "c4" exists with C4 stereotypes and packages
    And Priya has a Yggdrasil personal access token with read-write scope
    And the fixture repository "empty_repo" is available
    When Priya runs ratatosk bootstrap against the fixture repository "empty_repo"
    Then the exit code is 0
    And the output contains "nothing to scan"
    And there are no orphan Elements without a ChangeSetItem

  Scenario: ACT-1-DISC-13 MCP snapshot failure does not fall back to silent ORM invent
    Given the Metamodel "c4" exists with C4 stereotypes and packages
    And Priya has a Yggdrasil personal access token with read-write scope
    And the fixture repository "sample_webapp" is available
    And the MCP snapshot endpoint is unreachable
    When Priya runs ratatosk bootstrap against the fixture repository "sample_webapp"
    Then the exit code is not 0
    And the output contains "MCP"
    And there are no orphan Elements without a ChangeSetItem

  Scenario: ACT-1-DISC-14 Non-JSON LLM plan does not invent hardcoded Elements
    Given the Metamodel "c4" exists with C4 stereotypes and packages
    And Priya has a Yggdrasil personal access token with read-write scope
    And the fixture repository "sample_webapp" is available
    And the discovery LLM returns non-JSON prose only
    When Priya runs ratatosk bootstrap against the fixture repository "sample_webapp"
    Then the exit code is 0
    And the output contains "no architecture changes detected" or "empty plan"
    And there are no orphan Elements without a ChangeSetItem
