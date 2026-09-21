FROM python:3.12.14-slim-bookworm@sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e AS base
RUN pip install --no-cache-dir uv==0.12.17
ENV UV_PROJECT_ENVIRONMENT=/opt/venv PATH="/opt/venv/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app/apps/api
COPY apps/api/pyproject.toml apps/api/uv.lock ./
RUN uv sync --locked --no-dev
COPY apps/api/app ./app
COPY apps/api/alembic.ini ./
COPY apps/api/migrations ./migrations
COPY data/source/products.json data/source/knowledge_entries.json data/source/customers.json data/source/quotes.json data/source/quote_items.json data/source/price_rules.json /app/data/source/
RUN useradd --uid 10001 --create-home appuser
FROM base AS runtime
USER appuser
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
FROM base AS test
RUN uv sync --locked
COPY apps/api/tests ./tests
COPY data/source/golden_test_scenarios.json /app/test-source/
CMD ["pytest", "-v"]
