"""
Page-name registry for Gherkin navigation steps.

Maps human-readable page names used in scenarios to Django URL names,
resolved via ``reverse()`` (AT) or ``context.get_url()`` (E2E).
"""

from __future__ import annotations

from django.urls import reverse

# Human-readable page name -> Django URL name (may include namespace)
PAGE_REGISTRY: dict[str, str] = {
    "landing": "web:index",
    "health": "health",
}


def resolve_page_path(page_name: str) -> str:
    """
    Resolve a registry page name to a URL path.

    :param page_name: key in ``PAGE_REGISTRY``. Example: ``"landing"``.
    :return: URL path. Example: ``"/"``.
    :raises KeyError: if ``page_name`` is not registered.
    """
    url_name = PAGE_REGISTRY[page_name]
    return reverse(url_name)
