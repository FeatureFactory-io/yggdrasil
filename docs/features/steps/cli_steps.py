"""
Step definitions for Ratatosk CLI (Act 1 — ACT-1-CLI-* scenarios).

Steps run the ``ratatosk`` CLI via subprocess (or direct function call when
the package is installed in editable mode). The CLI must be importable from
the test environment.

System dependency: Ollama (for real LLM calls in E2E).
AT integration tests use ScriptedLLM via LLM_PROVIDER=scripted env var.
"""

from __future__ import annotations

import logging

from behave import given, then, when  # type: ignore[import]

logger = logging.getLogger("yggdrasil.at.cli_steps")


# ─── Given steps ────────────────────────────────────────────────────────────


@given("Priya has a Yggdrasil personal access token with read-write scope")
def step_priya_has_pat(context):
    """Create or reuse a PAT for Priya in the test context."""
    raise NotImplementedError()


@given('the Yggdrasil model "Yggdrasil" exists with no elements')
def step_empty_model(context):
    """Create an empty YggdrasilModel in the test DB."""
    raise NotImplementedError()


@given(
    'the Yggdrasil model "Yggdrasil" exists with {elem_count:d} elements and {rel_count:d} relationships'
)
def step_model_with_elements_rels(context, elem_count, rel_count):
    """Create a model with the specified element and relationship counts."""
    raise NotImplementedError()


@given("Priya has run a bootstrap with new candidates discovered")
def step_bootstrap_ran(context):
    """Set up a completed bootstrap run in the test context."""
    raise NotImplementedError()


@given("Ratatosk has produced delta buckets")
def step_ratatosk_delta_buckets(context):
    """Set up delta bucket data from the table in context."""
    raise NotImplementedError()


@given(
    "a ChangeSet with {total:d} operations where {below_threshold:d} are below confidence threshold"
)
def step_changeset_with_threshold(context, total, below_threshold):
    """Create a ChangeSet with the specified confidence distribution."""
    raise NotImplementedError()


@given("a successful bootstrap run on a Python web application repository")
def step_successful_bootstrap(context):
    """Set up a completed bootstrap run with C4 stereotypes seeded."""
    raise NotImplementedError()


# ─── When steps ─────────────────────────────────────────────────────────────


@when("Priya runs")
def step_priya_runs_cli(context):
    """Run the ratatosk CLI command from context.text (docstring)."""
    raise NotImplementedError()


# ─── Then steps ─────────────────────────────────────────────────────────────


@then("the exit code is 0")
def step_exit_code_zero(context):
    """Assert the CLI exited with code 0."""
    raise NotImplementedError()


@then("the exit code is not 0")
def step_exit_code_nonzero(context):
    """Assert the CLI exited with a non-zero code."""
    raise NotImplementedError()


@then('the output contains "{text}"')
def step_output_contains(context, text):
    """Assert the CLI stdout contains the expected text."""
    raise NotImplementedError()


@then("a link to the run result is printed")
def step_link_printed(context):
    """Assert a URL to the run detail page is in the output."""
    raise NotImplementedError()


@then("Then Munin produces ChangeSet with {count:d} planned operations")
def step_munin_produces_n_ops(context, count):
    """Assert the resulting ChangeSet has N operations."""
    raise NotImplementedError()


@then('the ChangeSet summary contains "{text}"')
def step_changeset_summary_contains(context, text):
    """Assert the ChangeSet's munin_reasoning contains the text."""
    raise NotImplementedError()


@then("{auto_count:d} operations are auto-applied to the model")
def step_auto_applied_count(context, auto_count):
    """Assert N operations were auto-applied."""
    raise NotImplementedError()


@then("{queued_count:d} operations are queued for review in the ChangeSet")
def step_queued_count(context, queued_count):
    """Assert N operations are still pending in the ChangeSet."""
    raise NotImplementedError()


@then("the model contains elements with stereotypes from")
def step_model_has_stereotypes(context):
    """Assert the model contains elements with the stereotypes from the table."""
    raise NotImplementedError()


@then("the model contains packages from")
def step_model_has_packages(context):
    """Assert the model contains packages matching the table."""
    raise NotImplementedError()
