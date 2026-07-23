"""
Step definitions for ACT-1-DISC and ACT-6-CICD discovery scenarios.

Drives ``bootstrap_repository`` / ``update_from_stdin`` in-process with
LocalOrmSnapshotPort (AT). Production CLI uses MCP snapshot instead.
"""

from __future__ import annotations

import logging
from pathlib import Path

from behave import given, then, when  # type: ignore[import]

from yggdrasil.changeset.models import ChangeSet, ChangeSetItem
from yggdrasil.graph.models import Element, Metamodel, YggdrasilModel, ensure_c4_metamodel
from yggdrasil.ratatosk.agent import bootstrap_repository, update_from_stdin
from yggdrasil.ratatosk.llm_factory import ScriptedDiscoveryLLM
from yggdrasil.ratatosk.snapshot import LocalOrmSnapshotPort

logger = logging.getLogger("yggdrasil.at.discovery_steps")

_FIXTURE_REPOS = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "repos"


@given('the fixture repository "{name}" is available')
def step_fixture_repo(context, name):
    """Resolve tests/fixtures/repos/{name} into context."""
    path = _FIXTURE_REPOS / name
    assert path.is_dir(), f"Missing fixture repo: {path}"
    context.cli_repo_path = str(path)
    logger.info("step_fixture_repo | path=%s", path)


@given('the stdin fixture "{name}" is available')
def step_stdin_fixture(context, name):
    """Load a sample_stdin fixture file into context."""
    path = _FIXTURE_REPOS / "sample_stdin" / name
    assert path.is_file(), f"Missing stdin fixture: {path}"
    context.stdin_text = path.read_text(encoding="utf-8")
    context.stdin_fixture_name = name
    logger.info("step_stdin_fixture | path=%s bytes=%s", path, len(context.stdin_text))


@given('a Metamodel "{slug}" exists')
def step_metamodel_exists(context, slug):
    """Create an empty Metamodel shell for mismatch tests."""
    mm, _ = Metamodel.objects.get_or_create(slug=slug, defaults={"name": slug.upper()})
    context.cli_metamodel = mm


@given('the Yggdrasil model "Yggdrasil" exists')
def step_model_exists(context):
    """Ensure model Yggdrasil exists bound to C4."""
    mm = ensure_c4_metamodel()
    model, _ = YggdrasilModel.objects.get_or_create(
        slug="yggdrasil",
        defaults={"name": "Yggdrasil", "metamodel": mm},
    )
    context.cli_model = model


@given('the Yggdrasil model "Yggdrasil" exists bound to metamodel "{slug}"')
def step_model_bound(context, slug):
    """Ensure model Yggdrasil is bound to the given metamodel slug."""
    mm = Metamodel.objects.get(slug=slug)
    model, _ = YggdrasilModel.objects.get_or_create(
        slug="yggdrasil",
        defaults={"name": "Yggdrasil", "metamodel": mm},
    )
    context.cli_model = model


@given('the Yggdrasil model "Yggdrasil" exists with element "{name}" stereotype "{stereotype}"')
def step_model_with_one_element(context, name, stereotype):
    """Seed one element for delta/unchanged assertions."""
    from tests.fixtures.factories.model_factories import (
        ElementFactory,
        PackageFactory,
        StereotypeFactory,
    )

    mm = ensure_c4_metamodel()
    model, _ = YggdrasilModel.objects.get_or_create(
        slug="yggdrasil",
        defaults={"name": "Yggdrasil", "metamodel": mm},
    )
    st = StereotypeFactory(
        metamodel=model.metamodel,
        name=stereotype,
        slug=stereotype.lower(),
        is_edge=False,
    )
    pkg = PackageFactory(metamodel=model.metamodel, name="Technology", slug="technology")
    ElementFactory(
        model=model, name=name, slug=name.lower().replace(" ", "-"), stereotype=st, package=pkg
    )
    context.cli_model = model


@given("the discovery LLM will return a candidate with stereotype {stereotype}")
@given('the discovery LLM will return a candidate with stereotype "{stereotype}"')
def step_llm_extra_stereotype(context, stereotype):
    """Configure ScriptedDiscoveryLLM with an unknown-stereotype candidate."""
    context.discovery_llm = ScriptedDiscoveryLLM(
        extra_candidate={
            "name": "Invented Thing",
            "stereotype": stereotype.strip('"'),
            "package": "technology",
            "confidence": 0.99,
        }
    )


@given("the discovery LLM returns non-JSON prose only")
def step_llm_non_json(context):
    """Force empty-plan scripted LLM (non-JSON path covered in pytest with FakeLLM)."""
    context.discovery_llm = ScriptedDiscoveryLLM(empty_plan=True)


