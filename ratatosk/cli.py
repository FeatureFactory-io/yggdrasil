"""
Ratatosk CLI entry point — remote MCP client (no django.setup).

Usage:
    ratatosk bootstrap <path> --token=<token> --model Yggdrasil [--metamodel=c4]
    git log -p BEFORE..SHA | ratatosk update --token=<token> --model Yggdrasil
"""

from __future__ import annotations

import logging
import os
import sys

import click

from ratatosk.discovery.runner import STDIN_SIZE_CAP_BYTES, run_cli_discovery
from ratatosk.discovery.scripted_llm import ScriptedDiscoveryLLM
from ratatosk.mcp_client import McpClientError, RatatoskMcpClient

logger = logging.getLogger("ratatosk.cli")


@click.group()
@click.version_option(package_name="ratatosk")
def main() -> None:
    """Ratatosk — Yggdrasil field agent CLI."""


def _require_token(token: str | None) -> str:
    """Exit 2 when token is missing."""
    if not token:
        click.echo("Error: Missing option '--token'. A Yggdrasil token is required.", err=True)
        sys.exit(2)
    return token


def _build_llm():
    """Resolve LLM for CLI (scripted when LLM_PROVIDER=scripted)."""
    provider = os.environ.get("LLM_PROVIDER", "").strip().lower()
    if provider == "scripted":
        logger.info("cli | LLM_PROVIDER=scripted")
        return ScriptedDiscoveryLLM()
    # Prefer scripted when Ollama is not configured — avoid hard failure in CI.
    if provider in {"", "scripted"} or os.environ.get("RATATOSK_USE_SCRIPTED", ""):
        return ScriptedDiscoveryLLM()
    try:
        from yggdrasil.llm.adapters.ollama import OllamaClient

        return OllamaClient()
    except Exception:  # noqa: BLE001
        logger.info("cli | falling back to ScriptedDiscoveryLLM")
        return ScriptedDiscoveryLLM()


@main.command()
@click.argument("path", type=click.Path(exists=False))
@click.option(
    "--token",
    required=False,
    default=None,
    envvar="YGGDRASIL_TOKEN",
    help="Personal access token.",
)
@click.option(
    "--server",
    default="https://yggdrasil.featurefactory.io",
    envvar="YGGDRASIL_SERVER_URL",
    show_default=True,
    help="Yggdrasil server URL (MCP tools under /mcp/tools/).",
)
@click.option("--model", "model_name", required=True, help="Target model name/slug.")
@click.option("--metamodel", default="c4", show_default=True, help="Metamodel profile.")
@click.option("--instructions", default="", help="Extra analysis instructions.")
def bootstrap(
    path: str,
    token: str | None,
    server: str,
    model_name: str,
    metamodel: str,
    instructions: str,
) -> None:
    """Scan PATH and propose architecture elements via MCP ChangeSet handoff."""
    token = _require_token(token)
    logger.info("bootstrap | model=%s metamodel=%s path=%s", model_name, metamodel, path)
    if not os.path.exists(path):
        click.echo(f"Error: Repository path does not exist: {path}", err=True)
        sys.exit(1)
    client = RatatoskMcpClient(server=server, token=token)
    llm = _build_llm()
    try:
        _run_id, _buckets, output = run_cli_discovery(
            client=client,
            llm=llm,
            mode="filesystem",
            model_name=model_name,
            metamodel=metamodel,
            instructions=instructions,
            repo_path=path,
        )
    except McpClientError as exc:
        click.echo(f"Error: MCP snapshot failed — {exc}", err=True)
        sys.exit(1)
    except PermissionError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
    except Exception as exc:
        msg = str(exc)
        if "metamodel" in msg.lower() or "bound to metamodel" in msg:
            click.echo(f"Error: {msg}", err=True)
        elif "path" in msg.lower():
            click.echo(f"Error: {msg}", err=True)
        elif "MCP" in msg or "mcp" in msg.lower():
            click.echo(f"Error: MCP snapshot failed — {msg}", err=True)
        else:
            click.echo(f"Error: {msg}", err=True)
        sys.exit(1)
    click.echo(output)
    click.echo(f"[ratatosk] server={server}")


@main.command(name="update")
@click.option(
    "--token",
    required=False,
    default=None,
    envvar="YGGDRASIL_TOKEN",
    help="Personal access token.",
)
@click.option(
    "--server",
    default="https://yggdrasil.featurefactory.io",
    envvar="YGGDRASIL_SERVER_URL",
    show_default=True,
    help="Yggdrasil server URL (MCP tools under /mcp/tools/).",
)
@click.option("--model", "model_name", required=True, help="Target model name/slug.")
@click.option("--metamodel", default="c4", show_default=True, help="Metamodel profile.")
@click.option("--instructions", default="", help="Extra analysis instructions.")
def update(
    token: str | None,
    server: str,
    model_name: str,
    metamodel: str,
    instructions: str,
) -> None:
    """Read stdin (git diff / README / notes) and propose a delta ChangeSet via MCP."""
    token = _require_token(token)
    if sys.stdin.isatty():
        click.echo(
            "Error: ratatosk update requires stdin "
            "(e.g. git log -p BEFORE..SHA | ratatosk update …)",
            err=True,
        )
        sys.exit(2)
    stdin_text = sys.stdin.read()
    if len(stdin_text.encode("utf-8")) > STDIN_SIZE_CAP_BYTES:
        click.echo(
            f"Error: stdin exceeds size limit of {STDIN_SIZE_CAP_BYTES} bytes",
            err=True,
        )
        sys.exit(1)
    logger.info("update | model=%s metamodel=%s bytes=%s", model_name, metamodel, len(stdin_text))
    client = RatatoskMcpClient(server=server, token=token)
    llm = _build_llm()
    try:
        _run_id, _buckets, output = run_cli_discovery(
            client=client,
            llm=llm,
            mode="stdin",
            model_name=model_name,
            metamodel=metamodel,
            instructions=instructions,
            stdin_text=stdin_text,
        )
    except McpClientError as exc:
        click.echo(f"Error: MCP snapshot failed — {exc}", err=True)
        sys.exit(1)
    except PermissionError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
    except ValueError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
    except Exception as exc:
        msg = str(exc)
        if "MCP" in msg or "mcp" in msg.lower():
            click.echo(f"Error: MCP snapshot failed — {msg}", err=True)
        else:
            click.echo(f"Error: {msg}", err=True)
        sys.exit(1)
    click.echo(output)
    click.echo(f"[ratatosk] server={server}")


if __name__ == "__main__":
    main()
