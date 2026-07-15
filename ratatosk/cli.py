"""
Ratatosk CLI entry point.

Usage:
    ratatosk bootstrap <path> --token=<token> [--server=<url>]
"""
from __future__ import annotations

import click


@click.group()
@click.version_option(package_name="ratatosk")
def main() -> None:
    """Ratatosk — Yggdrasil field agent CLI."""


@main.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--token", required=True, envvar="YGGDRASIL_TOKEN", help="Personal access token.")
@click.option(
    "--server",
    default="https://yggdrasil.featurefactory.io",
    envvar="YGGDRASIL_SERVER_URL",
    show_default=True,
    help="Yggdrasil server URL.",
)
def bootstrap(path: str, token: str, server: str) -> None:
    """
    Scan PATH and push discovered architecture elements to the graph.

    :param path: Local filesystem path to the repository root.
    :param token: Personal access token for authenticating with the server.
    :param server: Base URL of the Yggdrasil API server.
    """
    click.echo(f"[ratatosk] bootstrap {path!r} → {server}  (placeholder)")
