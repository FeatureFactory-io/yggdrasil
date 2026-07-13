"""Ratatosk CLI entrypoint."""

from __future__ import annotations

import json
import uuid

import click

from ratatosk.client import YggdrasilClient


@click.group()
def main() -> None:
    """Ratatosk — bootstrap and maintain the Yggdrasil graph."""


@main.command("scan-gitlab")
@click.option("--project", required=True, help="GitLab project path")
@click.option("--api-url", default=None, help="Yggdrasil API base URL")
def scan_gitlab(project: str, api_url: str | None) -> None:
    """Bootstrap connector: discover assets from GitLab (stub)."""
    run_id = f"gitlab-{uuid.uuid4().hex[:8]}"
    click.echo(f"Scanning GitLab project: {project}")
    # MVP stub: one discovered element
    items = [
        {
            "action": "create_element",
            "name": f"{project}-service",
            "stereotype_id": 1,
            "properties": {"repo": project},
            "confidence": 0.85,
        }
    ]
    client = YggdrasilClient(base_url=api_url)
    try:
        result = client.submit_changeset(run_id, items)
        click.echo(json.dumps(result, indent=2))
    finally:
        client.close()


if __name__ == "__main__":
    main()
