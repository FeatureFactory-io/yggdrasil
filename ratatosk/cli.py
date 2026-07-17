"""
Ratatosk CLI entry point.

Usage:
    ratatosk bootstrap <path> --token=<token> --model Yggdrasil [--metamodel=c4]
"""

from __future__ import annotations

import os
import sys

import click


@click.group()
@click.version_option(package_name="ratatosk")
def main() -> None:
    """Ratatosk — Yggdrasil field agent CLI."""


@main.command()
@click.argument("path", type=click.Path(exists=True))
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
    help="Yggdrasil server URL.",
)
@click.option("--model", "model_name", required=True, help="Target model name/slug.")
@click.option("--metamodel", default="c4", show_default=True, help="Metamodel profile.")
@click.option("--instructions", default="", help="Extra analysis instructions for Munin.")
def bootstrap(
    path: str,
    token: str | None,
    server: str,
    model_name: str,
    metamodel: str,
    instructions: str,
) -> None:
    """
    Scan PATH and push discovered architecture elements to the graph.

    :param path: Local filesystem path to the repository root.
    :param token: Personal access token for authenticating with the server.
    :param server: Base URL of the Yggdrasil API server.
    :param model_name: Target Yggdrasil model name.
    :param metamodel: Metamodel profile (default c4).
    :param instructions: Optional extra pass instructions.
    """
    if not token:
        click.echo("Error: Missing option '--token'. A Yggdrasil token is required.", err=True)
        sys.exit(2)
    # Local/desktop AT path: drive Django ORM bootstrap in-process.
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "yggdrasil.settings")
    import django

    django.setup()
    from yggdrasil.ratatosk.agent import bootstrap_repository

    _run, _buckets, output = bootstrap_repository(
        repo_path=path,
        model_name=model_name,
        metamodel=metamodel,
        instructions=instructions,
    )
    click.echo(output)
    click.echo(f"[ratatosk] server={server}")
