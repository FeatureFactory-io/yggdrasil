"""Scripted discovery LLM for CLI tests (no Django / yggdrasil imports)."""

from __future__ import annotations

import json
from dataclasses import dataclass


@dataclass
class LLMMessage:
    """Minimal message shape compatible with discovery prompts."""

    role: str
    content: str


@dataclass
class LLMResponse:
    """Minimal response shape."""

    content: str
    model: str = "scripted-discovery"


_SCRIPTED_CANDIDATES = [
    {
        "name": "Payment API",
        "stereotype": "container",
        "package": "technology",
        "confidence": 0.95,
    },
    {
        "name": "Order Service",
        "stereotype": "container",
        "package": "technology",
        "confidence": 0.93,
    },
    {
        "name": "Order Domain",
        "stereotype": "component",
        "package": "application",
        "confidence": 0.92,
    },
    {
        "name": "Billing Worker",
        "stereotype": "component",
        "package": "application",
        "confidence": 0.90,
    },
]


class ScriptedDiscoveryLLM:
    """Multi-turn scripted LLM for offline CLI / AT discovery."""

    model_id = "scripted-discovery"

    def __init__(self, *, empty_plan: bool = False) -> None:
        self._empty_plan = empty_plan
        self._call_count = 0

    @property
    def call_count(self) -> int:
        return self._call_count

    def complete(
        self,
        messages: list[LLMMessage],
        system: str = "",
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> LLMResponse:
        self._call_count += 1
        prompt = (messages[-1].content if messages else "").lower()
        if self._empty_plan:
            if "file tree" in prompt or "target paths" in prompt:
                return LLMResponse(content='{"project_kind":"unknown","targets":[]}')
            return LLMResponse(content="[]")
        if "file tree" in prompt or "target paths" in prompt or "project kind" in prompt:
            return LLMResponse(
                content=json.dumps(
                    {
                        "project_kind": "python-web",
                        "targets": [
                            "docker-compose.yml",
                            "README.md",
                            "src/order_service/app.py",
                            "src/order_domain/service.py",
                            "src/payment_api/app.py",
                            "src/billing_worker/worker.py",
                        ],
                    }
                )
            )
        if "noise" in prompt or "test_health" in prompt:
            return LLMResponse(content="[]")
        return LLMResponse(content=json.dumps(_SCRIPTED_CANDIDATES))
