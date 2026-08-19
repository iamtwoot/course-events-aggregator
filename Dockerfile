FROM python:3.13-slim

WORKDIR /app

RUN pip install uv

COPY pyproject.toml uv.lock alembic.ini ./
RUN uv sync --no-dev

COPY src src

CMD ["sh", "-c", "uv run --no-sync alembic upgrade head && uv run --no-sync uvicorn src.main:app --host 0.0.0.0 --port 8000"]
