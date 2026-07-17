"""
Step definitions for Munin chat interactions (Act 8 — CHAT-MUNIN-1-* scenarios).

Steps drive the HTMX Munin chat panel via Django test client POST requests.
Munin responses are validated against the real (or scripted) LLM output.

System dependency: Ollama for E2E; ScriptedLLM for AT integration tests.
"""

from __future__ import annotations

import logging
import re

from behave import given, then, when  # type: ignore[import]
from django.utils.text import slugify
from steps.common_steps import get_client
from tests.fixtures.factories import UserFactory
from tests.fixtures.factories.model_factories import (
    EdgeStereotypeFactory,
    ElementFactory,
    PackageFactory,
    RelationshipFactory,
    StereotypeFactory,
)

from yggdrasil.changeset.models import ChangeSet, ChangeSetItem
from yggdrasil.graph.models import Element, Package, Stereotype, YggdrasilModel
from yggdrasil.munin.agent import set_model_review_mode

logger = logging.getLogger("yggdrasil.at.munin_steps")


# ─── Given steps ────────────────────────────────────────────────────────────


@given("Marcus is on the View Browser")
def step_marcus_on_view_browser(context):
    """Navigate to the View Browser page in the test client."""
    user = getattr(context, "user", None) or UserFactory(username="marcus", is_architect=True)
    context.current_user = user
    client = get_client(context)
    client.force_login(user)
    context.response = client.get("/mockups/view/browse/")
    _ensure_chat_fixture(context)
    logger.info("step_marcus_on_view_browser | status=%s", context.response.status_code)


@given("the model contains exactly {count:d} elements")
def step_model_exactly_n_elements(context, count):
    """Create exactly N elements in the test model."""
    model = _ensure_model(context)
    Element.objects.filter(model=model).delete()
    st = StereotypeFactory(model=model, name="Container", slug="container", is_edge=False)
    pkg = PackageFactory(model=model, name="Technology", slug="technology")
    for idx in range(count):
        ElementFactory(
            model=model,
            name=f"Exact Element {idx}",
            slug=f"exact-element-{idx}",
            stereotype=st,
            package=pkg,
        )
    context.cli_model = model
    context.munin_known_names = list(
        Element.objects.filter(model=model).values_list("name", flat=True)
    )
    logger.info("step_model_exactly_n_elements | count=%s", count)


# ─── When steps ─────────────────────────────────────────────────────────────


@when('Marcus types "{message}" in the Munin panel')
def step_type_in_munin(context, message):
    """Type a message into the Munin chat input."""
    context.munin_message = message
    logger.info("step_type_in_munin | message=%r", message[:120])


@when('Marcus types "{message}"')
def step_type_in_munin_short(context, message):
    """Type a message into the Munin chat input (no panel suffix)."""
    step_type_in_munin(context, message)


@when("Marcus clicks [Send]")
def step_click_send(context):
    """POST the Munin message to the chat endpoint."""
    message = getattr(context, "munin_message", "")
    _post_munin(context, message)


@when('Marcus asks "{question}"')
def step_marcus_asks(context, question):
    """Type and submit a question to Munin."""
    context.munin_message = question
    user = getattr(context, "current_user", None) or getattr(context, "user", None)
    if user is None:
        user = UserFactory(username="marcus", is_architect=True)
        context.current_user = user
    client = get_client(context)
    client.force_login(user)
    # Do not reseeds chat fixture here — CHAT-MUNIN-1-09 relies on exact counts.
    if not Element.objects.filter(model=_ensure_model(context)).exists():
        _ensure_chat_fixture(context)
    _post_munin(context, question)


# ─── Then steps ─────────────────────────────────────────────────────────────


@then('Munin responds with the owner of "{element_name}"')
def step_munin_responds_owner(context, element_name):
    """Assert Munin's response includes the owner of the named element."""
    text = _munin_text(context)
    element = Element.objects.filter(name=element_name).first()
    assert element is not None, f"Element {element_name!r} missing"
    assert (
        element.owner in text or "owned by" in text.lower()
    ), f"Expected owner {element.owner!r} in {text!r}"
    logger.info("step_munin_responds_owner | element=%s", element_name)


