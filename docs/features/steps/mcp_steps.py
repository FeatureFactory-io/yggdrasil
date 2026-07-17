"""
Step definitions for MCP tool calls (Act 5 scenarios).

All steps call the FastMCP server in-process via the AsyncClient transport
(T1 pattern from artifact 57 §7). No subprocess, no real HTTP server needed
for AT; behave-django provides the Django context.

Usage pattern:
    When Priya calls MCP tool "list_elements" with:
      | param | value     |
      | model | Yggdrasil |
    Then the response contains 6 elements
"""

from __future__ import annotations

import ast
import logging
from typing import Any

from behave import given, then, when  # type: ignore[import]
from django.utils.text import slugify
from tests.fixtures.factories import UserFactory
from tests.fixtures.factories.model_factories import (
    EdgeStereotypeFactory,
    ElementFactory,
    PackageFactory,
    RelationshipFactory,
    StereotypeFactory,
    YggdrasilModelFactory,
)

from yggdrasil.changeset.models import ChangeSet, ChangeSetItem
from yggdrasil.graph.models import Element, YggdrasilModel
from yggdrasil.mcp import server as mcp_server
from yggdrasil.mcp.tools import changeset as changeset_tools
from yggdrasil.mcp.tools import query as query_tools
from yggdrasil.ratatosk.models import RataskRun

logger = logging.getLogger("yggdrasil.at.mcp_steps")

_TOOL_REGISTRY: dict[str, Any] = {
    "approve_changeset": changeset_tools.approve_changeset,
    "reject_changeset": changeset_tools.reject_changeset,
    "do_other_changeset": changeset_tools.do_other_changeset,
    "ask_munin": changeset_tools.ask_munin,
    "list_elements": query_tools.list_elements,
    "search": query_tools.search,
    "get_element": query_tools.get_element,
    "traverse": query_tools.traverse,
    "list_changesets": query_tools.list_changesets,
    "get_changeset": query_tools.get_changeset,
    "list_stereotypes": query_tools.list_stereotypes,
    "list_ratatosk_runs": query_tools.list_ratatosk_runs,
}

_SEED_ELEMENTS: list[tuple[str, str, str]] = [
    ("Payment API", "Container", "Technology"),
    ("Mobile App", "System", "Context"),
    ("Order Domain", "Component", "Application"),
    ("Notification Service", "Container", "Technology"),
    # Not a Container — QUERY-05 expects Container filter to exclude it.
    ("PostgreSQL", "System", "Technology"),
    ("LegacyBatch", "Container", "Technology"),
]


# ─── Given steps ────────────────────────────────────────────────────────────


@given("Priya has a valid read-write token configured in mcp_config.json")
def step_priya_has_rw_token(context):
    """Set up a read-write token in the test context."""
    user = UserFactory(username="priya", is_architect=True)
    context.current_user = user
    context.mcp_token_scope = "read-write"
    _ensure_query_fixture(context)
    logger.info("step_priya_has_rw_token | user=%s", user.pk)


@given("Priya has a valid read-write token")
def step_priya_has_rw_token_short(context):
    """Alias for the token setup step."""
    step_priya_has_rw_token(context)


@given("Priya has a read-only token")
def step_priya_has_ro_token(context):
    """Set up a read-only token in the test context."""
    user = UserFactory(username="priya-ro", is_viewer=True)
    context.current_user = user
    context.mcp_token_scope = "read-only"
    logger.info("step_priya_has_ro_token | user=%s", user.pk)


@given('the model "{model_name}" contains {count:d} elements')
def step_model_has_n_elements(context, model_name, count):
    """Create N elements in the specified model."""
    model = YggdrasilModelFactory(name=model_name, slug=slugify(model_name))
    context.mcp_model = model
    for name, stereotype_name, package_name in _SEED_ELEMENTS[:count]:
        stereotype = StereotypeFactory(
            model=model,
            name=stereotype_name,
            slug=slugify(stereotype_name),
            is_edge=False,
        )
        package = PackageFactory(
            model=model,
            name=package_name,
            slug=slugify(package_name),
        )
        ElementFactory(
            model=model,
            name=name,
            slug=slugify(name),
            stereotype=stereotype,
            package=package,
            owner="payments-team" if name == "Payment API" else "",
            properties={"framework": "FastAPI"} if name == "Payment API" else {},
        )
    logger.info(
        "step_model_has_n_elements | model=%s count=%s",
        model.slug,
        count,
    )


