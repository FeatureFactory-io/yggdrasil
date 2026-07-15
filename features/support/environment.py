"""
behave-django environment hooks.

Sets Django settings to test_settings so behave uses in-memory SQLite.
"""
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "yggdrasil.test_settings")
os.environ.setdefault("SECRET_KEY", "test-only-insecure-key")
os.environ.setdefault("LLM_PROVIDER", "ollama")
os.environ.setdefault("ANTHROPIC_API_KEY", "")
os.environ.setdefault("OPENAI_API_KEY", "")


def before_all(context):  # type: ignore[no-untyped-def]
    context.base_url = "http://localhost:8000"
