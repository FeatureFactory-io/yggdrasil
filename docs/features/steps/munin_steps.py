"""
Step definitions for Munin chat interactions (Act 8 — CHAT-MUNIN-1-* scenarios).

Steps drive the HTMX Munin chat panel via Django test client POST requests.
Munin responses are validated against the real (or scripted) LLM output.

System dependency: Ollama for E2E; ScriptedLLM for AT integration tests.
"""

from __future__ import annotations

import logging

from behave import given, then, when  # type: ignore[import]

logger = logging.getLogger("yggdrasil.at.munin_steps")


# ─── Given steps ────────────────────────────────────────────────────────────


@given("Marcus is on the View Browser")
def step_marcus_on_view_browser(context):
    """Navigate to the View Browser page in the test client."""
    raise NotImplementedError()


@given("the model contains exactly {count:d} elements")
def step_model_exactly_n_elements(context, count):
    """Create exactly N elements in the test model."""
    raise NotImplementedError()


# ─── When steps ─────────────────────────────────────────────────────────────


@when('Marcus types "{message}" in the Munin panel')
def step_type_in_munin(context, message):
    """Type a message into the Munin chat input."""
    raise NotImplementedError()


@when("Marcus clicks [Send]")
def step_click_send(context):
    """POST the Munin message to the chat endpoint."""
    raise NotImplementedError()


@when('Marcus asks "{question}"')
def step_marcus_asks(context, question):
    """Type and submit a question to Munin."""
    raise NotImplementedError()


# ─── Then steps ─────────────────────────────────────────────────────────────


@then('Munin responds with the owner of "{element_name}"')
def step_munin_responds_owner(context, element_name):
    """Assert Munin's response includes the owner of the named element."""
    raise NotImplementedError()


@then('the response cites "{text}"')
def step_response_cites(context, text):
    """Assert the Munin response cites the given text."""
    raise NotImplementedError()


@then("the view is navigated to show Payment API details")
def step_view_navigated(context):
    """Assert the response contains a navigation hint to Payment API."""
    raise NotImplementedError()


@then("Munin constructs a traverse query for incoming dependencies of Payment API")
def step_munin_traverse(context):
    """Assert Munin called the traverse tool in its response."""
    raise NotImplementedError()


@then('the view filters to elements owned by teams other than "{team}"')
def step_view_filtered(context, team):
    """Assert the response includes a filter instruction."""
    raise NotImplementedError()


@then("the response contains a semantic URL reference")
def step_response_has_url(context):
    """Assert the response includes a URL."""
    raise NotImplementedError()


@then("Munin responds with a prefill link for creating the element")
def step_munin_prefill_link(context):
    """Assert the response contains a /elements/new?prefill=... link."""
    raise NotImplementedError()


@then('the link contains name "{name}" and stereotype "{stereotype}" and package "{package}"')
def step_link_params(context, name, stereotype, package):
    """Assert the prefill link has the correct query params."""
    raise NotImplementedError()


@then("Marcus can click the link to open the pre-filled create form")
def step_link_clickable(context):
    """Assert the link is a valid URL to the element create form."""
    raise NotImplementedError()


@then("Munin returns a narrative timeline of changes to Payment API")
def step_munin_timeline(context):
    """Assert the response is a timeline narrative."""
    raise NotImplementedError()


@then("the response includes ChangeSet references")
def step_response_has_changeset_refs(context):
    """Assert the response cites ChangeSet IDs."""
    raise NotImplementedError()


@then("the response includes diff links")
def step_response_has_diff_links(context):
    """Assert the response includes diff URL links."""
    raise NotImplementedError()


@then("Munin runs its agentic loop")
def step_munin_agentic_loop(context):
    """Assert Munin executed multiple tool calls (agentic loop evidence)."""
    raise NotImplementedError()


@then("Munin searches for all Components in the Payment package")
def step_munin_searches_components(context):
    """Assert Munin called list_elements with stereotype=component."""
    raise NotImplementedError()


@then("Munin calls update_relationships_batch with the planned relationship additions")
def step_munin_calls_batch(context):
    """Assert Munin called the update_relationships_batch MCP tool."""
    raise NotImplementedError()


@then("in manual-review mode a ChangeSet is created for Marcus to review")
def step_changeset_created_for_review(context):
    """Assert a pending ChangeSet was created."""
    raise NotImplementedError()


@then("Munin returns a Markdown document in the chat")
def step_munin_returns_markdown(context):
    """Assert the response is a Markdown document."""
    raise NotImplementedError()


@then("the document contains Mermaid diagram blocks")
def step_document_has_mermaid(context):
    """Assert the Markdown contains ```mermaid blocks."""
    raise NotImplementedError()


@then("the document contains one section per C4 level")
def step_document_has_c4_sections(context):
    """Assert the document has Context, Container, Component, Code sections."""
    raise NotImplementedError()


@then('Munin responds with exactly "{text}"')
def step_munin_responds_exactly(context, text):
    """Assert Munin's response is exactly the given text."""
    raise NotImplementedError()


@then("the response does not reference elements not in the model")
def step_no_hallucination(context):
    """Assert Munin's response only references known elements."""
    raise NotImplementedError()


@then("Munin responds with a list of elements changed since 2026-01-01")
def step_munin_changed_elements(context):
    """Assert Munin returned elements with change dates."""
    raise NotImplementedError()


@then("the response includes cited element links")
def step_response_cites_elements(context):
    """Assert the response includes URLs to element detail pages."""
    raise NotImplementedError()