@given("the model has ChangeSet id={cs_id:d} (run-{run_id}, pending, {op_count:d} operations)")
def step_model_has_changeset(context, cs_id, run_id, op_count):
    """Create a pending ChangeSet with N operations in the test DB."""
    model = _ensure_model()
    context.current_user = getattr(context, "current_user", None) or UserFactory(
        username="priya", is_architect=True
    )
    changeset = ChangeSet(
        pk=cs_id,
        model=model,
        source=ChangeSet.SOURCE_RATATOSK,
        status=ChangeSet.STATUS_PENDING,
        review_mode=ChangeSet.REVIEW_MANUAL,
        run_id=f"run-{run_id}",
        munin_reasoning="I analysed 3 services and proposed graph updates",
    )
    changeset.save()
    ChangeSetItem.objects.filter(changeset=changeset).delete()
    names = [
        "Notification Service",
        "Payment API",
        "Mobile App",
        "Order Domain",
        "LegacyBatch",
        "PostgreSQL",
    ]
    for order in range(1, op_count + 1):
        item_kwargs: dict[str, Any] = {
            "changeset": changeset,
            "order": order,
            "op_type": ChangeSetItem.OP_ADD_ELEMENT,
            "detail": {
                "name": names[order - 1] if order <= len(names) else f"Element {order}",
                "stereotype_slug": "container",
            },
            "status": ChangeSetItem.ITEM_STATUS_PENDING,
            "confidence": 0.9,
        }
        if cs_id == 1:
            item_kwargs["pk"] = order
        ChangeSetItem.objects.create(**item_kwargs)
    context.changeset_id = cs_id
    logger.info(
        "step_model_has_changeset | id=%s run=%s ops=%s",
        cs_id,
        run_id,
        op_count,
    )


@given("the model has {count:d} completed Ratatosk runs")
def step_model_has_ratatosk_runs(context, count):
    """Create N completed RataskRun records."""
    model = _ensure_model()
    context.current_user = getattr(context, "current_user", None) or UserFactory(
        username="ci-agent", is_architect=True
    )
    cs = ChangeSet.objects.filter(pk=1).first()
    if cs is None:
        cs = ChangeSet.objects.create(
            pk=1,
            model=model,
            source=ChangeSet.SOURCE_RATATOSK,
            status=ChangeSet.STATUS_APPLIED,
            run_id="run-linked",
        )
    RataskRun.objects.filter(model=model).delete()
    for i in range(1, count + 1):
        RataskRun.objects.create(
            pk=i,
            model=model,
            run_id=f"run-{i:03d}",
            repo_path="./repo",
            status=RataskRun.STATUS_COMPLETE,
            changeset=cs if i == 3 else None,
        )
    context.mcp_model = model
    logger.info("step_model_has_ratatosk_runs | count=%s", count)


@given("ChangeSet id={cs_id:d} has {count:d} pending operations")
def step_changeset_has_pending_ops(context, cs_id, count):
    """Create a ChangeSet with N pending ChangeSetItems."""
    model = _ensure_model()
    changeset = ChangeSet(
        pk=cs_id,
        model=model,
        source=ChangeSet.SOURCE_RATATOSK,
        status=ChangeSet.STATUS_PENDING,
        review_mode=ChangeSet.REVIEW_MANUAL,
        run_id=f"run-{cs_id:03d}",
        munin_reasoning="Pending ChangeSet for MCP AT",
    )
    changeset.save()
    ChangeSetItem.objects.filter(changeset=changeset).delete()
    for order in range(1, count + 1):
        item_kwargs: dict[str, Any] = {
            "changeset": changeset,
            "order": order,
            "op_type": ChangeSetItem.OP_ADD_ELEMENT,
            "detail": {
                "name": f"Element {order}",
                "stereotype_slug": "container",
                "package_slug": "technology",
            },
            "status": ChangeSetItem.ITEM_STATUS_PENDING,
            "confidence": 0.9,
        }
        # Stable PKs for item_ids assertions in ACT-5-MCP-CHANGESET-02+.
        if cs_id == 1:
            item_kwargs["pk"] = order
        ChangeSetItem.objects.create(**item_kwargs)
    context.changeset_id = cs_id
    context.mcp_changeset = changeset
    logger.info(
        "step_changeset_has_pending_ops | changeset_id=%s pending=%s",
        cs_id,
        count,
    )


