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
import os
import re
import tempfile
from pathlib import Path

import yaml
from behave import given, then, when  # type: ignore[import]
from tests.fixtures.factories import UserFactory
from tests.fixtures.factories.model_factories import (
    EdgeStereotypeFactory,
    ElementFactory,
    PackageFactory,
    RelationshipFactory,
    StereotypeFactory,
)

from yggdrasil.auth.services import TokenService
from yggdrasil.changeset.models import ChangeSet, ChangeSetItem
from yggdrasil.changeset.services import ChangeSetService
from yggdrasil.graph.models import (
    Element,
    Metamodel,
    Package,
    Stereotype,
    YggdrasilModel,
    ensure_c4_metamodel,
)
from yggdrasil.ratatosk.agent import (
    DEFAULT_CONFIDENCE_THRESHOLD,
    DeltaBuckets,
    bootstrap_repository,
    handoff_buckets_to_munin,
)

logger = logging.getLogger("yggdrasil.at.cli_steps")

_token_service = TokenService()
_changeset_service = ChangeSetService()


# ─── Given steps ────────────────────────────────────────────────────────────


@given("Priya has a Yggdrasil personal access token with read-write scope")
def step_priya_has_pat(context):
    """Create or reuse a PAT for Priya in the test context."""
    user = UserFactory(username="priya", is_architect=True)
    token, raw = _token_service.create_token(user, "ratatosk-at", "read-write")
    context.current_user = user
    context.cli_token = raw
    context.cli_token_obj = token
    logger.info("step_priya_has_pat | user=%s token_pk=%s", user.pk, token.pk)


@given('the Yggdrasil model "Yggdrasil" exists with no elements')
def step_empty_model(context):
    """Create an empty YggdrasilModel in the test DB."""
    model, _ = YggdrasilModel.objects.get_or_create(
        slug="yggdrasil",
        defaults={"name": "Yggdrasil", "metamodel": ensure_c4_metamodel()},
    )
    Element.objects.filter(model=model).delete()
    context.cli_model = model
    logger.info("step_empty_model | model_id=%s", model.pk)


@given(
    'the Yggdrasil model "Yggdrasil" exists with {elem_count:d} elements '
    "and {rel_count:d} relationships"
)
def step_model_with_elements_rels(context, elem_count, rel_count):
    """Create a model with the specified element and relationship counts."""
    model, _ = YggdrasilModel.objects.get_or_create(
        slug="yggdrasil",
        defaults={"name": "Yggdrasil", "metamodel": ensure_c4_metamodel()},
    )
    Element.objects.filter(model=model).delete()
    st = StereotypeFactory(
        metamodel=model.metamodel, name="Container", slug="container", is_edge=False
    )
    pkg = PackageFactory(metamodel=model.metamodel, name="Technology", slug="technology")
    elements = []
    for idx in range(elem_count):
        elements.append(
            ElementFactory(
                model=model,
                name=f"Element {idx}",
                slug=f"element-{idx}",
                stereotype=st,
                package=pkg,
            )
        )
    edge = EdgeStereotypeFactory(metamodel=model.metamodel, name="depends_on", slug="depends_on")
    for idx in range(rel_count):
        source = elements[idx % len(elements)]
        target = elements[(idx + 1) % len(elements)]
        RelationshipFactory(model=model, source=source, target=target, stereotype=edge)
    context.cli_model = model
    logger.info(
        "step_model_with_elements_rels | model_id=%s elems=%s rels=%s",
        model.pk,
        elem_count,
        rel_count,
    )


@given("Priya has run a bootstrap with new candidates discovered")
def step_bootstrap_ran(context):
    """Set up a completed bootstrap run in the test context."""
    user = getattr(context, "current_user", None) or UserFactory(
        username="priya", is_architect=True
    )
    context.current_user = user
    repo = _ensure_temp_repo(context)
    run, buckets, output = bootstrap_repository(
        repo_path=repo,
        model_name="Yggdrasil",
        metamodel="c4",
        user=user,
    )
    context.cli_run = run
    context.cli_buckets = buckets
    context.cli_output = output
    context.cli_exit_code = 0
    context.changeset_id = run.changeset_id
    logger.info("step_bootstrap_ran | run_id=%s", run.run_id)


