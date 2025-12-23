FROM python:3.11-slim

WORKDIR /app

# uv 설치
RUN pip install --no-cache-dir uv

# 프로젝트 파일
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

COPY src ./src

ENV PYTHONUNBUFFERED=1

CMD ["python"]