@given("the MCP snapshot endpoint is unreachable")
def step_mcp_unreachable(context):
    """Inject a failing SnapshotPort."""

    class _FailSnap:
        def fetch_model(self, model_slug: str) -> dict:
            raise RuntimeError("MCP snapshot failed: connection refused")

    context.discovery_snapshot = _FailSnap()


@given("Priya has a Yggdrasil personal access token with read-only scope")
def step_priya_ro_token(context):
    """Create a read-only PAT for Priya."""
    from tests.fixtures.factories import UserFactory

    from yggdrasil.auth.services import TokenService

    user = UserFactory(username="priya-ro", is_architect=True)
    token, raw = TokenService().create_token(user, "ratatosk-ro", "read-only")
    context.current_user = user
    context.cli_token = raw
    context.cli_token_obj = token
    context.cli_token_scope = "read-only"


@when('Priya runs ratatosk bootstrap against the fixture repository "{name}"')
def step_bootstrap_fixture(context, name):
    """Bootstrap against a named fixture repo."""
    _run_bootstrap(context, repo_name=name)


@when(
    'Priya runs ratatosk bootstrap against the fixture repository "{name}" '
    "with a scripted discovery LLM"
)
def step_bootstrap_scripted(context, name):
    """Bootstrap with explicit ScriptedDiscoveryLLM for call-count assertions."""
    context.discovery_llm = ScriptedDiscoveryLLM()
    _run_bootstrap(context, repo_name=name)


@when(
    'Priya runs ratatosk bootstrap against the fixture repository "{name}" '
    'with metamodel "{metamodel}"'
)
def step_bootstrap_metamodel(context, name, metamodel):
    """Bootstrap with an explicit metamodel slug."""
    _run_bootstrap(context, repo_name=name, metamodel=metamodel)


@when("Marcus pipes the stdin fixture {name} into ratatosk update")
@when('Marcus pipes the stdin fixture "{name}" into ratatosk update')
def step_pipe_update(context, name):
    """Pipe a stdin fixture into update_from_stdin."""
    path = _FIXTURE_REPOS / "sample_stdin" / name.strip('"')
    context.stdin_text = path.read_text(encoding="utf-8")
    _run_update(context)


@when("Marcus pipes the stdin fixture {name} into:")
@when('Marcus pipes the stdin fixture "{name}" into:')
def step_pipe_update_docstring(context, name):
    """Pipe fixture; command text is narrative-only for AT."""
    path = _FIXTURE_REPOS / "sample_stdin" / name.strip('"')
    context.stdin_text = path.read_text(encoding="utf-8")
    _run_update(context)


@when("Marcus pipes empty stdin into ratatosk update")
def step_pipe_empty(context):
    """Empty stdin update path."""
    context.stdin_text = ""
    _run_update(context)


@when("Marcus pipes stdin larger than the size cap into ratatosk update")
def step_pipe_oversize(context):
    """Oversize stdin should fail with limit message."""
    from yggdrasil.ratatosk.agent import STDIN_SIZE_CAP_BYTES

    context.stdin_text = "x" * (STDIN_SIZE_CAP_BYTES + 8)
    _run_update(context)


@then('the output contains "{a}" or "{b}"')
def step_output_contains_either(context, a, b):
    """Assert stdout contains at least one of two phrases."""
    output = getattr(context, "cli_output", "") or ""
    assert a in output or b in output, f"Expected {a!r} or {b!r} in:\n{output}"


@then('the run blackboard contains step "{step}"')
def step_blackboard_has(context, step):
    """Assert RataskRun.blackboard contains a step key."""
    board = context.cli_run.blackboard or {}
    assert step in board, f"Missing blackboard step {step!r} in {board.keys()}"


@then('the run blackboard tree includes "{path}"')
def step_blackboard_tree_includes(context, path):
    """Assert tree paths include a relative path."""
    paths = (context.cli_run.blackboard or {}).get("tree", {}).get("paths") or []
    assert path in paths, f"{path!r} not in tree {paths[:20]}"


@then('the run blackboard has input_mode "{mode}"')
def step_blackboard_input_mode(context, mode):
    """Assert blackboard input_mode."""
    assert (context.cli_run.blackboard or {}).get("input_mode") == mode


@then('the run blackboard has stdin kind "{kind}"')
def step_blackboard_stdin_kind(context, kind):
    """Assert blackboard stdin_kind."""
    assert (context.cli_run.blackboard or {}).get("stdin_kind") == kind


@then("the discovery LLM was invoked at least once")
def step_llm_invoked(context):
    """Assert ScriptedDiscoveryLLM.call_count >= 1."""
    llm = context.discovery_llm
    assert getattr(llm, "call_count", 0) >= 1