@given("Ratatosk has produced delta buckets:")
def step_ratatosk_delta_buckets(context):
    """Set up delta bucket data from the table in context."""
    model, _ = YggdrasilModel.objects.get_or_create(
        slug="yggdrasil",
        defaults={"name": "Yggdrasil", "metamodel": ensure_c4_metamodel()},
    )
    context.cli_model = model
    context.current_user = getattr(context, "current_user", None) or UserFactory(
        username="priya", is_architect=True
    )
    counts = {row["bucket"]: int(row["count"]) for row in context.table}
    st = StereotypeFactory(
        metamodel=model.metamodel, name="Container", slug="container", is_edge=False
    )
    pkg = PackageFactory(metamodel=model.metamodel, name="Technology", slug="technology")
    to_update = []
    for idx in range(counts.get("to_update", 0)):
        element = ElementFactory(
            model=model,
            name=f"Update Me {idx}",
            slug=f"update-me-{idx}",
            stereotype=st,
            package=pkg,
            owner="old-team",
        )
        to_update.append(
            {
                "name": element.name,
                "element_id": element.pk,
                "confidence": 0.9,
                "fields": {"owner": ["old-team", "new-team"]},
            }
        )
    to_delete = []
    for idx in range(counts.get("to_delete", 0)):
        element = ElementFactory(
            model=model,
            name=f"Delete Me {idx}",
            slug=f"delete-me-{idx}",
            stereotype=st,
            package=pkg,
        )
        to_delete.append(
            {
                "name": element.name,
                "element_id": element.pk,
                "confidence": 0.7,
            }
        )
    to_add = [
        {
            "name": f"New Service {idx}",
            "stereotype": "Container",
            "package": "Technology",
            "confidence": 0.91,
        }
        for idx in range(counts.get("to_add", 0))
    ]
    unchanged = [
        {"name": f"Stable {idx}", "confidence": 1.0} for idx in range(counts.get("unchanged", 0))
    ]
    buckets = DeltaBuckets(
        to_add=to_add,
        to_update=to_update,
        to_delete=to_delete,
        unchanged=unchanged,
    )
    changeset = handoff_buckets_to_munin(
        buckets, model=model, user=context.current_user, run_id="cli-04-handoff"
    )
    context.cli_buckets = buckets
    context.changeset_id = changeset.pk
    context.mcp_changeset = changeset
    logger.info(
        "step_ratatosk_delta_buckets | ops=%s cs=%s",
        changeset.items.count(),
        changeset.pk,
    )


@given(
    "a ChangeSet with {total:d} operations where {below_threshold:d} "
    "are below confidence threshold"
)
def step_changeset_with_threshold(context, total, below_threshold):
    """Create a ChangeSet with the specified confidence distribution."""
    model, _ = YggdrasilModel.objects.get_or_create(
        slug="yggdrasil",
        defaults={"name": "Yggdrasil", "metamodel": ensure_c4_metamodel()},
    )
    context.cli_model = model
    user = getattr(context, "current_user", None) or UserFactory(
        username="priya", is_architect=True
    )
    context.current_user = user
    above = total - below_threshold
    operations = []
    for idx in range(above):
        operations.append(
            {
                "op_type": ChangeSetItem.OP_ADD_ELEMENT,
                "detail": {
                    "name": f"High Conf {idx}",
                    "stereotype_slug": "container",
                    "package_slug": "technology",
                },
                "confidence": 0.9,
            }
        )
    for idx in range(below_threshold):
        operations.append(
            {
                "op_type": ChangeSetItem.OP_ADD_ELEMENT,
                "detail": {
                    "name": f"Low Conf {idx}",
                    "stereotype_slug": "container",
                    "package_slug": "technology",
                },
                "confidence": 0.5,
            }
        )
    changeset = _changeset_service.propose(
        model_id=model.pk,
        source=ChangeSet.SOURCE_RATATOSK,
        operations=operations,
        munin_reasoning="CLI-05 threshold fixture",
        run_id="cli-05",
        review_mode=ChangeSet.REVIEW_MANUAL,
        user=user,
    )
    auto_ids = [
        item.pk
        for item in changeset.items.all()
        if float(item.confidence) >= DEFAULT_CONFIDENCE_THRESHOLD
    ]
    changeset = _changeset_service.approve(changeset_id=changeset.pk, item_ids=auto_ids, user=user)
    context.changeset_id = changeset.pk
    context.cli_output = (
        f"auto-applied {len(auto_ids)}\n"
        f"below threshold: {below_threshold} operations queued for review\n"
        f"ChangeSet #{changeset.pk}"
    )
    context.cli_exit_code = 0
    logger.info(
        "step_changeset_with_threshold | cs=%s auto=%s below=%s",
        changeset.pk,
        len(auto_ids),
        below_threshold,
    )


