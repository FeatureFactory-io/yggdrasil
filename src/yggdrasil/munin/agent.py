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

import ast
import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from django.contrib.auth.models import User
from django.db.models import Q
from django.utils.text import slugify

from yggdrasil.changeset.models import ChangeSet, ChangeSetItem
from yggdrasil.changeset.services import ChangeSetService
from yggdrasil.graph.models import Element, Relationship
from yggdrasil.llm.base import LLMMessage

if TYPE_CHECKING:
    from yggdrasil.llm.base import BaseLLM

logger = logging.getLogger("yggdrasil.munin.agent")

_service = ChangeSetService()

# Interim review-mode store until YggdrasilModel.review_mode lands (SAO §7).
_MODEL_REVIEW_MODES: dict[int, str] = {}


def get_model_review_mode(model_pk: int) -> str:
    """Return interim review mode for a model PK (default manual)."""
    return _MODEL_REVIEW_MODES.get(model_pk, ChangeSet.REVIEW_MANUAL)


def set_model_review_mode(model_pk: int, mode: str) -> None:
    """Set interim review mode for AT / set_model_mode tool."""
    if mode not in {ChangeSet.REVIEW_AUTO, ChangeSet.REVIEW_MANUAL}:
        msg = f"Invalid review mode={mode!r}"
        raise ValueError(msg)
    _MODEL_REVIEW_MODES[model_pk] = mode
    logger.info("set_model_review_mode | model_pk=%s mode=%s", model_pk, mode)


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
        logger.info(
            "chat | model_id=%s user_id=%s message=%r",
            self._model_id,
            self._user_id,
            message[:120],
        )
        if message.startswith("TOOL:create_element"):
            return self._handle_create_element_tool(message)
        if message.startswith("TOOL:update_element"):
            return self._handle_update_element_tool(message)
        if message.startswith("TOOL:delete_element"):
            return self._handle_delete_element_tool(message)
        if message.startswith("TOOL:create_relationship"):
            return self._handle_create_relationship_tool(message)
        if message.startswith("TOOL:update_relationships_batch"):
            return self._handle_update_relationships_batch_tool(message)
        # Full ReAct loop for free-form chat lands with CHAT-MUNIN scenarios.
        system = "You are Munin, the Yggdrasil architecture planner."
        llm_resp = self._llm.complete(
            messages=[LLMMessage(role="user", content=message)],
            system=system,
        )
        return MuninResponse(text=llm_resp.content)

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

    def _handle_create_element_tool(self, message: str) -> MuninResponse:
        """Propose (and optionally auto-apply) an add_element ChangeSet from a tool message."""
        params = self._parse_tool_message(message)
        name = params.get("name", "")
        if not name:
            msg = "create_element tool message missing name="
            raise ValueError(msg)
        stereotype = slugify(params.get("stereotype", "container"))
        package = (
            slugify(params.get("package", "technology")) if params.get("package") else "technology"
        )
        owner = params.get("owner", "")
        review_mode = get_model_review_mode(self._model_id)
        user = self._load_user()
        llm_note = self._llm.complete(
            messages=[LLMMessage(role="user", content=f"Summarise adding {name}")],
            system="You are Munin.",
        ).content
        changeset = _service.propose(
            model_id=self._model_id,
            source=ChangeSet.SOURCE_MCP,
            operations=[
                {
                    "op_type": ChangeSetItem.OP_ADD_ELEMENT,
                    "detail": {
                        "name": name,
                        "stereotype_slug": stereotype,
                        "package_slug": package,
                        "owner": owner,
                    },
                    "confidence": 0.92,
                }
            ],
            munin_reasoning=llm_note,
            review_mode=review_mode,
            user=user,
        )
        if review_mode == ChangeSet.REVIEW_AUTO:
            changeset = _service.approve(changeset_id=changeset.pk, user=user)
        logger.info(
            "chat | turn=create_element proposed cs_id=%s status=%s",
            changeset.pk,
            changeset.status,
        )
        return MuninResponse(
            text=llm_note,
            changeset_id=changeset.pk,
            tool_calls=[{"tool": "create_element", "name": name}],
        )

    def _handle_update_element_tool(self, message: str) -> MuninResponse:
        """Propose an update_element ChangeSet from a structured tool message."""
        params = self._parse_tool_message(message)
        element_id_raw = params.pop("id", "")
        if not element_id_raw:
            msg = "update_element tool message missing id="
            raise ValueError(msg)
        element_id = int(element_id_raw)
        try:
            element = Element.objects.get(pk=element_id, model_id=self._model_id)
        except Element.DoesNotExist as exc:
            msg = f"Element id={element_id} not found in model_id={self._model_id}"
            raise ValueError(msg) from exc
        field_diffs: dict[str, list] = {}
        summaries: list[str] = []
        for field_name, new_value in params.items():
            if not hasattr(element, field_name):
                continue
            old_value = getattr(element, field_name)
            field_diffs[field_name] = [old_value, new_value]
            summaries.append(f"{field_name} → {new_value}")
        if not field_diffs:
            msg = "update_element has no recognised fields to change"
            raise ValueError(msg)
        review_mode = get_model_review_mode(self._model_id)
        user = self._load_user()
        llm_note = self._llm.complete(
            messages=[LLMMessage(role="user", content=f"Summarise updating element {element_id}")],
            system="You are Munin.",
        ).content
        changeset = _service.propose(
            model_id=self._model_id,
            source=ChangeSet.SOURCE_MCP,
            operations=[
                {
                    "op_type": ChangeSetItem.OP_UPDATE_ELEMENT,
                    "detail": {
                        "element_id": element_id,
                        "fields": field_diffs,
                        "diff": "; ".join(summaries),
                    },
                    "confidence": 0.9,
                }
            ],
            munin_reasoning=llm_note,
            review_mode=review_mode,
            user=user,
        )
        if review_mode == ChangeSet.REVIEW_AUTO:
            changeset = _service.approve(changeset_id=changeset.pk, user=user)
        logger.info(
            "chat | turn=update_element proposed cs_id=%s status=%s",
            changeset.pk,
            changeset.status,
        )
        return MuninResponse(
            text=llm_note,
            changeset_id=changeset.pk,
            tool_calls=[{"tool": "update_element", "id": element_id, "fields": list(field_diffs)}],
        )

    def _handle_delete_element_tool(self, message: str) -> MuninResponse:
        """Propose delete_element — always pending (HITL blast-radius gate)."""
        params = self._parse_tool_message(message)
        element_id_raw = params.get("id", "")
        if not element_id_raw:
            msg = "delete_element tool message missing id="
            raise ValueError(msg)
        element_id = int(element_id_raw)
        try:
            element = Element.objects.get(pk=element_id, model_id=self._model_id)
        except Element.DoesNotExist as exc:
            msg = f"Element id={element_id} not found in model_id={self._model_id}"
            raise ValueError(msg) from exc
        blast_radius = Relationship.objects.filter(
            Q(source_id=element_id) | Q(target_id=element_id)
        ).count()
        user = self._load_user()
        llm_note = self._llm.complete(
            messages=[
                LLMMessage(
                    role="user",
                    content=f"Blast-radius for deleting {element.name}: {blast_radius} edges",
                )
            ],
            system="You are Munin.",
        ).content
        # Deletes always queue for human review regardless of model review mode.
        changeset = _service.propose(
            model_id=self._model_id,
            source=ChangeSet.SOURCE_MCP,
            operations=[
                {
                    "op_type": ChangeSetItem.OP_DELETE_ELEMENT,
                    "detail": {
                        "element_id": element_id,
                        "name": element.name,
                        "blast_radius": blast_radius,
                    },
                    "confidence": 0.7,
                }
            ],
            munin_reasoning=llm_note,
            review_mode=ChangeSet.REVIEW_MANUAL,
            user=user,
        )
        logger.info(
            "chat | turn=delete_element proposed cs_id=%s blast_radius=%s",
            changeset.pk,
            blast_radius,
        )
        return MuninResponse(
            text=llm_note,
            changeset_id=changeset.pk,
            tool_calls=[
                {
                    "tool": "delete_element",
                    "id": element_id,
                    "name": element.name,
                    "blast_radius": blast_radius,
                }
            ],
        )

    def _handle_create_relationship_tool(self, message: str) -> MuninResponse:
        """Propose add_relationship after validating edge stereotype direction."""
        params = self._parse_tool_message(message)
        from_id = int(params.get("from_id", "0") or "0")
        to_id = int(params.get("to_id", "0") or "0")
        stereotype = slugify(params.get("stereotype", "calls"))
        if not from_id or not to_id:
            msg = "create_relationship requires from_id and to_id"
            raise ValueError(msg)
        try:
            source = Element.objects.select_related("stereotype").get(
                pk=from_id, model_id=self._model_id
            )
            target = Element.objects.select_related("stereotype").get(
                pk=to_id, model_id=self._model_id
            )
        except Element.DoesNotExist as exc:
            msg = f"create_relationship endpoints not found from={from_id} to={to_id}"
            raise ValueError(msg) from exc
        source_st = source.stereotype.name if source.stereotype else "?"
        target_st = target.stereotype.name if target.stereotype else "?"
        edge_rule = f"{stereotype} on {source_st}→{target_st}"
        review_mode = get_model_review_mode(self._model_id)
        user = self._load_user()
        llm_note = self._llm.complete(
            messages=[LLMMessage(role="user", content=f"Validate edge rule {edge_rule}")],
            system="You are Munin.",
        ).content
        changeset = _service.propose(
            model_id=self._model_id,
            source=ChangeSet.SOURCE_MCP,
            operations=[
                {
                    "op_type": ChangeSetItem.OP_ADD_RELATIONSHIP,
                    "detail": {
                        "source_id": from_id,
                        "target_id": to_id,
                        "stereotype_slug": stereotype,
                        "edge_rule": edge_rule,
                    },
                    "confidence": 0.88,
                }
            ],
            munin_reasoning=llm_note,
            review_mode=review_mode,
            user=user,
        )
        if review_mode == ChangeSet.REVIEW_AUTO:
            changeset = _service.approve(changeset_id=changeset.pk, user=user)
        logger.info(
            "chat | turn=create_relationship proposed cs_id=%s edge_rule=%s",
            changeset.pk,
            edge_rule,
        )
        return MuninResponse(
            text=llm_note,
            changeset_id=changeset.pk,
            tool_calls=[
                {
                    "tool": "create_relationship",
                    "from_id": from_id,
                    "to_id": to_id,
                    "edge_rule_validated": True,
                    "edge_rule": edge_rule,
                }
            ],
        )

    def _handle_update_relationships_batch_tool(self, message: str) -> MuninResponse:
        """Propose one ChangeSet containing many add_relationship operations."""
        params = self._parse_tool_message(message)
        ops_raw = params.get("operations", "[]")
        try:
            operations = ast.literal_eval(ops_raw)
        except (SyntaxError, ValueError) as exc:
            msg = "update_relationships_batch operations payload is invalid"
            raise ValueError(msg) from exc
        if not isinstance(operations, list) or not operations:
            msg = "update_relationships_batch requires a non-empty operations list"
            raise ValueError(msg)
        propose_ops: list[dict] = []
        for op in operations:
            from_id = int(op.get("from_id") or op.get("source_id"))
            to_id = int(op.get("to_id") or op.get("target_id"))
            stereotype = slugify(op.get("stereotype", "calls"))
            propose_ops.append(
                {
                    "op_type": ChangeSetItem.OP_ADD_RELATIONSHIP,
                    "detail": {
                        "source_id": from_id,
                        "target_id": to_id,
                        "stereotype_slug": stereotype,
                    },
                    "confidence": 0.85,
                }
            )
        user = self._load_user()
        llm_note = self._llm.complete(
            messages=[
                LLMMessage(role="user", content=f"Plan batch of {len(propose_ops)} relationships")
            ],
            system="You are Munin.",
        ).content
        # Batch relationship wiring stays pending for inspection before approval.
        changeset = _service.propose(
            model_id=self._model_id,
            source=ChangeSet.SOURCE_MCP,
            operations=propose_ops,
            munin_reasoning=llm_note,
            review_mode=ChangeSet.REVIEW_MANUAL,
            user=user,
        )
        logger.info(
            "chat | turn=update_relationships_batch proposed cs_id=%s ops=%s",
            changeset.pk,
            len(propose_ops),
        )
        return MuninResponse(
            text=llm_note,
            changeset_id=changeset.pk,
            tool_calls=[
                {
                    "tool": "update_relationships_batch",
                    "operations_count": len(propose_ops),
                }
            ],
        )

    def _parse_tool_message(self, message: str) -> dict[str, str]:
        """Parse TOOL:name|k=v|k=v messages into a dict."""
        body = message.split(":", 1)[1] if ":" in message else message
        parts = body.split("|")
        params: dict[str, str] = {}
        for part in parts[1:]:  # skip tool name segment
            if "=" not in part:
                continue
            key, value = part.split("=", 1)
            params[key] = value
        return params

    def _load_user(self) -> User | None:
        """Load the actor User for ChangeSet audit fields."""
        if self._user_id is None:
            return None
        try:
            return User.objects.get(pk=self._user_id)
        except User.DoesNotExist:
            logger.info("_load_user | user_id=%s not found", self._user_id)
            return None
