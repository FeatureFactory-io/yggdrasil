#!/usr/bin/env python
"""Django management command entry point."""

import os
import sys


def main() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "yggdrasil.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Activate the virtualenv: source .venv/bin/activate"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
