# Backend container — Django + Gunicorn
# Published to ECR, deployed on Elastic Beanstalk.
FROM python:3.14-slim AS base

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc curl && \
    rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Copy dependency manifests first for layer cache efficiency
COPY pyproject.toml README.md ./

# Install runtime deps only (no dev group)
RUN uv sync --no-group dev --no-editable

# Copy source
COPY src/ ./src/
COPY manage.py ./

# Collect static files
RUN uv run python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["uv", "run", "gunicorn", "yggdrasil.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
