"""Scripted discovery LLM for CLI tests (no Django / yggdrasil imports)."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass

logger = logging.getLogger("ratatosk.discovery.scripted_llm")

_PREVIEW_CHARS = 1200


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
        user_content = messages[-1].content if messages else ""
        logger.info(
            "ScriptedDiscoveryLLM.complete | entry call=%s empty_plan=%s user_chars=%s",
            self._call_count,
            self._empty_plan,
            len(user_content),
        )
        if system:
            logger.info(
                "ScriptedDiscoveryLLM.complete | request.system preview=%s",
                self._preview(system),
            )
        logger.info(
            "ScriptedDiscoveryLLM.complete | request.user preview=%s",
            self._preview(user_content),
        )
        prompt = user_content.lower()
        if self._empty_plan:
            if "file tree" in prompt or "target paths" in prompt:
                response = LLMResponse(content='{"project_kind":"unknown","targets":[]}')
                branch = "empty_plan_project_map"
            else:
                response = LLMResponse(content="[]")
                branch = "empty_plan_extract"
        elif "file tree" in prompt or "target paths" in prompt or "project kind" in prompt:
            response = LLMResponse(
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
            branch = "project_map"
        elif "noise" in prompt or "test_health" in prompt:
            response = LLMResponse(content="[]")
            branch = "empty_noise"
        else:
            response = LLMResponse(content=json.dumps(_SCRIPTED_CANDIDATES))
            branch = "extract_candidates"
        logger.info(
            "ScriptedDiscoveryLLM.complete | result call=%s branch=%s chars=%s preview=%s",
            self._call_count,
            branch,
            len(response.content),
            self._preview(response.content),
        )
        return response

    @staticmethod
    def _preview(text: str, limit: int = _PREVIEW_CHARS) -> str:
        collapsed = text.replace("\n", "\\n")
        if len(collapsed) <= limit:
            return collapsed
        return f"{collapsed[:limit]}…({len(text)} chars total)"
