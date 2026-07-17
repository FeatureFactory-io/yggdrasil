"""
Munin agentic planner: conversational AI that reads + writes the graph (SAO.md §17.6).

Assembly profile: Conversational Planner (SAO.md §17.2).
Modules active: LLM Port, Prompt Stack (Foundation+Rules+Context+Instructions),
Tool Surface, Agent Loop, Plan & Steps, Agent Blackboard, Chat Streaming.

Munin is called from:
  1. GUI chat panel (HTMX POST to /chat/munin/)
  2. MCP ask_munin tool (headless via FastMCP server)
  3. do_other_changeset (re-plan a rejected operation)

All writes produced by Munin go through ChangeSetService.propose()
— never directly to ORM (SAO.md §1 — all writes through ChangeSet pipeline).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from yggdrasil.llm.base import BaseLLM

logger = logging.getLogger("yggdrasil.munin.agent")


@dataclass
class MuninResponse:
    """
    Structured response from a single Munin conversation turn.

    :Example:

    >>> resp = MuninResponse(
    ...     text="payments-team owns Payment API",
    ...     cited_elements=[{"id": 1, "name": "Payment API"}],
    ...     navigation_url="/elements/payment-api",
    ... )
    """

    text: str
    cited_elements: list[dict] = field(default_factory=list)
    navigation_url: str | None = None
    changeset_id: int | None = None
    tool_calls: list[dict] = field(default_factory=list)


class MuninAgent:
    """
    Munin conversational planner: answers questions and proposes graph changes.

    :Example:

    >>> agent = MuninAgent(llm=scripted_llm, model_id=1, user_id=42)
    >>> resp = agent.chat("Who owns Payment API?", history=[])
    >>> resp.text
    'payments-team'
    """

    CONFIDENCE_HIGH_THRESHOLD = 0.85

    def __init__(
        self,
        llm: BaseLLM,
        model_id: int,
        user_id: int | None = None,
    ) -> None:
        """
        :param llm: LLM client. ScriptedLLM for tests; OllamaClient for desktop.
        :param model_id: YggdrasilModel PK to scope queries. Example: 1
        :param user_id: Authenticated user PK for HITL gates. Example: 42
        """
        self._llm = llm
        self._model_id = model_id
        self._user_id = user_id
        logger.info(
            "MuninAgent: initialised | model_id=%s user_id=%s llm=%s",
            model_id,
            user_id,
            llm.model_id,
        )

    def chat(
        self,
        message: str,
        history: list[dict],
        instructions: str = "",
    ) -> MuninResponse:
        """
        Process a single conversational turn and return a structured response.

        Runs the full agentic loop: plan → tool calls → synthesise → respond.
        Write operations are always routed through ChangeSetService.propose().

        :param message: User's natural-language input. Example: "Who owns Payment API?"
        :param history: Prior conversation turns (list of {role, content} dicts).
        :param instructions: Optional extra instructions (e.g. from do_other).
        :return: MuninResponse with text, cited elements, navigation URL.
        :raises LLMError: If the LLM call fails.
        """
        raise NotImplementedError()

    def replan_operation(
        self,
        rejected_item_id: int,
        instructions: str,
    ) -> MuninResponse:
        """
        Re-plan a rejected ChangeSetItem with human instructions as extra context.

        Called by ChangeSetService.do_other(). Produces a new ChangeSet with
        corrected operations.

        :param rejected_item_id: ChangeSetItem PK to re-plan. Example: 3
        :param instructions: Human guidance. Example: "it's an external system"
        :return: MuninResponse with changeset_id of the replacement ChangeSet.
        :raises ValueError: If item not found.
        """
        raise NotImplementedError()

    # ── Private helpers ───────────────────────────────────────────────────────

    def _build_system_prompt(self, rules: list[str]) -> str:
        """Assemble Prompt Stack layers: Foundation + Rules + Context."""
        raise NotImplementedError()

    def _run_agent_loop(
        self,
        system: str,
        messages: list[dict],
        max_steps: int = 10,
    ) -> tuple[str, list[dict]]:
        """
        Execute the Plan & Steps loop until no more tool calls are needed.

        Returns (final_text, all_tool_calls_executed).
        """
        raise NotImplementedError()

    def _dispatch_tool(self, tool_name: str, tool_args: dict) -> dict:
        """Route a tool call to the appropriate service method."""
        raise NotImplementedError()

    def _parse_tool_calls(self, llm_text: str) -> list[dict]:
        """Extract structured tool call requests from LLM output."""
        raise NotImplementedError()

    def _synthesise_response(
        self,
        tool_results: list[dict],
        user_message: str,
    ) -> MuninResponse:
        """Build a structured MuninResponse from tool results and the LLM answer."""
        raise NotImplementedError()