@given("ChangeSet id={cs_id:d} has operations {item_ids}")
def step_changeset_has_operations(context, cs_id, item_ids):
    """Create a ChangeSet with specific item IDs."""
    ids = _parse_id_list(item_ids)
    model = _ensure_model()
    changeset = ChangeSet(
        pk=cs_id,
        model=model,
        source=ChangeSet.SOURCE_RATATOSK,
        status=ChangeSet.STATUS_PENDING,
        review_mode=ChangeSet.REVIEW_MANUAL,
        run_id=f"run-{cs_id:03d}",
        munin_reasoning="Pending ChangeSet for MCP partial-approve AT",
    )
    changeset.save()
    ChangeSetItem.objects.filter(changeset=changeset).delete()
    for order, declared_id in enumerate(ids, start=1):
        ChangeSetItem.objects.create(
            pk=declared_id,
            changeset=changeset,
            order=order,
            op_type=ChangeSetItem.OP_ADD_ELEMENT,
            detail={
                "name": f"Element {declared_id}",
                "stereotype_slug": "container",
                "package_slug": "technology",
            },
            status=ChangeSetItem.ITEM_STATUS_PENDING,
            confidence=0.9,
        )
    context.changeset_id = cs_id
    context.mcp_changeset = changeset
    logger.info(
        "step_changeset_has_operations | changeset_id=%s item_ids=%s",
        cs_id,
        ids,
    )


@given('the model contains element "{name}" with owner "{owner}"')
def step_model_has_element_with_owner(context, name, owner):
    """Ensure an element exists with the given owner."""
    raise NotImplementedError()


@given('the model contains element "{name}" (id={elem_id:d}) with {count:d} relationships')
def step_model_has_element_with_rels(context, name, elem_id, count):
    """Create an element with N relationships."""
    raise NotImplementedError()


@given('the model contains "{name1}" and "{name2}"')
def step_model_has_two_elements(context, name1, name2):
    """Ensure two named elements exist in the model."""
    raise NotImplementedError()


@given("ChangeSet id={cs_id:d} has operation id={op_id:d} ({op_description})")
def step_changeset_has_specific_op(context, cs_id, op_id, op_description):
    """Create a ChangeSet with a specific operation."""
    raise NotImplementedError()


@given("a post-merge ChangeSet with {count:d} operations")
def step_post_merge_changeset(context, count):
    """Create a ChangeSet with operations from the table."""
    raise NotImplementedError()


@given('the model "Yggdrasil" is in {mode}-review mode')
def step_model_in_mode(context, mode):
    """Set the model review mode."""
    raise NotImplementedError()


@given('the model "Yggdrasil" is currently in {mode}-review mode')
def step_model_currently_in_mode(context, mode):
    """Set the model review mode (alias)."""
    raise NotImplementedError()


@given("Elena wants to see the domain model as of {date}")
def step_elena_wants_historical(context, date):
    """Set up historical context for Elena's query."""
    user = UserFactory(username="elena", is_architect=True)
    context.current_user = user
    context.as_of = date
    _ensure_query_fixture(context)
    logger.info("step_elena_wants_historical | as_of=%s user=%s", date, user.pk)


@given("Elena has a valid read-only token in Claude Desktop")
def step_elena_has_ro_token(context):
    """Set up a read-only token for Elena."""
    raise NotImplementedError()


@given("Priya is in Cursor and wants to know what depends on Payment API")
def step_priya_in_cursor(context):
    """Set up Priya + query fixture for traverse scenarios."""
    user = UserFactory(username="priya", is_architect=True)
    context.current_user = user
    _ensure_query_fixture(context)
    logger.info("step_priya_in_cursor | user=%s", user.pk)


@given("Marcus has a Python script to wire a new service's relationships")
def step_marcus_has_script(context):
    """No-op setup."""
    pass


# ─── When steps ─────────────────────────────────────────────────────────────


