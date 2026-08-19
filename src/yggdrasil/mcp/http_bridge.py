"""
HTTP bridge for Ratatosk CLI → MCP tools (POST /mcp/tools/<name>/).

FastMCP stdio/SSE transports serve IDE clients; the CLI uses simple JSON POST
with Bearer PAT auth against the Django app (SAO.md §18.4).
"""

from __future__ import annotations

import hashlib
import json
import logging
from collections.abc import Callable
from typing import Any

from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from yggdrasil.auth.models import PersonalAccessToken
from yggdrasil.auth.services import TokenService
from yggdrasil.mcp.server import (
    get_current_user_id,
    get_token_scope,
    initialize_mcp,
    set_current_user_id,
    set_token_scope,
)

logger = logging.getLogger("yggdrasil.mcp.http_bridge")

ToolFn = Callable[..., dict[str, Any]]


def _tool_registry() -> dict[str, ToolFn]:
    """Build name → callable map matching FastMCP registration."""
    from yggdrasil.mcp.tools import changeset as changeset_tools
    from yggdrasil.mcp.tools import propose as propose_tools
    from yggdrasil.mcp.tools import query as query_tools
    from yggdrasil.mcp.tools import write as write_tools

    tools: list[ToolFn] = [
        query_tools.list_elements,
        query_tools.search,
        query_tools.get_element,
        query_tools.traverse,
        query_tools.list_changesets,
        query_tools.get_changeset,
        query_tools.list_stereotypes,
        query_tools.list_packages,
        query_tools.list_relationships,
        query_tools.list_ratatosk_runs,
        changeset_tools.approve_changeset,
        changeset_tools.reject_changeset,
        changeset_tools.do_other_changeset,
        changeset_tools.ask_munin,
        propose_tools.ensure_model,
        propose_tools.propose_changeset,
        propose_tools.record_ratatosk_run,
        write_tools.create_element,
        write_tools.update_element,
        write_tools.delete_element,
        write_tools.create_relationship,
        write_tools.update_relationships_batch,
        write_tools.set_model_mode,
    ]
    return {fn.__name__: fn for fn in tools}


@csrf_exempt
@require_POST
def dispatch_tool(request: HttpRequest, tool_name: str) -> JsonResponse:
    """
    Invoke an MCP tool by name with JSON body ``{"arguments": {...}}``.

    :param request: Django HTTP request with Bearer PAT.
    :param tool_name: Registered tool function name.
    :return: JSON ``{"result": ...}`` or error payload.
    """
    initialize_mcp()
    auth_error = _authenticate_request(request)
    if auth_error is not None:
        return auth_error

    registry = _tool_registry()
    fn = registry.get(tool_name)
    if fn is None:
        logger.info(
            "http_bridge.dispatch_tool | branch | tool=%s reason=unknown_tool",
            tool_name,
        )
        return JsonResponse({"error": f"unknown tool {tool_name!r}"}, status=404)

    try:
        body = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        logger.info(
            "http_bridge.dispatch_tool | error | tool=%s reason=invalid_json",
            tool_name,
        )
        return JsonResponse({"error": "invalid JSON body"}, status=400)

    arguments: dict[str, Any] = body.get("arguments") or body
    logger.info(
        "http_bridge.dispatch_tool | entry | tool=%s user_id=%s scope=%s arg_keys=%s",
        tool_name,
        get_current_user_id(),
        get_token_scope(),
        sorted(arguments.keys()),
    )
    try:
        result = fn(**arguments)
    except PermissionError as exc:
        logger.info(
            "http_bridge.dispatch_tool | error | tool=%s reason=permission_denied",
            tool_name,
        )
        return JsonResponse({"error": str(exc)}, status=403)
    except ValueError as exc:
        logger.info(
            "http_bridge.dispatch_tool | error | tool=%s reason=bad_request",
            tool_name,
        )
        return JsonResponse({"error": str(exc)}, status=400)
    except Exception as exc:
        logger.exception("http_bridge.dispatch_tool | error | tool=%s reason=unhandled", tool_name)
        return JsonResponse({"error": str(exc)}, status=500)

    logger.info("http_bridge.dispatch_tool | exit | tool=%s", tool_name)
    return JsonResponse({"result": result})


def _authenticate_request(request: HttpRequest) -> JsonResponse | None:
    """Validate Bearer token and set MCP context vars."""
    header = request.META.get("HTTP_AUTHORIZATION", "")
    if not header.startswith("Bearer "):
        logger.info(
            "http_bridge._authenticate_request | branch | reason=missing_bearer",
        )
        return JsonResponse({"error": "missing Bearer token"}, status=401)
    raw = header[7:].strip()
    user = TokenService().authenticate(raw)
    if user is None:
        logger.info(
            "http_bridge._authenticate_request | branch | reason=invalid_token",
        )
        return JsonResponse({"error": "invalid token"}, status=401)
    token_hash = hashlib.sha256(raw.encode()).hexdigest()
    try:
        scope = PersonalAccessToken.objects.values_list("scope", flat=True).get(
            token_hash=token_hash
        )
    except PersonalAccessToken.DoesNotExist:
        logger.info(
            "http_bridge._authenticate_request | branch | reason=invalid_token",
        )
        return JsonResponse({"error": "invalid token"}, status=401)
    set_current_user_id(user.pk)
    set_token_scope(scope)
    logger.info(
        "http_bridge._authenticate_request | branch | user_pk=%s scope=%s reason=authenticated",
        user.pk,
        scope,
    )
    return None
