"""
Test settings — inherits from base settings, overrides DB to in-memory SQLite.

Used by pytest via pyproject.toml DJANGO_SETTINGS_MODULE.
No Docker or Postgres/Redis required for unit and integration tests.
"""

import os

# Ensure minimal required env vars are set before importing base settings
os.environ.setdefault("SECRET_KEY", "test-only-insecure-key")
os.environ.setdefault("DATABASE_URL", "sqlite://:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
# Discovery / Munin tests use scripted LLM — never call a real provider in CI.
os.environ.setdefault("LLM_PROVIDER", "scripted")
os.environ.setdefault("ANTHROPIC_API_KEY", "")
os.environ.setdefault("OPENAI_API_KEY", "")
os.environ.setdefault("OLLAMA_BASE_URL", "http://localhost:11434")

from yggdrasil.settings import *  # noqa: F403

# behave-django management command (`manage.py behave`) requires its app
# registered to expose the `behave` management command.
INSTALLED_APPS = [*INSTALLED_APPS, "behave_django"]  # noqa: F405

# Acceptance/E2E fixtures (seed.json, presets) live outside any single app.
FIXTURE_DIRS = [BASE_DIR / "tests" / "fixtures"]  # noqa: F405

# Force SQLite regardless of what .env says
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Use Django's dummy cache for tests — no Redis required
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}

# Speed up password hashing in tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]