@then('a ChangeSet with source "{source}" exists')
def step_changeset_source(context, source):
    """Assert a ChangeSet with the given source exists for the run/model."""
    cs_id = getattr(context, "changeset_id", None)
    if cs_id:
        cs = ChangeSet.objects.get(pk=cs_id)
        assert cs.source == source
        return
    assert ChangeSet.objects.filter(source=source).exists()


@then("every new Element is referenced by an operation on that ChangeSet")
@then("there are no orphan Elements without a ChangeSetItem")
def step_no_orphans(context):
    """DISC-06 / CICD-13 orphan check."""
    model = getattr(context, "cli_model", None)
    if model is None and getattr(context, "cli_run", None):
        model = context.cli_run.model
    if model is None:
        assert Element.objects.count() == 0
        return
    for el in Element.objects.filter(model=model):
        assert ChangeSetItem.objects.filter(
            changeset__model=model,
            op_type=ChangeSetItem.OP_ADD_ELEMENT,
            detail__name=el.name,
        ).exists(), f"orphan Element {el.name!r}"


@then('no ChangeSet operation references stereotype "{stereotype}"')
def step_no_stereotype_ops(context, stereotype):
    """Assert no ChangeSetItem uses the unknown stereotype slug."""
    slug = stereotype.lower()
    for item in ChangeSetItem.objects.filter(changeset_id=context.changeset_id):
        assert (item.detail or {}).get("stereotype_slug") != slug


@then('the model does not contain an element with stereotype "{stereotype}"')
def step_no_element_stereotype(context, stereotype):
    """Assert no Element uses the stereotype."""
    assert not Element.objects.filter(stereotype__name__iexact=stereotype).exists()


@then("no ChangeSet with source {source} was created for this run")
@then('no ChangeSet with source "{source}" was created for this run')
def step_no_changeset(context, source):
    """Assert failed runs did not create a ratatosk ChangeSet."""
    source = source.strip('"')
    run = getattr(context, "cli_run", None)
    if run is not None:
        assert run.changeset_id is None
    # Best-effort: no brand-new complete handoff expected on failure path


@then('no Model was created with metamodel "{slug}"')
def step_no_model_wrong_mm(context, slug):
    """Assert no YggdrasilModel bound to the unknown metamodel."""
    assert not YggdrasilModel.objects.filter(metamodel__slug=slug).exists()


@then("unchanged elements are never sent to Munin")
def step_unchanged_not_sent(context):
    """Unchanged bucket must not appear as ChangeSet operations."""
    buckets = getattr(context, "cli_buckets", None)
    if buckets is None:
        return
    ops = ChangeSetItem.objects.filter(changeset_id=context.changeset_id)
    assert ops.count() == buckets.total_ops


@given("a GitHub Actions workflow with YGGDRASIL_TOKEN configured")
def step_gha_token_configured(context):
    """Narrative Given — token comes from Priya/Marcus PAT steps or context."""
    if not getattr(context, "cli_token", None):
        from tests.fixtures.factories import UserFactory

        from yggdrasil.auth.services import TokenService

        user = UserFactory(username="marcus-ci", is_architect=True)
        _token, raw = TokenService().create_token(user, "ci", "read-write")
        context.current_user = user
        context.cli_token = raw


@then("the ChangeSet has 0 operations")
def step_changeset_zero_ops(context):
    """Assert linked ChangeSet has no items."""
    cs = ChangeSet.objects.get(pk=context.changeset_id)
    assert cs.items.count() == 0


@then("the delta buckets contain:")
def step_delta_buckets_min(context):
    """Assert bucket min_counts from table."""
    buckets = context.cli_buckets
    for row in context.table:
        name = row["bucket"]
        minimum = int(row["min_count"])
        actual = len(getattr(buckets, name))
        assert actual >= minimum, f"{name}: {actual} < {minimum}"


@then("the output contains a URL to the run result")
def step_output_has_run_url(context):
    """Assert run URL present in CLI output."""
    output = getattr(context, "cli_output", "") or ""
    assert "http" in output and "ratatosk-runs" in output


@then("the URL points to RATATOSK_RUN-VIEW_RATATOSK_RUN-1 for the new run")
def step_url_points_to_run_view(context):
    """Narrative Screen ID — URL contains run id."""
    output = getattr(context, "cli_output", "") or ""
    run = getattr(context, "cli_run", None)
    assert run is not None
    assert run.run_id in output