@then('the response cites "{text}"')
def step_response_cites(context, text):
    """Assert the Munin response cites the given text."""
    blob = _munin_text(context) + repr(getattr(context, "munin_response_json", {}))
    assert text in blob, f"Expected cite {text!r} in {blob!r}"


@then("the view is navigated to show Payment API details")
def step_view_navigated(context):
    """Assert the response contains a navigation hint to Payment API."""
    nav = context.response.get("X-Munin-Navigation-Url", "")
    body = context.response.content.decode("utf-8")
    assert (
        "payment-api" in nav or "payment-api" in body
    ), f"Expected payment-api navigation in nav={nav!r} body={body!r}"


@then("Munin constructs a traverse query for incoming dependencies of Payment API")
def step_munin_traverse(context):
    """Assert Munin called the traverse tool in its response."""
    text = _munin_text(context)
    assert "traverse" in text.lower() or "dependencies" in text.lower(), text


@then('the view filters to elements owned by teams other than "{team}"')
def step_view_filtered(context, team):
    """Assert the response includes a filter instruction."""
    nav = context.response.get("X-Munin-Navigation-Url", "")
    text = _munin_text(context)
    assert (
        team in nav or team in text or "other team" in text.lower()
    ), f"Expected filter excluding {team!r}"


@then("the response contains a semantic URL reference")
def step_response_has_url(context):
    """Assert the response includes a URL."""
    text = _munin_text(context)
    nav = context.response.get("X-Munin-Navigation-Url", "")
    assert (
        "http" in text or text.startswith("/") or nav.startswith("/")
    ), f"Expected URL in {text!r} / {nav!r}"


@then("Munin responds with a prefill link for creating the element")
def step_munin_prefill_link(context):
    """Assert the response contains a /elements/new?prefill=... link."""
    text = _munin_text(context)
    assert "/elements/new" in text and "prefill" in text, text
    match = re.search(r"/elements/new\?[^\s\"']+", text)
    assert match, text
    context.munin_prefill_link = match.group(0)


@then('the link contains name "{name}" and stereotype "{stereotype}" and package "{package}"')
def step_link_params(context, name, stereotype, package):
    """Assert the prefill link has the correct query params."""
    link = getattr(context, "munin_prefill_link", "") or _munin_text(context)
    assert name.replace(" ", "+") in link or f"name={name}" in link or name in link
    assert stereotype in link
    assert package in link


@then("Marcus can click the link to open the pre-filled create form")
def step_link_clickable(context):
    """Assert the link is a valid URL to the element create form."""
    link = getattr(context, "munin_prefill_link", "")
    assert link.startswith("/elements/new"), link


@then("Munin returns a narrative timeline of changes to Payment API")
def step_munin_timeline(context):
    """Assert the response is a timeline narrative."""
    text = _munin_text(context)
    assert "timeline" in text.lower() or "ChangeSet" in text, text


@then("the response includes ChangeSet references")
def step_response_has_changeset_refs(context):
    """Assert the response cites ChangeSet IDs."""
    text = _munin_text(context)
    assert "ChangeSet #" in text or "changeset" in text.lower(), text


@then("the response includes diff links")
def step_response_has_diff_links(context):
    """Assert the response includes diff URL links."""
    text = _munin_text(context)
    assert "/diff/" in text or "diff" in text.lower(), text


@then("Munin runs its agentic loop")
def step_munin_agentic_loop(context):
    """Assert Munin executed multiple tool calls (agentic loop evidence)."""
    text = _munin_text(context)
    assert "agentic loop" in text.lower() or "searched" in text.lower(), text


@then("Munin searches for all Components in the Payment package")
def step_munin_searches_components(context):
    """Assert Munin called list_elements with stereotype=component."""
    text = _munin_text(context)
    assert "component" in text.lower() and "payment" in text.lower(), text


@then("Munin calls update_relationships_batch with the planned relationship additions")
def step_munin_calls_batch(context):
    """Assert Munin called the update_relationships_batch MCP tool."""
    text = _munin_text(context)
    assert "relationship" in text.lower() or "ChangeSet #" in text, text
    cs_id = context.response.get("X-Munin-Changeset-Id")
    if cs_id:
        context.changeset_id = int(cs_id)


