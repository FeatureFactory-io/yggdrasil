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
from logging.handlers import RotatingFileHandler
from pathlib import Path

import click

from ratatosk.discovery.exclude import merge_bootstrap_exclude_patterns, normalize_exclude_patterns
from ratatosk.config import (
    build_extract_llm_from_config,
    build_planning_llm_from_config,
    load_bootstrap_config,
)
from ratatosk.discovery.runner import STDIN_SIZE_CAP_BYTES, run_cli_discovery
from ratatosk.mcp_client import McpClientError, RatatoskMcpClient

logger = logging.getLogger("ratatosk.cli")


def _configure_cli_logging() -> None:
    """Configure stderr + rotating file logging once at CLI entry."""
    level_name = os.environ.get("RATATOSK_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    log_file = os.environ.get("RATATOSK_LOG_FILE", "logs/ratatosk.log")

    root = logging.getLogger()
    if root.handlers:
        root.setLevel(level)
        return

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(level)
    stderr_handler.setFormatter(formatter)
    root.addHandler(stderr_handler)

    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    if log_path.exists():
        log_path.write_text("", encoding="utf-8")
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=5_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)
    root.setLevel(level)
    logger.info(
        "_configure_cli_logging | level=%s file=%s reason=cli_entry",
        level_name,
        log_path.resolve(),
    )


@click.group()
@click.version_option(package_name="ratatosk")
def main() -> None:
    """Ratatosk — Yggdrasil field agent CLI."""
    _configure_cli_logging()


def _require_token(token: str | None) -> str:
    """Exit 2 when token is missing."""
    if not token:
        click.echo("Error: Missing option '--token'. A Yggdrasil token is required.", err=True)
        sys.exit(2)
    return token


def _build_llm(config=None):
    """Resolve field-tier extract LLM for CLI from BootstrapConfig."""
    if config is None:
        config = load_bootstrap_config()
    return build_extract_llm_from_config(config)


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
@click.option(
    "--exclude",
    "exclude",
    multiple=True,
    help="Path prefix or glob to skip (repeatable or comma-separated).",
)
def bootstrap(
    path: str,
    token: str | None,
    server: str,
    model_name: str,
    metamodel: str,
    instructions: str,
    exclude: tuple[str, ...],
) -> None:
    """Scan PATH and propose architecture elements via MCP ChangeSet handoff."""
    token = _require_token(token)
    exclude_csv = ",".join(exclude)
    config = load_bootstrap_config(
        flags={
            "server": server,
            "metamodel": metamodel,
            "exclude": exclude_csv,
            "instructions": instructions,
        },
        repo_path=path,
    )
    effective_instructions = instructions.strip() or config.instructions
    operator_exclude = normalize_exclude_patterns(exclude_csv) or config.exclude_patterns
    effective_exclude = merge_bootstrap_exclude_patterns(operator_exclude)
    logger.info(
        "bootstrap | config llm_provider=%s resolved_model=%s planning_model=%s "
        "max_extract_targets=%s server=%s",
        config.llm_provider,
        config.resolved_model,
        config.resolved_planning_model,
        config.max_extract_targets,
        config.yggdrasil_server_url,
    )
    logger.info("bootstrap | model=%s metamodel=%s path=%s", model_name, metamodel, path)
    if not os.path.exists(path):
        click.echo(f"Error: Repository path does not exist: {path}", err=True)
        sys.exit(1)
    client = RatatoskMcpClient(server=server, token=token)
    planning_llm = build_planning_llm_from_config(config)
    extract_llm = build_extract_llm_from_config(config)
    try:
        _run_id, _buckets, output = run_cli_discovery(
            client=client,
            llm=extract_llm,
            planning_llm=planning_llm,
            extract_llm=extract_llm,
            discovery_limits=config.discovery_limits,
            mode="filesystem",
            model_name=model_name,
            metamodel=metamodel,
            instructions=effective_instructions,
            repo_path=path,
            exclude_patterns=effective_exclude,
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
    config = load_bootstrap_config(flags={"server": server, "metamodel": metamodel})
    logger.info(
        "update | config llm_provider=%s resolved_model=%s",
        config.llm_provider,
        config.resolved_model,
    )
    client = RatatoskMcpClient(server=server, token=token)
    planning_llm = build_planning_llm_from_config(config)
    extract_llm = build_extract_llm_from_config(config)
    try:
        _run_id, _buckets, output = run_cli_discovery(
            client=client,
            llm=extract_llm,
            planning_llm=planning_llm,
            extract_llm=extract_llm,
            discovery_limits=config.discovery_limits,
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