@when('Priya calls MCP tool "{tool_name}" with:')
def step_call_mcp_tool_with_table(context, tool_name):
    """Call an MCP tool with parameters from a table."""
    user = getattr(context, "current_user", None) or UserFactory(
        username="priya", is_architect=True
    )
    _call_mcp_tool(context, tool_name, user=user)


@when('Priya calls MCP tool "{tool_name}" with no params')
def step_call_mcp_tool_no_params(context, tool_name):
    """Call an MCP tool with no parameters."""
    user = getattr(context, "current_user", None) or UserFactory(
        username="priya", is_architect=True
    )
    context.table = None
    _call_mcp_tool(context, tool_name, user=user)


@when('the CI agent calls MCP tool "{tool_name}" with:')
def step_ci_agent_calls_tool(context, tool_name):
    """CI agent calls an MCP tool — same as Priya call but under CI identity."""
    user = UserFactory(username="ci-agent", is_architect=True)
    _call_mcp_tool(context, tool_name, user=user)


@when('Elena calls MCP tool "{tool_name}" with:')
def step_elena_calls_tool(context, tool_name):
    """Elena calls an MCP tool."""
    user = getattr(context, "current_user", None) or UserFactory(
        username="elena", is_architect=True
    )
    _call_mcp_tool(context, tool_name, user=user)


@when('Marcus calls MCP tool "{tool_name}" with:')
def step_marcus_calls_tool(context, tool_name):
    """Marcus calls an MCP tool."""
    user = getattr(context, "current_user", None) or UserFactory(
        username="marcus", is_architect=True
    )
    _call_mcp_tool(context, tool_name, user=user)


@when('Priya calls MCP tool "{tool_name}" with name "{element_name}"')
def step_call_tool_with_name(context, tool_name, element_name):
    """Call a tool with a single name argument."""
    raise NotImplementedError()


@when(
    'Marcus calls MCP tool "update_relationships_batch" with {count:d} create-relationship operations'
)
def step_call_batch_tool(context, count):
    """Call update_relationships_batch with N operations."""
    raise NotImplementedError()


@when("the CI agent approves operations with confidence >= {threshold:f}")
def step_ci_approves_high_confidence(context, threshold):
    """CI agent approves high-confidence operations."""
    raise NotImplementedError()


@when("calls do_other_changeset for operation {op_id:d} with instructions {instructions}")
def step_ci_do_other(context, op_id, instructions):
    """CI agent redirects one operation."""
    raise NotImplementedError()


@when("subsequent create_element calls apply directly without queuing")
def step_verify_auto_mode(context):
    """Verify that auto-mode is now in effect."""
    raise NotImplementedError()


# ─── Then steps ─────────────────────────────────────────────────────────────


@then("the response contains {count:d} elements")
def step_response_has_n_elements(context, count):
    """Assert the MCP response contains exactly N elements."""
    response = context.mcp_response
    assert response is not None, "No mcp_response on context"
    items = response.get("items", response if isinstance(response, list) else [])
    assert len(items) == count, f"Expected {count} elements, got {len(items)}: {items!r}"
    logger.info("step_response_has_n_elements | count=%s", count)


@then('element "{name}" is in the response with stereotype "{stereotype}"')
def step_element_in_response(context, name, stereotype):
    """Assert a named element is present with the given stereotype."""
    items = context.mcp_response.get("items", [])
    match = next((item for item in items if item.get("name") == name), None)
    assert match is not None, f"Element {name!r} not in response items={items!r}"
    actual = match.get("stereotype") or match.get("stereotype_slug")
    assert actual.lower() == stereotype.lower() or slugify(actual) == slugify(
        stereotype
    ), f"Element {name!r} stereotype={actual!r}, expected {stereotype!r}"
    logger.info("step_element_in_response | name=%s stereotype=%s", name, stereotype)


@then('the response contains "{value}"')
def step_response_contains_str(context, value):
    """Assert the response contains the given string or field value."""
    blob = repr(context.mcp_response)
    assert value in blob, f"Expected {value!r} in response {context.mcp_response!r}"
    logger.info("step_response_contains_str | value=%s", value)


@then('the response does not contain "{value}"')
def step_response_not_contain(context, value):
    """Assert the response does not contain the value."""
    blob = repr(context.mcp_response)
    assert value not in blob, f"Did not expect {value!r} in response {context.mcp_response!r}"
    logger.info("step_response_not_contain | value=%s", value)


