"""Tests for ``manage.py mcp_server`` — real initialize_mcp, not mocked away."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from django.core.management import call_command

from yggdrasil.mcp import server as mcp_server_mod


@pytest.fixture(autouse=True)
def _reset_mcp_singleton():
    """Ensure each test gets a fresh FastMCP singleton."""
    mcp_server_mod._mcp_instance = None
    mcp_server_mod._initialized = False
    yield
    mcp_server_mod._mcp_instance = None
    mcp_server_mod._initialized = False


@pytest.mark.django_db
def test_initialize_mcp_registers_all_tools():
    """
    Real ``initialize_mcp()`` registers tools — catches **kwargs / schema errors.

    This is the failure Cursor hit when spawning mcp_server.
    """
    import asyncio

    mcp_server_mod.initialize_mcp()
    mcp = mcp_server_mod.get_mcp()
    tools = asyncio.run(mcp.list_tools())
    names = {t.name for t in tools}
    assert "list_elements" in names
    assert "list_relationships" in names
    assert "propose_changeset" in names
    assert "record_ratatosk_run" in names
    assert "create_element" in names
    assert "update_element" in names
    assert "list_packages" in names
    assert len(names) == 23


@pytest.mark.django_db
def test_mcp_server_stdio_command_calls_run_after_real_init():
    """
    ``mcp_server --transport stdio`` runs real initialize, then mcp.run.

    Only ``mcp.run`` is stubbed (blocks forever). initialize_mcp is real.
    """
    run_mock = MagicMock()

    def _get_mcp_stubbed():
        assert mcp_server_mod._initialized, "initialize_mcp must run before get_mcp"
        mcp = mcp_server_mod._mcp_instance
        assert mcp is not None
        mcp.run = run_mock  # type: ignore[method-assign]
        return mcp

    with (
        patch.object(mcp_server_mod, "redirect_print_to_stderr"),
        patch.object(mcp_server_mod, "get_mcp", side_effect=_get_mcp_stubbed),
    ):
        call_command("mcp_server", "--transport", "stdio")

    run_mock.assert_called_once_with(transport="stdio", show_banner=False, log_level="ERROR")


@pytest.mark.django_db
def test_mcp_server_invalid_token_exits(monkeypatch):
    """Invalid ``YGGDRASIL_TOKEN`` causes SystemExit(1) before run."""
    monkeypatch.setenv("YGGDRASIL_TOKEN", "definitely-invalid")
    with pytest.raises(SystemExit) as exc:
        call_command("mcp_server", "--transport", "stdio")
    assert exc.value.code == 1
