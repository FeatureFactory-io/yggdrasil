"""Shared helpers for E2E step modules (no behave step decorators)."""


def test_id(field: str, suffix: str) -> str:
    """Build a ``data-testid`` following IA naming conventions."""
    if field.endswith(suffix) or field.endswith("-btn") or field.endswith("-input"):
        return field
    return f"{field}{suffix}"