@then("the response contains:")
def step_response_contains_table(context):
    """Assert the response contains all field/value pairs from the table."""
    response = context.mcp_response
    for row in context.table:
        field = row["field"]
        expected = row["value"]
        actual = response.get(field)
        assert str(actual) == expected, f"field {field}: expected {expected!r}, got {actual!r}"
    logger.info("step_response_contains_table | ok")


@then('the response contains a "{field}" field with "{key}": "{value}"')
def step_response_has_field_key(context, field, key, value):
    """Assert a nested field exists with a specific key/value pair."""
    nested = context.mcp_response.get(field)
    assert isinstance(nested, dict), f"Expected dict at {field!r}, got {nested!r}"
    assert str(nested.get(key)) == value, f"{field}.{key}={nested.get(key)!r}, expected {value!r}"
    logger.info("step_response_has_field_key | %s.%s=%s", field, key, value)


@then('the response contains a "{field}" field')
def step_response_has_field(context, field):
    """Assert the response contains the named field."""
    assert field in context.mcp_response, f"Missing field {field!r} in {context.mcp_response!r}"
    logger.info("step_response_has_field | field=%s", field)


@then("the response reflects the model state as of {date}")
def step_response_is_historical(context, date):
    """Assert the response is scoped to the historical timestamp."""
    assert (
        context.mcp_response.get("as_of") == date
    ), f"Expected as_of={date!r}, got {context.mcp_response!r}"
    logger.info("step_response_is_historical | as_of=%s", date)


@then("the response header or metadata indicates the historical timestamp")
def step_response_has_timestamp(context):
    """Assert the response carries a historical timestamp."""
    assert "as_of" in context.mcp_response, f"Missing as_of in {context.mcp_response!r}"
    logger.info("step_response_has_timestamp | as_of=%s", context.mcp_response.get("as_of"))


@then('the response contains a ChangeSet with status "{status}"')
def step_response_has_changeset_status(context, status):
    """Assert a ChangeSet with the given status is in the response."""
    items = context.mcp_response.get("items", [])
    assert any(
        item.get("status") == status for item in items
    ), f"No ChangeSet with status={status!r} in {items!r}"
    logger.info("step_response_has_changeset_status | status=%s", status)


@then('the response contains ChangeSets with status "{status}"')
def step_response_has_changesets_status(context, status):
    """Assert ChangeSets with the given status are in the response."""
    step_response_has_changeset_status(context, status)


@then("the response contains {count:d} operations")
def step_response_has_n_ops(context, count):
    """Assert the response contains N operations."""
    ops = context.mcp_response.get("operations", [])
    assert len(ops) == count, f"Expected {count} ops, got {len(ops)}"
    logger.info("step_response_has_n_ops | count=%s", count)


@then('the response contains "{name}" in an Add Element operation')
def step_response_has_add_element(context, name):
    """Assert an Add Element operation for the named element is present."""
    ops = context.mcp_response.get("operations", [])
    match = next(
        (op for op in ops if op.get("op_type") == "add_element" and name in repr(op.get("detail"))),
        None,
    )
    assert match is not None, f"No add_element for {name!r} in {ops!r}"
    logger.info("step_response_has_add_element | name=%s", name)


@then('the response contains stereotype "{name}"')
def step_response_has_stereotype(context, name):
    """Assert a stereotype is in the response."""
    items = context.mcp_response.get("items", [])
    assert any(item.get("name") == name for item in items), f"Stereotype {name!r} not in {items!r}"
    logger.info("step_response_has_stereotype | name=%s", name)


@then("each entry includes the property_schema")
def step_entries_have_property_schema(context):
    """Assert each entry has a property_schema field."""
    items = context.mcp_response.get("items", [])
    assert items, "No stereotype items in response"
    for item in items:
        assert "property_schema" in item, f"Missing property_schema in {item!r}"
    logger.info("step_entries_have_property_schema | count=%s", len(items))


@then("the response contains {count:d} runs")
def step_response_has_n_runs(context, count):
    """Assert the response contains N runs."""
    items = context.mcp_response.get("items", [])
    assert len(items) == count, f"Expected {count} runs, got {len(items)}"
    logger.info("step_response_has_n_runs | count=%s", count)


