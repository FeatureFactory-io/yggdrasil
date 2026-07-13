"""HTTP client for Yggdrasil REST API."""

from __future__ import annotations

import os
from typing import Any

import httpx


class YggdrasilClient:
    def __init__(self, base_url: str | None = None, token: str | None = None) -> None:
        self.base_url = (base_url or os.environ.get("YGGDRASIL_API_URL", "http://localhost:8000")).rstrip("/")
        self.token = token or os.environ.get("YGGDRASIL_API_TOKEN", "")
        self._client = httpx.Client(
            base_url=f"{self.base_url}/api/v1",
            headers={"Authorization": f"Token {self.token}"} if self.token else {},
            timeout=60.0,
        )

    def submit_changeset(
        self, run_id: str, items: list[dict[str, Any]], source: str = "ratatosk"
    ) -> dict:
        payload = {
            "run_id": run_id,
            "source": source,
            "items": items,
            "confidence_min": min((i.get("confidence", 1.0) for i in items), default=0.0),
            "confidence_max": max((i.get("confidence", 1.0) for i in items), default=1.0),
        }
        resp = self._client.post("/changesets/", json=payload)
        resp.raise_for_status()
        return resp.json()

    def close(self) -> None:
        self._client.close()
