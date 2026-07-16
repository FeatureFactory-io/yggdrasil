"""
Personal access token authentication for DRF.

Placeholder implementation — full token hashing and RBAC in a later sprint.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from rest_framework.authentication import BaseAuthentication

if TYPE_CHECKING:
    from rest_framework.request import Request

logger = logging.getLogger("yggdrasil.auth")


class TokenAuthentication(BaseAuthentication):
    """
    Authenticate via ``Authorization: Bearer <token>`` header.

    Placeholder — returns ``None`` (anonymous) until the auth app
    models are implemented.

    :param request: DRF request object.
    :return: ``None`` (defer to next authenticator).
    """

    def authenticate(self, request: Request) -> None:  # type: ignore[override]
        logger.debug("TokenAuthentication.authenticate called (placeholder)")
        return None