@then('run id={run_id:d} has status "{status}" and changeset_id={cs_id:d}')
def step_run_has_status(context, run_id, status, cs_id):
    """Assert a specific run has the given status and changeset_id."""
    items = context.mcp_response.get("items", [])
    run = next((item for item in items if item.get("id") == run_id), None)
    assert run is not None, f"Run id={run_id} not in {items!r}"
    assert run.get("status") == status, f"status={run.get('status')!r}, expected {status!r}"
    assert (
        run.get("changeset_id") == cs_id
    ), f"changeset_id={run.get('changeset_id')!r}, expected {cs_id}"
    logger.info("step_run_has_status | id=%s status=%s cs=%s", run_id, status, cs_id)


@then("all {count:d} operations are applied to the model")
def step_all_ops_applied(context, count):
    """Assert N operations have been applied to the graph."""
    cs_id = context.changeset_id
    accepted = ChangeSetItem.objects.filter(
        changeset_id=cs_id,
        status=ChangeSetItem.ITEM_STATUS_ACCEPTED,
    ).count()
    assert accepted == count, f"Expected {count} accepted ops on ChangeSet {cs_id}, got {accepted}"
    logger.info("step_all_ops_applied | changeset_id=%s accepted=%s", cs_id, accepted)


@then('the ChangeSet status changes to "{status}"')
def step_changeset_status(context, status):
    """Assert the ChangeSet has the given status."""
    cs_id = context.changeset_id
    changeset = ChangeSet.objects.get(pk=cs_id)
    assert (
        changeset.status == status
    ), f"Expected ChangeSet {cs_id} status={status!r}, got {changeset.status!r}"
    logger.info("step_changeset_status | changeset_id=%s status=%s", cs_id, status)


@then("operations {item_ids} are applied")
def step_specific_ops_applied(context, item_ids):
    """Assert specific operations are applied."""
    ids = _parse_id_list(item_ids)
    for item_id in ids:
        item = ChangeSetItem.objects.get(pk=item_id)
        assert (
            item.status == ChangeSetItem.ITEM_STATUS_ACCEPTED
        ), f"Expected item {item_id} accepted, got {item.status!r}"
    logger.info("step_specific_ops_applied | item_ids=%s", ids)


@then("operations {item_ids} remain pending")
def step_specific_ops_pending(context, item_ids):
    """Assert specific operations remain pending."""
    ids = _parse_id_list(item_ids)
    for item_id in ids:
        item = ChangeSetItem.objects.get(pk=item_id)
        assert (
            item.status == ChangeSetItem.ITEM_STATUS_PENDING
        ), f"Expected item {item_id} pending, got {item.status!r}"
    cs = ChangeSet.objects.get(pk=context.changeset_id)
    assert (
        cs.status == ChangeSet.STATUS_PENDING
    ), f"Expected ChangeSet still pending, got {cs.status!r}"
    logger.info("step_specific_ops_pending | item_ids=%s", ids)


@then("all {count:d} operations are rejected")
def step_all_ops_rejected(context, count):
    """Assert all operations are rejected."""
    cs_id = context.changeset_id
    rejected = ChangeSetItem.objects.filter(
        changeset_id=cs_id,
        status=ChangeSetItem.ITEM_STATUS_REJECTED,
    ).count()
    assert rejected == count, f"Expected {count} rejected ops on ChangeSet {cs_id}, got {rejected}"
    logger.info("step_all_ops_rejected | changeset_id=%s rejected=%s", cs_id, rejected)


@then("a MuninRule is created with the provided reason text")
def step_munin_rule_created(context):
    """Assert a MuninRule was created."""
    raise NotImplementedError()


@then("the rule is prepended to Munin's BASE prompt on the next run")
def step_rule_in_base_prompt(context):
    """Assert the rule is active and will affect the next Munin run."""
    raise NotImplementedError()


@then("operation {op_id:d} is rejected")
def step_op_rejected(context, op_id):
    """Assert a specific operation is rejected."""
    raise NotImplementedError()


@then("Munin re-processes operation {op_id:d} with the instructions as context")
def step_munin_reprocesses(context, op_id):
    """Assert Munin re-processes the operation."""
    raise NotImplementedError()


@then("a replacement ChangeSet is produced with the corrected operation")
def step_replacement_changeset(context):
    """Assert a replacement ChangeSet was created."""
    raise NotImplementedError()


