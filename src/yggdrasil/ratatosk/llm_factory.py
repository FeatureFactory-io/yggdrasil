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

# Deterministic AT candidates — aligned with sample_webapp expected_elements.yaml.
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
        endpoint_noise: bool = False,
        readme_only_c4: bool = False,
    ) -> None:
        """
        :param responses: Optional fixed response queue (overrides smart replies).
        :param empty_plan: When True, always return empty JSON structures.
        :param extra_candidate: Appended to extract responses (e.g. unknown stereotype).
        :param endpoint_noise: When True, inject endpoint-level noise unless README-only.
        :param readme_only_c4: When True, never inject endpoint-level candidates.
        """
        self._responses = list(responses) if responses is not None else None
        self._index = 0
        self._call_count = 0
        self._empty_plan = empty_plan
        self._extra_candidate = extra_candidate
        self._endpoint_noise = endpoint_noise
        self._readme_only_c4 = readme_only_c4

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
        if self._extra_candidate:
            candidates.append(dict(self._extra_candidate))
        if (
            self._endpoint_noise
            and not self._readme_only_c4
            and not self._prompt_requests_readme_only(prompt)
        ):
            candidates.append(
                {
                    "name": "Liveness probe",
                    "stereotype": "component",
                    "package": "application",
                    "confidence": 0.88,
                }
            )
        if "noise" in prompt or "test_health" in prompt:
            return "[]"
        return json.dumps(candidates)

    @staticmethod
    def _prompt_requests_readme_only(prompt: str) -> bool:
        """True when operator instructions steer toward README-only C4 extraction."""
        lowered = prompt.lower()
        return (
            "readme" in lowered
            and "c4" in lowered
            and ("ignore endpoint" in lowered or "only c4" in lowered)
        )


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
    from ratatosk.config import build_extract_llm_from_config, load_bootstrap_config

    config = load_bootstrap_config(env=os.environ)
    return build_extract_llm_from_config(config)


def build_planning_discovery_llm(llm: object | None = None) -> object:
    """
    Resolve planning-tier LLM for project map steps.

    :param llm: Explicit injection (tests). When set, returned as-is.
    :return: LLM client implementing ``complete``.
    """
    if llm is not None:
        return llm
    provider = os.environ.get("LLM_PROVIDER", "").strip().lower()
    if provider == "scripted" or not provider:
        return build_discovery_llm()
    from ratatosk.config import build_planning_llm_from_config, load_bootstrap_config

    config = load_bootstrap_config(env=os.environ)
    return build_planning_llm_from_config(config)