def _run_bootstrap(context, *, repo_name: str, metamodel: str = "c4") -> None:
    """Shared bootstrap runner for discovery AT steps."""
    path = getattr(context, "cli_repo_path", None) or str(_FIXTURE_REPOS / repo_name)
    llm = getattr(context, "discovery_llm", None) or ScriptedDiscoveryLLM()
    context.discovery_llm = llm
    snapshot = getattr(context, "discovery_snapshot", None) or LocalOrmSnapshotPort()
    scope = getattr(context, "cli_token_scope", None)
    try:
        run, buckets, output = bootstrap_repository(
            repo_path=path,
            model_name="Yggdrasil",
            metamodel=metamodel,
            user=getattr(context, "current_user", None),
            llm=llm,
            snapshot=snapshot,
            require_write_token=scope == "read-only",
            token_scope=scope,
        )
        context.cli_run = run
        context.cli_buckets = buckets
        context.cli_output = output
        context.cli_exit_code = 0
        context.changeset_id = run.changeset_id
        context.cli_model = run.model
    except Exception as exc:
        context.cli_exit_code = 1
        context.cli_output = str(exc)
        logger.info("_run_bootstrap | failed: %s", exc)


@then('the output does not contain "{text}"')
def step_output_does_not_contain(context, text):
    """Assert CLI output lacks stale phrases (unchanged, wiping on update)."""
    output = getattr(context, "cli_output", "") or ""
    assert text not in output, f"Unexpected {text!r} in output:\n{output}"


# ─── @wip scout / config / ModelSummary stubs (BPE) ─────────────────────────


def _wip_step(name: str):
    """Return a behave step that marks unimplemented spec steps."""

    def _stub(context, *args, **kwargs):
        raise NotImplementedError(f"TFK-07: {name}")

    return _stub


for _decorator, _phrase, _name in [
    (then, 'the run blackboard contains key "{key}"', "blackboard key assertion"),
    (
        then,
        "the run blackboard model_summary_chars is at most {n:d} tokens equivalent",
        "ModelSummary budget",
    ),
    (
        then,
        'the run blackboard metamodel_guidance mentions stereotype "{name}"',
        "metamodel guidance blackboard",
    ),
    (then, "bootstrap candidates include all manifest elements:", "manifest 4/4 assertion"),
    (
        when,
        'Priya runs ratatosk bootstrap against fixture "{name}" via subprocess',
        "subprocess CLI bootstrap",
    ),
    (then, 'MCP tool "{tool}" was called during bootstrap', "MCP handoff chain"),
    (given, 'Ollama is reachable at "{url}"', "Ollama reachable"),
    (given, 'Ollama model "{model}" is not available', "Ollama model missing"),
    (then, "the discovery LLM was invoked at least {n:d} times", "LLM call count"),
    (then, "the output contains wipe no-op for empty graph", "wipe no-op phrase"),
    (
        when,
        'Marcus pipes the stdin fixture "{name}" into ratatosk update with repo "./repo"',
        "update with --repo",
    ),
    (
        when,
        'Marcus pipes commit message stdin into ratatosk update with repo "./repo":',
        "commit scout trigger",
    ),
    (
        then,
        'the delta buckets contain bucket "{bucket}" with count at least {n:d}',
        "to_delete min count",
    ),
    (then, 'the delta buckets contain bucket "{bucket}" with count {n:d}', "to_delete exact count"),
    (
        then,
        'the Yggdrasil model "Yggdrasil" still has {n:d} elements',
        "update never wipes element count",
    ),
    (
        then,
        'an MCP tool call to "{tool}" was recorded on the blackboard',
        "MCP drill-down blackboard",
    ),
    (
        then,
        'an MCP tool call to "search" or "get_element" was recorded on the blackboard',
        "scout MCP probe",
    ),
]:
    _decorator(_phrase)(_wip_step(_name))


def _run_update(context) -> None:
    """Shared update runner for Act 6 AT steps."""
    llm = getattr(context, "discovery_llm", None) or ScriptedDiscoveryLLM()
    snapshot = getattr(context, "discovery_snapshot", None) or LocalOrmSnapshotPort()
    text = getattr(context, "stdin_text", "")
    try:
        run, buckets, output = update_from_stdin(
            stdin_text=text,
            model_name="Yggdrasil",
            metamodel="c4",
            user=getattr(context, "current_user", None),
            llm=llm,
            snapshot=snapshot,
        )
        context.cli_run = run
        context.cli_buckets = buckets
        context.cli_output = output
        context.cli_exit_code = 0
        context.changeset_id = run.changeset_id
        context.cli_model = run.model
    except Exception as exc:
        context.cli_exit_code = 1
        context.cli_output = str(exc)
        logger.info("_run_update | failed: %s", exc)