@then("the instructions are appended to LEARNED")
def step_instructions_learned(context):
    """Assert instructions are stored as a MuninRule."""
    raise NotImplementedError()


@then('Munin produces a ChangeSet with an "{op_type}" operation for "{name}"')
def step_munin_produces_changeset(context, op_type, name):
    """Assert Munin produced a ChangeSet with the specified operation."""
    raise NotImplementedError()


@then("in auto-approval mode the operation is applied directly")
def step_auto_applied(context):
    """Assert the operation was applied (not queued)."""
    raise NotImplementedError()


@then("the ChangeSet is retained as an audit trail")
def step_changeset_retained(context):
    """Assert the ChangeSet exists even after auto-apply."""
    raise NotImplementedError()


@then('a ChangeSet with status "{status}" is created')
def step_changeset_created_with_status(context, status):
    """Assert a ChangeSet with the given status was created."""
    raise NotImplementedError()


@then('the ChangeSet contains {count:d} operation with status "{status}"')
def step_changeset_has_op_with_status(context, count, status):
    """Assert the ChangeSet has N operations with the given status."""
    raise NotImplementedError()


@then('a ChangeSet with an "{op_type}" operation is produced')
def step_changeset_with_op(context, op_type):
    """Assert a ChangeSet with the given operation type is produced."""
    raise NotImplementedError()


@then('the operation detail contains "{detail}"')
def step_op_detail_contains(context, detail):
    """Assert the operation detail contains the given string."""
    raise NotImplementedError()


@then('Munin checks the blast-radius of deleting "{name}"')
def step_munin_blast_radius(context, name):
    """Assert Munin computed a blast-radius check."""
    raise NotImplementedError()


@then('a ChangeSet with a "{op_type}" operation is queued')
def step_changeset_queued(context, op_type):
    """Assert a ChangeSet with the given operation type is queued."""
    raise NotImplementedError()


@then('Munin validates the edge rule for "{stereotype}" on System→Container')
def step_munin_validates_edge(context, stereotype):
    """Assert Munin validated the edge stereotype rule."""
    raise NotImplementedError()


@then('Munin plans exactly {count:d} ChangeSet containing {op_count:d} "{op_type}" operations')
def step_munin_plans_batch(context, count, op_count, op_type):
    """Assert Munin planned exactly the specified batch."""
    raise NotImplementedError()


@then("the ChangeSet can be inspected via get_changeset before approval")
def step_changeset_inspectable(context):
    """Assert the ChangeSet is retrievable via get_changeset."""
    raise NotImplementedError()


@then("subsequent create_element calls apply directly without queuing")
def step_auto_mode_effective(context):
    """Assert subsequent calls go through auto-approval."""
    raise NotImplementedError()


@then('the error message contains "{text}"')
def step_error_contains(context, text):
    """Assert the error message contains the text."""
    raise NotImplementedError()


@then("each entry includes the element owner and confidence")
def step_entries_have_owner_confidence(context):
    """Assert each traversal result has owner and confidence fields."""
    nodes = context.mcp_response.get("nodes", [])
    assert nodes, "No traverse nodes in response"
    for node in nodes:
        assert "owner" in node, f"Missing owner in {node!r}"
        assert "confidence" in node, f"Missing confidence in {node!r}"
    logger.info("step_entries_have_owner_confidence | nodes=%s", len(nodes))


@then("operation {op_id:d} remains pending for human review")
def step_op_remains_pending(context, op_id):
    """Assert an operation is still pending."""
    raise NotImplementedError()


@then("operation {op_id:d} is redirected to Munin for re-planning")
def step_op_redirected(context, op_id):
    """Assert an operation has been queued for Munin re-planning."""
    raise NotImplementedError()


# ─── Helpers ────────────────────────────────────────────────────────────────


def _ensure_model() -> YggdrasilModel:
    """Return (or create) the default AT model."""
    model, created = YggdrasilModel.objects.get_or_create(
        slug="yggdrasil",
        defaults={"name": "Yggdrasil", "metamodel": YggdrasilModel.METAMODEL_C4},
    )
    logger.info("_ensure_model | model_id=%s created=%s", model.pk, created)
    return model


