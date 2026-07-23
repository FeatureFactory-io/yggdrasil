"""Click-layer CLI tests — no django.setup on production path."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from ratatosk.cli import main

FIXTURE = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "repos" / "sample_webapp"


def test_cli_bootstrap_missing_token() -> None:
    """DISC-07 / CLI-06: missing token → non-zero, output contains token."""
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["bootstrap", str(FIXTURE), "--model", "Yggdrasil", "--metamodel=c4"],
        env={**os.environ, "YGGDRASIL_TOKEN": ""},
    )
    assert result.exit_code != 0
    assert "token" in (result.output + result.stderr).lower()


def test_cli_bootstrap_missing_path() -> None:
    """DISC-11: missing path → non-zero, output contains path."""
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "bootstrap",
            "/tmp/yggdrasil-no-such-repo-xyz",
            "--token=fake",
            "--model",
            "Yggdrasil",
        ],
    )
    assert result.exit_code != 0
    assert "path" in (result.output + result.stderr).lower()


def test_cli_update_missing_token() -> None:
    """CICD-11: update without token fails like bootstrap."""
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["update", "--model", "Yggdrasil"],
        input="diff --git a/x b/x\n",
        env={**os.environ, "YGGDRASIL_TOKEN": ""},
    )
    assert result.exit_code != 0
    assert "token" in (result.output + result.stderr).lower()


def test_cli_bootstrap_no_django_setup() -> None:
    """Production bootstrap must not call django.setup."""
    runner = CliRunner()
    fake_client = MagicMock()
    fake_client.call_tool.side_effect = lambda name, args=None: {
        "ensure_model": {"slug": "yggdrasil", "metamodel": "c4", "created": False},
        "list_elements": {"items": [], "total": 0},
        "list_relationships": {"items": [], "total": 0},
        "list_stereotypes": {
            "items": [
                {"name": "Container", "slug": "container", "is_edge": False},
                {"name": "Component", "slug": "component", "is_edge": False},
            ]
        },
        "propose_changeset": {
            "changeset_id": 42,
            "status": "pending",
            "applied_count": 1,
            "pending_count": 0,
            "operations_count": 1,
            "run_url": "https://yggdrasil.local/ratatosk-runs/run-x",
        },
        "record_ratatosk_run": {"run_id": "run-x", "changeset_id": 42, "status": "complete"},
    }.get(name, {})

    with (
        patch("ratatosk.cli.RatatoskMcpClient", return_value=fake_client),
        patch("django.setup") as django_setup,
        patch.dict(os.environ, {"LLM_PROVIDER": "scripted", "YGGDRASIL_TOKEN": "t"}),
    ):
        result = runner.invoke(
            main,
            [
                "bootstrap",
                str(FIXTURE),
                "--token=t",
                "--model",
                "Yggdrasil",
                "--metamodel=c4",
            ],
        )
    assert django_setup.call_count == 0
    assert result.exit_code == 0, result.output + result.stderr
    assert "building ModelSummary" in result.output
    assert "ChangeSet #42" in result.output
    tools_called = [c.args[0] for c in fake_client.call_tool.call_args_list]
    assert "list_elements" in tools_called
    assert "propose_changeset" in tools_called
