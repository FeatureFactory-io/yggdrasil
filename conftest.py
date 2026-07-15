"""
Root pytest conftest.

Django settings are selected via pyproject.toml (DJANGO_SETTINGS_MODULE = "yggdrasil.test_settings").
test_settings.py forces in-memory SQLite — no Docker/Postgres required for unit tests.
"""
