FROM python:3.11-slim
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/root/.local/bin:$PATH"

# Install uv and create venv
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && curl -LsSf https://astral.sh/uv/install.sh | sh

COPY requirements.txt ./
RUN uv venv /app/.venv \
    && . /app/.venv/bin/activate \
    && uv pip install -r requirements.txt

COPY . .
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8001
CMD ["sh", "-c", "alembic upgrade head || true; uvicorn main:app --host 0.0.0.0 --port ${PORT:-8001}"]
