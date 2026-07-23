"""
LLM factory for Ratatosk discovery.

``LLM_PROVIDER=scripted`` (tests / AT) → :class:`ScriptedDiscoveryLLM`.
Otherwise → configured Ollama (or Anthropic) client. Never silently inject
hardcoded Payment API candidates outside the scripted provider.
"""

from __future__ import annotations

import json
import logging
import os

from yggdrasil.llm.base import LLMMessage, LLMResponse

logger = logging.getLogger("yggdrasil.ratatosk.llm_factory")

# Deterministic AT candidates — only used by ScriptedDiscoveryLLM explicitly.
_SCRIPTED_CANDIDATES = [
    {
        "name": "Payment API",
        "stereotype": "container",
        "package": "technology",
        "confidence": 0.95,
    },
    {
        "name": "Order Domain",
        "stereotype": "component",
        "package": "application",
        "confidence": 0.92,
    },
    {
        "name": "Mobile App",
        "stereotype": "system",
        "package": "context",
        "confidence": 0.9,
    },
    {
        "name": "Notification Service",
        "stereotype": "container",
        "package": "technology",
        "confidence": 0.88,
    },
    {
        "name": "Billing Worker",
        "stereotype": "container",
        "package": "technology",
        "confidence": 0.86,
    },
    {
        "name": "Legacy Batch",
        "stereotype": "container",
        "package": "technology",
        "confidence": 0.55,
    },
]


class ScriptedDiscoveryLLM:
    """
    Multi-turn scripted LLM for discovery tests and behave ATs.

    Responds with JSON project maps / candidate arrays based on prompt content.
    Call count is tracked for DISC-05 assertions.
    """

    model_id = "scripted-discovery"

    def __init__(
        self,
        *,
        responses: list[str] | None = None,
        empty_plan: bool = False,
        extra_candidate: dict | None = None,
    ) -> None:
        """
        :param responses: Optional fixed response queue (overrides smart replies).
        :param empty_plan: When True, always return empty JSON structures.
        :param extra_candidate: Appended to extract responses (e.g. unknown stereotype).
        """
        self._responses = list(responses) if responses is not None else None
        self._index = 0
        self._call_count = 0
        self._empty_plan = empty_plan
        self._extra_candidate = extra_candidate

    @property
    def call_count(self) -> int:
        """Number of ``complete`` invocations."""
        return self._call_count

    def complete(
        self,
        messages: list[LLMMessage],
        system: str = "",
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> LLMResponse:
        """Return the next scripted discovery response."""
        self._call_count += 1
        if self._responses is not None:
            if self._index >= len(self._responses):
                from yggdrasil.llm.base import LLMError

                raise LLMError(f"ScriptedDiscoveryLLM exhausted after {len(self._responses)} calls")
            content = self._responses[self._index]
            self._index += 1
            return LLMResponse(content=content, model=self.model_id)

        prompt = (messages[-1].content if messages else "").lower()
        content = self._smart_reply(prompt, system)
        logger.info(
            "ScriptedDiscoveryLLM.complete | call=%s kind=%s",
            self._call_count,
            "map" if "target" in prompt or "file tree" in prompt else "extract",
        )
        return LLMResponse(content=content, model=self.model_id)

    def _smart_reply(self, prompt: str, system: str) -> str:
        """Build JSON for map vs extract vs stdin prompts."""
        if self._empty_plan:
            if "file tree" in prompt or "target paths" in prompt or "project map" in prompt:
                return json.dumps({"project_kind": "unknown", "targets": []})
            return "[]"

        if "file tree" in prompt or "target paths" in prompt or "project kind" in prompt:
            return json.dumps(
                {
                    "project_kind": "python-web",
                    "targets": [
                        "docker-compose.yml",
                        "README.md",
                        "src/order_domain/service.py",
                        "src/payment_api/app.py",
                        "pyproject.toml",
                    ],
                }
            )

        candidates = list(_SCRIPTED_CANDIDATES)
        if "instruction" in prompt or "extra pass" in system.lower() or "domain" in prompt:
            candidates.append(
                {
                    "name": "Domain Logic Probe",
                    "stereotype": "component",
                    "package": "application",
                    "confidence": 0.84,
                }
            )
        if self._extra_candidate:
            candidates.append(dict(self._extra_candidate))
        if "noise" in prompt or "test_health" in prompt:
            return "[]"
        return json.dumps(candidates)


def build_discovery_llm(
    llm: object | None = None,
    *,
    empty_plan: bool = False,
    extra_candidate: dict | None = None,
) -> object:
    """
    Resolve the LLM client for a discovery run.

    :param llm: Explicit injection (tests). When set, returned as-is.
    :param empty_plan: Scripted empty-plan mode (DISC-14).
    :param extra_candidate: Extra candidate for scripted extract (DISC-04).
    :return: LLM client implementing ``complete``.
    """
    if llm is not None:
        return llm
    provider = os.environ.get("LLM_PROVIDER", "").strip().lower()
    if not provider:
        try:
            from django.conf import settings

            provider = str(getattr(settings, "LLM_PROVIDER", "ollama")).lower()
        except Exception:
            provider = "ollama"

    if provider == "scripted" or empty_plan or extra_candidate is not None:
        logger.info("build_discovery_llm | provider=scripted empty_plan=%s", empty_plan)
        return ScriptedDiscoveryLLM(empty_plan=empty_plan, extra_candidate=extra_candidate)

    logger.info("build_discovery_llm | provider=%s", provider)
    if provider == "anthropic":
        from yggdrasil.llm.adapters.anthropic import AnthropicClient

        return AnthropicClient()
    from yggdrasil.llm.adapters.ollama import OllamaClient

    return OllamaClient()
