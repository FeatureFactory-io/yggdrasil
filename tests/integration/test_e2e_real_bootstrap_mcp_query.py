"""
Sprint E2E — real subprocess bootstrap + MCP query (local-only).

Uses pytest-django ``live_server`` so the HTTP MCP bridge is available without
a manually running ``make run``.

Manual certification (optional)::

    export YGGDRASIL_E2E=1
    export LLM_PROVIDER=anthropic
    export BASE_MODEL=haiku
    # ANTHROPIC_API_KEY from .env (auto-loaded) or export explicitly
    uv run pytest tests/integration/test_e2e_real_bootstrap_mcp_query.py -m e2e_real -s
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
from django.contrib.auth import get_user_model

from yggdrasil.auth.services import TokenService
from yggdrasil.graph.models import ensure_c4_metamodel

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "repos" / "sample_webapp"
MANIFEST_NAMES = {
    "Payment API",
    "Order Service",
    "Order Domain",
    "Billing Worker",
}


def _load_local_env() -> None:
    """Load repo ``.env`` into os.environ without overriding existing vars."""
    env_path = PROJECT_ROOT / ".env"
    if not env_path.is_file():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        key = key.strip()
        if not key:
            continue
        parsed = value.strip().strip('"').strip("'")
        existing = os.environ.get(key)
        if existing is None or not existing.strip():
            os.environ[key] = parsed


def _require_llm_credentials(provider: str) -> None:
    """Skip early when the selected real LLM provider lacks credentials."""
    if provider == "anthropic" and not os.getenv("ANTHROPIC_API_KEY"):
        pytest.skip(
            "LLM_PROVIDER=anthropic requires ANTHROPIC_API_KEY "
            "(export it or add to .env at repo root)"
        )
    if provider == "openai" and not os.getenv("OPENAI_API_KEY"):
        pytest.skip(
            "LLM_PROVIDER=openai requires OPENAI_API_KEY " "(export it or add to .env at repo root)"
        )


@pytest.fixture
def e2e_token(db):
    """Create a read-write PAT for live_server bootstrap."""
    user_model = get_user_model()
    user, _ = user_model.objects.get_or_create(
        username="e2e-bootstrap",
        defaults={"is_staff": True, "is_superuser": True},
    )
    _token, raw = TokenService().create_token(user, "e2e-cert", "read-write")
    return raw


@pytest.mark.e2e_real
@pytest.mark.django_db(transaction=True)
def test_real_bootstrap_sample_webapp_then_mcp_query(live_server, e2e_token) -> None:
    """Subprocess bootstrap against live_server + MCP list_elements query."""
    if not os.getenv("YGGDRASIL_E2E"):
        pytest.skip("Set YGGDRASIL_E2E=1 to run real bootstrap E2E")

    _load_local_env()
    provider = os.getenv("LLM_PROVIDER", "scripted")
    _require_llm_credentials(provider)

    ensure_c4_metamodel()
    server = live_server.url.rstrip("/")
    env = {
        **os.environ,
        "LLM_PROVIDER": provider,
        "YGGDRASIL_SERVER_URL": server,
        "YGGDRASIL_TOKEN": e2e_token,
        "RATATOSK_LOG_LEVEL": "INFO",
    }
    cmd = [
        sys.executable,
        "-m",
        "ratatosk.cli",
        "bootstrap",
        str(FIXTURE),
        f"--token={e2e_token}",
        "--model",
        "Yggdrasil",
        "--metamodel=c4",
        f"--server={server}",
    ]
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
    )
    combined_lines: list[str] = []
    assert proc.stdout is not None
    for line in proc.stdout:
        combined_lines.append(line)
        sys.stdout.write(line)
        sys.stdout.flush()
    returncode = proc.wait(timeout=600)
    combined = "".join(combined_lines)
    assert returncode == 0, combined
    assert "building ModelSummary" in combined
    assert "run complete" in combined
    assert "ChangeSet #" in combined
    assert "wipe no-op for empty graph" in combined

    import httpx

    response = httpx.post(
        f"{server}/mcp/tools/list_elements",
        json={"arguments": {"model": "yggdrasil", "limit": 50, "offset": 0}},
        headers={"Authorization": f"Bearer {e2e_token}"},
        timeout=30.0,
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    result = payload.get("result") or payload
    names = {item["name"] for item in result.get("items") or []}
    for manifest_name in MANIFEST_NAMES:
        assert manifest_name in names, f"missing {manifest_name!r}; got {names}"

    traverse_resp = httpx.post(
        f"{server}/mcp/tools/traverse",
        json={
            "arguments": {
                "from_": "Payment API",
                "direction": "incoming",
                "model": "yggdrasil",
            }
        },
        headers={"Authorization": f"Bearer {e2e_token}"},
        timeout=30.0,
    )
    assert traverse_resp.status_code == 200, traverse_resp.text
    traverse_result = traverse_resp.json().get("result") or traverse_resp.json()
    assert len(traverse_result.get("edges") or []) >= 1