@given('the Metamodel "{slug}" exists with C4 stereotypes and packages')
def step_metamodel_exists_with_c4(context, slug):
    """Ensure a Metamodel catalog exists (C4 seed for slug=c4)."""
    if slug == "c4":
        mm = ensure_c4_metamodel()
    else:
        mm, _ = Metamodel.objects.get_or_create(slug=slug, defaults={"name": slug.upper()})
    context.cli_metamodel = mm
    logger.info("step_metamodel_exists_with_c4 | slug=%s id=%s", slug, mm.pk)


@given("a successful bootstrap run on a Python web application repository")
def step_successful_bootstrap(context):
    """Set up a completed bootstrap run guided by the C4 Metamodel."""
    ensure_c4_metamodel()
    user = getattr(context, "current_user", None) or UserFactory(
        username="priya", is_architect=True
    )
    context.current_user = user
    repo = _ensure_temp_repo(context)
    run, _buckets, output = bootstrap_repository(
        repo_path=repo,
        model_name="Yggdrasil",
        metamodel="c4",
        user=user,
    )
    context.cli_run = run
    context.cli_model = run.model
    context.cli_output = output
    context.cli_exit_code = 0
    context.changeset_id = run.changeset_id
    logger.info("step_successful_bootstrap | run_id=%s", run.run_id)


@then('the model\'s metamodel is "{slug}"')
def step_model_metamodel_is(context, slug):
    """Assert the Model is bound to the given Metamodel slug."""
    model = getattr(context, "cli_model", None) or YggdrasilModel.objects.get(slug="yggdrasil")
    assert (
        model.metamodel.slug == slug
    ), f"Expected metamodel {slug!r}, got {model.metamodel.slug!r}"


# ─── When steps ─────────────────────────────────────────────────────────────


