@wip
Feature: ACT-1-CFG Ratatosk CLI configuration
  As a Software Architect (Priya)
  I want Ratatosk to merge config from flags, env, and YAML files
  So that scout bounds, tool allowlists, and secrets are consistent across laptop and CI

  # Merge order: CLI flags → env → repo ratatosk.yaml → ~/.ratatosk/config.yaml
  # MVP-W1: bootstrap env (Ollama + local server).

  # ── MVP-W1: bootstrap config ───────────────────────────────────────────────

  Scenario: ACT-1-CFG-02 CLI flag overrides repo config for model summary budget
    Given a repo config file "ratatosk.yaml" with model_summary_token_budget 8000
    When Priya runs ratatosk bootstrap with flag "--model-summary-budget 4000"
    Then the effective config key "model_summary_token_budget" is 4000

  Scenario: ACT-1-CFG-06 LLM_PROVIDER ollama selects Ollama not scripted fallback
    Given the environment variable "LLM_PROVIDER" is set to "ollama"
    When Ratatosk loads configuration for bootstrap
    Then the effective config key "llm_provider" is "ollama"

  Scenario: ACT-1-CFG-07 OLLAMA_BASE_URL from env is used by CLI LLM client
    Given the environment variable "OLLAMA_BASE_URL" is set to "http://localhost:11434"
    When Ratatosk loads configuration for bootstrap
    Then the effective config key "ollama_base_url" is "http://localhost:11434"

  Scenario: ACT-1-CFG-08 Default LLM provider is ollama when unset
    When Ratatosk loads configuration for bootstrap
    Then the effective config key "llm_provider" is "ollama"

  Scenario: ACT-1-CFG-08b Default LLM model is qwen3:14b when unset
    When Ratatosk loads configuration for bootstrap
    Then the effective config key "llm_ollama_model" is "qwen3:14b"

  Scenario: ACT-1-CFG-09 YGGDRASIL_SERVER_URL default for CLI bootstrap server
    Given the environment variable "YGGDRASIL_SERVER_URL" is set to "http://localhost:8000"
    When Ratatosk loads configuration for bootstrap
    Then the effective config key "yggdrasil_server_url" is "http://localhost:8000"

  # ── ACT-1-LLM-ANTHROPIC — unified BASE_MODEL + provider swap ────────────────

  Scenario: ACT-1-CFG-10 LLM_PROVIDER anthropic selects Anthropic not Ollama
    Given the environment variable "LLM_PROVIDER" is set to "anthropic"
    And the environment variable "ANTHROPIC_API_KEY" is set to "sk-test-key"
    When Ratatosk loads configuration for bootstrap
    Then the effective config key "llm_provider" is "anthropic"

  Scenario: ACT-1-CFG-11 BASE_MODEL haiku resolves to Anthropic Haiku model id
    Given the environment variable "LLM_PROVIDER" is set to "anthropic"
    And the environment variable "BASE_MODEL" is set to "haiku"
    And the environment variable "ANTHROPIC_API_KEY" is set to "sk-test-key"
    When Ratatosk loads configuration for bootstrap
    Then the effective config key "resolved_model" contains "haiku"

  Scenario: ACT-1-CFG-12 Repo .ratatosk/config.yaml sets llm_provider for bootstrap
    Given a repo config file ".ratatosk/config.yaml" with llm_provider "ollama"
    And a repo config file ".ratatosk/config.yaml" with base_model "qwen3:14b"
    When Ratatosk loads configuration for bootstrap with repo "./tests/fixtures/repos/sample_webapp"
    Then the effective config key "llm_provider" is "ollama"
    And the effective config key "resolved_model" is "qwen3:14b"

  Scenario: ACT-1-CFG-13 Environment overrides repo config for llm_provider
    Given a repo config file ".ratatosk/config.yaml" with llm_provider "ollama"
    And the environment variable "LLM_PROVIDER" is set to "anthropic"
    And the environment variable "ANTHROPIC_API_KEY" is set to "sk-test-key"
    When Ratatosk loads configuration for bootstrap with repo "./tests/fixtures/repos/sample_webapp"
    Then the effective config key "llm_provider" is "anthropic"

  @wip
  Scenario: ACT-1-CFG-14 RATATOSK_MAX_EXTRACT_TARGETS env sets scout extract ceiling
    Given the environment variable "RATATOSK_MAX_EXTRACT_TARGETS" is set to "75"
    When Ratatosk loads configuration for bootstrap
    Then the effective config key "max_extract_targets" is 75

  # ── MVP-W2: scout / update / doctor ────────────────────────────────────────

  @wip
  Scenario: ACT-1-CFG-01 Repo ratatosk.yaml overrides home defaults for scout bounds
    Given a home config file "~/.ratatosk/config.yaml" with scout max_rounds 10
    And a repo config file "ratatosk.yaml" with scout max_rounds 5
    When Priya runs ratatosk update with repo "./repo" and stdin fixture "pr.diff"
    Then the effective scout max_rounds is 5

  @wip
  Scenario: ACT-1-CFG-03 Tool allowlist restricts scout to configured connectors
    Given a repo config file "ratatosk.yaml" with tools:
      | allow |
      | local |
      | mcp.yggdrasil |
    And Ratatosk config disallows connector "mcp.atlassian"
    When Marcus pipes commit message stdin into ratatosk update with repo "./repo":
      """
      feat: change #MIM-056
      """
    Then no MCP tool call to connector "mcp.atlassian" was recorded

  @wip
  Scenario: ACT-1-CFG-04 Secrets resolve from env:VAR only
    Given a repo config file "ratatosk.yaml" with atlassian token "env:ATLASSIAN_TOKEN"
    And the environment variable ATLASSIAN_TOKEN is set
    When Ratatosk loads configuration for update
    Then the atlassian token is resolved from the environment
    And the repo config file does not contain a plaintext secret

  @wip
  Scenario: ACT-1-CFG-05 ratatosk doctor validates config and connectivity
    Given Priya has a Yggdrasil personal access token with read-write scope
    When Priya runs "ratatosk doctor --repo ./repo"
    Then the exit code is 0
    And the output contains "Yggdrasil MCP"
    And the output contains "config merge"