def _ensure_query_fixture(context) -> None:
    """
    Ensure the canonical Act-5 graph fixture exists for query scenarios.

    Creates 6 elements, incoming deps on Payment API, stereotypes, and
    one pending + one applied ChangeSet when the model is empty.
    """
    model = _ensure_model()
    context.mcp_model = model
    if Element.objects.filter(model=model).count() < 6:
        step_model_has_n_elements(context, "Yggdrasil", 6)
    payment = Element.objects.filter(model=model, slug="payment-api").first()
    mobile = Element.objects.filter(model=model, slug="mobile-app").first()
    order = Element.objects.filter(model=model, slug="order-domain").first()
    if payment and mobile and order and not payment.incoming_relationships.exists():
        edge_st = EdgeStereotypeFactory(model=model, name="depends_on", slug="depends_on")
        RelationshipFactory(
            model=model, source=mobile, target=payment, stereotype=edge_st, confidence=0.9
        )
        RelationshipFactory(
            model=model, source=order, target=payment, stereotype=edge_st, confidence=0.88
        )
        mobile.owner = "mobile-team"
        mobile.confidence = 0.95
        mobile.save(update_fields=["owner", "confidence"])
        order.owner = "orders-team"
        order.confidence = 0.91
        order.save(update_fields=["owner", "confidence"])
    if not ChangeSet.objects.filter(model=model, status=ChangeSet.STATUS_PENDING).exists():
        ChangeSet.objects.create(
            model=model,
            source=ChangeSet.SOURCE_RATATOSK,
            status=ChangeSet.STATUS_PENDING,
            run_id="run-pending",
            munin_reasoning="pending fixture",
        )
    if not ChangeSet.objects.filter(model=model, status=ChangeSet.STATUS_APPLIED).exists():
        ChangeSet.objects.create(
            model=model,
            source=ChangeSet.SOURCE_RATATOSK,
            status=ChangeSet.STATUS_APPLIED,
            run_id="run-applied",
            munin_reasoning="applied fixture",
        )
    logger.info("_ensure_query_fixture | model_id=%s", model.pk)


def _call_mcp_tool(context, tool_name: str, *, user) -> None:
    """
    Invoke an MCP tool function in-process (T2 direct call).

    FastMCP AsyncClient (T1) requires initialize_mcp(); until that skeleton is
    filled, AT exercises the same tool callables the server will register.
    """
    tool_fn = _TOOL_REGISTRY.get(tool_name)
    assert tool_fn is not None, f"Unknown MCP tool {tool_name!r}"
    params = _parse_tool_table(context)
    mcp_server.set_current_user_id(user.pk)
    context.current_user = user
    logger.info(
        "_call_mcp_tool | tool=%s user=%s params=%s",
        tool_name,
        user.pk,
        params,
    )
    try:
        context.mcp_response = tool_fn(**params)
        context.mcp_error = None
    except Exception as exc:
        context.mcp_response = None
        context.mcp_error = exc
        logger.info("_call_mcp_tool | tool=%s raised %s: %s", tool_name, type(exc).__name__, exc)
        raise
    finally:
        mcp_server.set_current_user_id(None)


def _parse_tool_table(context) -> dict[str, Any]:
    """Parse a behave table of param/value rows into tool kwargs."""
    if not getattr(context, "table", None):
        return {}
    params: dict[str, Any] = {}
    for row in context.table:
        key = row["param"].strip()
        # Python keyword: traverse(from_=...) — feature tables use "from".
        if key == "from":
            key = "from_"
        raw = row["value"].strip()
        params[key] = _coerce_param(raw)
    return params


def _coerce_param(raw: str) -> Any:
    """Coerce table cell strings to int/list/bool/str."""
    if raw.lower() in {"true", "false"}:
        return raw.lower() == "true"
    if raw.startswith("[") and raw.endswith("]"):
        return list(ast.literal_eval(raw))
    try:
        return int(raw)
    except ValueError:
        return raw


def _parse_id_list(raw: str) -> list[int]:
    """Parse '[1, 2]', '1 and 2', or '3, 4, 5, 6' into a list of ints."""
    text = raw.strip()
    if text.startswith("[") and text.endswith("]"):
        return [int(x) for x in ast.literal_eval(text)]
    normalized = text.replace(" and ", ",")
    return [int(part.strip()) for part in normalized.split(",") if part.strip()]