@when("Priya runs:")
def step_priya_runs_cli(context):
    """Run the ratatosk CLI command from context.text (docstring)."""
    command = (context.text or "").strip()
    context.cli_command = command
    logger.info("step_priya_runs_cli | command=%r", command[:200])
    if "bootstrap" not in command:
        context.cli_exit_code = 2
        context.cli_output = "unknown command"
        return
    token = _extract_token(command, context)
    if not token:
        context.cli_exit_code = 2
        context.cli_output = "Error: Missing option '--token'. A Yggdrasil token is required."
        return
    model_name = _extract_option(command, "model") or "Yggdrasil"
    metamodel = _extract_option(command, "metamodel") or "c4"
    instructions = _extract_instructions(command)
    repo = _extract_repo_path(command, context)
    user = getattr(context, "current_user", None)
    try:
        run, buckets, output = bootstrap_repository(
            repo_path=repo,
            model_name=model_name,
            metamodel=metamodel,
            instructions=instructions,
            user=user,
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
        logger.info("step_priya_runs_cli | failed: %s", exc)


# ─── Then steps ─────────────────────────────────────────────────────────────


@then("the exit code is 0")
def step_exit_code_zero(context):
    """Assert the CLI exited with code 0."""
    assert (
        context.cli_exit_code == 0
    ), f"Expected exit 0, got {context.cli_exit_code}: {getattr(context, 'cli_output', '')}"


@then("the exit code is not 0")
def step_exit_code_nonzero(context):
    """Assert the CLI exited with a non-zero code."""
    assert context.cli_exit_code != 0, "Expected non-zero exit code"


@then('the output contains "{text}"')
def step_output_contains(context, text):
    """Assert the CLI stdout contains the expected text."""
    output = getattr(context, "cli_output", "") or ""
    assert text in output, f"Expected {text!r} in output:\n{output}"


@then("a link to the run result is printed")
def step_link_printed(context):
    """Assert a URL to the run detail page is in the output."""
    output = getattr(context, "cli_output", "") or ""
    assert "http" in output and "ratatosk-runs" in output, f"No run link in:\n{output}"


@then("Munin produces ChangeSet with {count:d} planned operations")
def step_munin_produces_n_ops(context, count):
    """Assert the resulting ChangeSet has N operations."""
    cs = ChangeSet.objects.get(pk=context.changeset_id)
    assert cs.items.count() == count, f"Expected {count} ops, got {cs.items.count()}"


@given("Ratatosk has produced bootstrap buckets:")
def step_ratatosk_bootstrap_buckets_cli(context):
    """@wip — bootstrap add-heavy bucket fixture."""
    raise NotImplementedError("TFK-07: bootstrap wipe + add-heavy buckets")


@then("Munin produces ChangeSet with at least {count:d} planned operations")
def step_munin_at_least_n_ops_cli(context, count):
    """@wip — Munin relationship planning from element candidates."""
    raise NotImplementedError("TFK-07: Munin plans relationships from bootstrap candidates")


@then('the ChangeSet summary contains "{text}"')
def step_changeset_summary_contains(context, text):
    """Assert the ChangeSet's munin_reasoning contains the text."""
    cs = ChangeSet.objects.get(pk=context.changeset_id)
    assert text in (cs.munin_reasoning or ""), f"Expected {text!r} in {cs.munin_reasoning!r}"


@then("{auto_count:d} operations are auto-applied to the model")
def step_auto_applied_count(context, auto_count):
    """Assert N operations were auto-applied."""
    accepted = ChangeSetItem.objects.filter(
        changeset_id=context.changeset_id,
        status=ChangeSetItem.ITEM_STATUS_ACCEPTED,
    ).count()
    assert accepted == auto_count, f"Expected {auto_count} accepted, got {accepted}"


@then("{queued_count:d} operations are queued for review in the ChangeSet")
def step_queued_count(context, queued_count):
    """Assert N operations are still pending in the ChangeSet."""
    pending = ChangeSetItem.objects.filter(
        changeset_id=context.changeset_id,
        status=ChangeSetItem.ITEM_STATUS_PENDING,
    ).count()
    assert pending == queued_count, f"Expected {queued_count} pending, got {pending}"


@then("the model contains elements with stereotypes from:")
def step_model_has_stereotypes(context):
    """Assert the Model's Metamodel defines the stereotypes (and/or elements use them)."""
    model = getattr(context, "cli_model", None) or YggdrasilModel.objects.get(slug="yggdrasil")
    for row in context.table:
        name = row["stereotype"]
        assert Stereotype.objects.filter(metamodel=model.metamodel, name__iexact=name).exists() or (
            Element.objects.filter(model=model, stereotype__name__iexact=name).exists()
        ), f"Missing stereotype {name!r} on metamodel {model.metamodel.slug!r}"


@then("the model contains packages from:")
@then("the model's metamodel contains packages from:")
def step_model_has_packages(context):
    """Assert the Model's Metamodel defines the packages from the table."""
    model = getattr(context, "cli_model", None) or YggdrasilModel.objects.get(slug="yggdrasil")
    for row in context.table:
        name = row["package"]
        assert Package.objects.filter(
            metamodel=model.metamodel, name__iexact=name
        ).exists(), f"Missing package {name!r} on metamodel {model.metamodel.slug!r}"


# ─── Helpers ────────────────────────────────────────────────────────────────


def _ensure_temp_repo(context) -> str:
    """Create a temporary repo directory for bootstrap AT."""
    if getattr(context, "cli_repo_path", None):
        return context.cli_repo_path
    tmp = tempfile.mkdtemp(prefix="ratatosk-repo-")
    Path(tmp, "README.md").write_text("# sample repo\n", encoding="utf-8")
    context.cli_repo_path = tmp
    return tmp


def _extract_token(command: str, context) -> str | None:
    """Extract --token=... or $YGGDRASIL_TOKEN from the command / context."""
    match = re.search(r"--token=(\S+)", command)
    if match:
        raw = match.group(1)
        if raw in {"$YGGDRASIL_TOKEN", "${YGGDRASIL_TOKEN}"}:
            return getattr(context, "cli_token", None)
        return raw
    if "--token" not in command and "YGGDRASIL_TOKEN" not in command:
        return None
    return getattr(context, "cli_token", None)


def _extract_option(command: str, name: str) -> str | None:
    """Extract --name=value or --name value from the command string."""
    match = re.search(rf"--{name}=(\S+)", command)
    if match:
        return match.group(1)
    match = re.search(rf"--{name}\s+(\S+)", command)
    if match:
        return match.group(1)
    return None


def _extract_instructions(command: str) -> str:
    """Extract --instructions \"...\" from the command string."""
    match = re.search(r'--instructions\s+"([^"]+)"', command, re.DOTALL)
    if match:
        return match.group(1)
    match = re.search(r"--instructions\s+'([^']+)'", command, re.DOTALL)
    if match:
        return match.group(1)
    return ""


def _extract_repo_path(command: str, context) -> str:
    """Extract the repository path argument after bootstrap."""
    if getattr(context, "cli_repo_path", None):
        return context.cli_repo_path
    match = re.search(r"bootstrap\s+(\S+)", command)
    if match:
        path = match.group(1)
        if path.startswith("./") or path == "./repo":
            return _ensure_temp_repo(context)
        return path
    return _ensure_temp_repo(context)


# ─── @wip config / env stubs (TFK-07) ───────────────────────────────────────


@given('the environment variable "{name}" is set to "{value}"')
def step_env_var_set(context, name, value):
    """Bootstrap env for CLI-09 / CFG-*."""
    if not hasattr(context, "env_overrides"):
        context.env_overrides = {}
    context.env_overrides[name] = value
    logger.info("step_env_var_set | %s=%s", name, value)


@when('Priya runs ratatosk bootstrap with flag "{flag}"')
def step_bootstrap_with_flag(context, flag):
    """CFG-02 CLI flag override — stored for config loader."""
    context.cli_flags = getattr(context, "cli_flags", {})
    if "=" in flag:
        key, val = flag.split("=", 1)
        context.cli_flags[key.lstrip("-")] = val
    else:
        context.cli_flags[flag.lstrip("-")] = True
    logger.info("step_bootstrap_with_flag | flag=%s", flag)


@when("Ratatosk loads configuration for bootstrap")
def step_load_config_bootstrap(context):
    """CFG-06..09 config loader."""
    from ratatosk.config import load_bootstrap_config

    env = {**dict(os.environ), **getattr(context, "env_overrides", {})}
    for key in getattr(context, "env_unset", set()):
        env.pop(key, None)
    flags = getattr(context, "cli_flags", {})
    context.bootstrap_config = load_bootstrap_config(
        env=env,
        repo_path=getattr(context, "cli_repo_path", ""),
        flags=flags,
    )
    logger.info(
        "step_load_config_bootstrap | llm_provider=%s",
        context.bootstrap_config.llm_provider,
    )


@then('the effective config key "{key}" is {value}')
def step_effective_config_key(context, key, value):
    """CFG effective config assertion."""
    config = getattr(context, "bootstrap_config", None)
    assert config is not None, "load configuration step must run first"
    actual = getattr(config, key, None)
    assert str(actual) == value.strip('"'), f"{key}: expected {value!r}, got {actual!r}"


@given('a repo config file "ratatosk.yaml" with model_summary_token_budget {n:d}')
def step_repo_config_budget(context, n):
    """CFG-02 repo config fixture — stub for future ratatosk.yaml merge."""
    context.repo_config_budget = n
    logger.info("step_repo_config_budget | budget=%s", n)


def _repo_yaml_bucket(context) -> dict[str, dict[str, str]]:
    if not hasattr(context, "repo_yaml_data"):
        context.repo_yaml_data = {}
    return context.repo_yaml_data


def _project_root() -> Path:
    return Path(__file__).resolve().parents[3]


@given('a repo config file "{path}" with llm_provider "{value}"')
def step_repo_config_llm_provider(context, path, value):
    """CFG-12/13: accumulate repo YAML llm_provider."""
    bucket = _repo_yaml_bucket(context)
    bucket.setdefault(path, {})["llm_provider"] = value
    logger.info("step_repo_config_llm_provider | path=%s value=%s", path, value)


@given('a repo config file "{path}" with base_model "{value}"')
def step_repo_config_base_model(context, path, value):
    """CFG-12: accumulate repo YAML base_model."""
    bucket = _repo_yaml_bucket(context)
    bucket.setdefault(path, {})["base_model"] = value
    logger.info("step_repo_config_base_model | path=%s value=%s", path, value)


def _write_repo_yaml_files(context) -> None:
    root = _project_root()
    for rel_path, data in _repo_yaml_bucket(context).items():
        target = root / rel_path.strip("./")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
        logger.info("step_write_repo_yaml | path=%s keys=%s", target, list(data))


@when('Ratatosk loads configuration for bootstrap with repo "{path}"')
def step_load_config_bootstrap_with_repo(context, path):
    """CFG-12/13: load config with repo YAML merge."""
    from ratatosk.config import load_bootstrap_config

    _write_repo_yaml_files(context)
    env = {**dict(os.environ), **getattr(context, "env_overrides", {})}
    for key in getattr(context, "env_unset", set()):
        env.pop(key, None)
    flags = getattr(context, "cli_flags", {})
    repo = str(_project_root() / path.strip("./"))
    context.cli_repo_path = repo
    context.bootstrap_config = load_bootstrap_config(
        env=env,
        repo_path=repo,
        flags=flags,
    )
    logger.info(
        "step_load_config_bootstrap_with_repo | repo=%s llm_provider=%s",
        repo,
        context.bootstrap_config.llm_provider,
    )


@then('the effective config key "resolved_model" is "{value}"')
def step_effective_config_resolved_model_is(context, value):
    """CFG-11/12: exact resolved_model assertion."""
    config = getattr(context, "bootstrap_config", None)
    assert config is not None, "load configuration step must run first"
    actual = getattr(config, "resolved_model", None)
    assert str(actual) == value, f"resolved_model: expected {value!r}, got {actual!r}"


@then('the effective config key "resolved_model" contains "{substring}"')
def step_effective_config_resolved_model_contains(context, substring):
    """CFG-11: substring match on resolved_model."""
    config = getattr(context, "bootstrap_config", None)
    assert config is not None, "load configuration step must run first"
    actual = getattr(config, "resolved_model", None)
    assert actual is not None, "resolved_model not set on BootstrapConfig"
    assert substring in str(actual), f"resolved_model {actual!r} missing {substring!r}"


@given('the environment variable "ANTHROPIC_API_KEY" is set')
def step_anthropic_api_key_set(context):
    """LLM-05: require real ANTHROPIC_API_KEY in environment for manual cert."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise AssertionError(
            "ANTHROPIC_API_KEY must be set in environment for @anthropic scenarios"
        )
    if not hasattr(context, "env_overrides"):
        context.env_overrides = {}
    context.env_overrides["ANTHROPIC_API_KEY"] = os.environ["ANTHROPIC_API_KEY"]
    logger.info("step_anthropic_api_key_set | using env ANTHROPIC_API_KEY")


@given('the environment variable "ANTHROPIC_API_KEY" is not set')
def step_anthropic_api_key_not_set(context):
    """LLM-06: ensure API key absent from effective env."""
    if not hasattr(context, "env_unset"):
        context.env_unset = set()
    context.env_unset.add("ANTHROPIC_API_KEY")
    if hasattr(context, "env_overrides"):
        context.env_overrides.pop("ANTHROPIC_API_KEY", None)
    logger.info("step_anthropic_api_key_not_set | ANTHROPIC_API_KEY excluded")