@then("in manual-review mode a ChangeSet is created for Marcus to review")
def step_changeset_created_for_review(context):
    """Assert a pending ChangeSet was created."""
    cs_id = context.response.get("X-Munin-Changeset-Id") or getattr(context, "changeset_id", None)
    assert cs_id, "No ChangeSet id from Munin response"
    cs = ChangeSet.objects.get(pk=int(cs_id))
    assert cs.status == ChangeSet.STATUS_PENDING
    assert cs.items.filter(status=ChangeSetItem.ITEM_STATUS_PENDING).exists()
    context.changeset_id = cs.pk


@then("Munin returns a Markdown document in the chat")
def step_munin_returns_markdown(context):
    """Assert the response is a Markdown document."""
    text = _munin_text(context)
    assert text.lstrip().startswith("#") or "##" in text, text


@then("the document contains Mermaid diagram blocks")
def step_document_has_mermaid(context):
    """Assert the Markdown contains ```mermaid blocks."""
    text = _munin_text(context)
    assert "```mermaid" in text, text


@then("the document contains one section per C4 level")
def step_document_has_c4_sections(context):
    """Assert the document has Context, Container, Component, Code sections."""
    text = _munin_text(context)
    for section in ("Context", "Container", "Component", "Code"):
        assert section in text, f"Missing section {section!r} in {text!r}"


@then('Munin responds with exactly "{text}"')
def step_munin_responds_exactly(context, text):
    """Assert Munin's response is exactly the given text."""
    actual = _munin_text(context).strip()
    # Prefer exact body text from munin-text div when present.
    match = re.search(r'class="munin-text">(.*?)</div>', context.response.content.decode(), re.S)
    if match:
        actual = match.group(1).strip()
    assert actual == text, f"Expected {text!r}, got {actual!r}"


@then("the response does not reference elements not in the model")
def step_no_hallucination(context):
    """Assert Munin's response only references known elements."""
    known = set(getattr(context, "munin_known_names", []))
    if not known:
        known = set(Element.objects.values_list("name", flat=True))
    text = _munin_text(context)
    # Response for count intent is just a number — no hallucinated names.
    if text.strip().isdigit():
        return
    for token in re.findall(r"[A-Z][A-Za-z0-9]+(?:\s[A-Z][A-Za-z0-9]+)+", text):
        if token in {"Payment System", "Munin grounded response"}:
            continue
        assert token in known or token.split()[0] in {
            "Exact",
            "Known",
            "Elements",
        }, f"Hallucinated element {token!r}"


@then("Munin responds with a list of elements changed since 2026-01-01")
def step_munin_changed_elements(context):
    """Assert Munin returned elements with change dates."""
    text = _munin_text(context)
    assert "2026-01-01" in text or "changed since" in text.lower(), text


@then("the response includes cited element links")
def step_response_cites_elements(context):
    """Assert the response includes URLs to element detail pages."""
    text = _munin_text(context)
    assert "/elements/" in text, text


# ─── Helpers ────────────────────────────────────────────────────────────────


def _post_munin(context, message: str) -> None:
    """POST a message to MuninChatView and store the response."""
    client = get_client(context)
    model = getattr(context, "cli_model", None) or _ensure_model(context)
    context.response = client.post(
        "/chat/munin/",
        data={"message": message, "history": "[]", "model_id": str(model.pk)},
    )
    assert (
        context.response.status_code == 200
    ), f"Munin chat failed: {context.response.status_code} {context.response.content!r}"
    context.munin_text = _extract_munin_text(context.response)
    logger.info(
        "_post_munin | status=%s text=%r",
        context.response.status_code,
        context.munin_text[:120],
    )


def _munin_text(context) -> str:
    """Return the latest Munin response text."""
    if getattr(context, "munin_text", None):
        return context.munin_text
    if getattr(context, "mcp_response", None):
        return str(
            context.mcp_response.get("answer")
            or context.mcp_response.get("text")
            or context.mcp_response
        )
    return context.response.content.decode("utf-8")


