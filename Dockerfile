FROM python:3.11-slim

WORKDIR /app

# uv 설치 (공식 바이너리)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 의존성 복사 및 설치
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# 소스 복사
COPY app/ ./app/

# 출력 디렉토리 생성
RUN mkdir -p /app/output /app/data/vectors

EXPOSE 8000

CMD ["sh", "-c", "uv run uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
