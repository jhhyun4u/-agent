FROM python:3.11-slim

WORKDIR /app

# curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# uv 설치 (공식 바이너리)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 의존성 복사 및 설치
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# 소스 복사
COPY app/ ./app/

# 출력 디렉토리 생성 + non-root 사용자
RUN mkdir -p /app/output /app/data/vectors \
    && useradd -m -r appuser \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

CMD ["sh", "-c", "uv run uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