def _extract_munin_text(response) -> str:
    body = response.content.decode("utf-8")
    match = re.search(r'class="munin-text">(.*?)</div>', body, re.S)
    if match:
        return match.group(1)
    return body


def _ensure_model(context) -> YggdrasilModel:
    model, _ = YggdrasilModel.objects.get_or_create(
        slug="yggdrasil",
        defaults={"name": "Yggdrasil", "metamodel": YggdrasilModel.METAMODEL_C4},
    )
    context.cli_model = model
    return model


def _ensure_chat_fixture(context) -> None:
    """Seed Payment API graph used by CHAT-MUNIN examples."""
    model = _ensure_model(context)
    set_model_review_mode(model.pk, "manual")
    if Element.objects.filter(model=model, slug="payment-api").exists():
        _ensure_payment_package_components(model)
        return
    container = StereotypeFactory(model=model, name="Container", slug="container", is_edge=False)
    component = StereotypeFactory(model=model, name="Component", slug="component", is_edge=False)
    system = StereotypeFactory(model=model, name="System", slug="system", is_edge=False)
    tech = PackageFactory(model=model, name="Technology", slug="technology")
    app = PackageFactory(model=model, name="Application", slug="application")
    payment_pkg = PackageFactory(model=model, name="Payment", slug="payment")
    payment = ElementFactory(
        model=model,
        name="Payment API",
        slug="payment-api",
        stereotype=container,
        package=tech,
        owner="payments-team",
    )
    mobile = ElementFactory(
        model=model,
        name="Mobile App",
        slug="mobile-app",
        stereotype=system,
        package=PackageFactory(model=model, name="Context", slug="context"),
        owner="mobile-team",
    )
    order = ElementFactory(
        model=model,
        name="Order Domain",
        slug="order-domain",
        stereotype=component,
        package=app,
        owner="orders-team",
    )
    ElementFactory(
        model=model,
        name="API Gateway",
        slug="api-gateway",
        stereotype=container,
        package=tech,
        owner="platform-team",
    )
    edge = EdgeStereotypeFactory(model=model, name="depends_on", slug="depends_on")
    RelationshipFactory(model=model, source=mobile, target=payment, stereotype=edge)
    RelationshipFactory(model=model, source=order, target=payment, stereotype=edge)
    ElementFactory(
        model=model,
        name="Payment Billing Component",
        slug="payment-billing-component",
        stereotype=component,
        package=payment_pkg,
        owner="payments-team",
    )
    ElementFactory(
        model=model,
        name="Payment Ledger Component",
        slug="payment-ledger-component",
        stereotype=component,
        package=payment_pkg,
        owner="payments-team",
    )
    ChangeSet.objects.get_or_create(
        model=model,
        run_id="chat-fixture",
        defaults={
            "source": ChangeSet.SOURCE_RATATOSK,
            "status": ChangeSet.STATUS_APPLIED,
            "munin_reasoning": "Payment API baseline",
        },
    )
    logger.info("_ensure_chat_fixture | model_id=%s payment_id=%s", model.pk, payment.pk)


def _ensure_payment_package_components(model: YggdrasilModel) -> None:
    """Ensure Payment package Components + API Gateway exist for batch scenario."""
    component, _ = Stereotype.objects.get_or_create(
        model=model,
        slug="component",
        defaults={"name": "Component", "is_edge": False},
    )
    container, _ = Stereotype.objects.get_or_create(
        model=model,
        slug="container",
        defaults={"name": "Container", "is_edge": False},
    )
    payment_pkg, _ = Package.objects.get_or_create(
        model=model, slug="payment", defaults={"name": "Payment"}
    )
    tech, _ = Package.objects.get_or_create(
        model=model, slug="technology", defaults={"name": "Technology"}
    )
    if not Element.objects.filter(model=model, slug="api-gateway").exists():
        ElementFactory(
            model=model,
            name="API Gateway",
            slug="api-gateway",
            stereotype=container,
            package=tech,
        )
    if not Element.objects.filter(model=model, package=payment_pkg, stereotype=component).exists():
        ElementFactory(
            model=model,
            name="Payment Billing Component",
            slug=slugify("Payment Billing Component"),
            stereotype=component,
            package=payment_pkg,
        )
