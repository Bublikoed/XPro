FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    "fastapi>=0.115.0" \
    "uvicorn[standard]>=0.30.0" \
    "sqlalchemy[asyncio]>=2.0.0" \
    "aiomysql>=0.2.0" \
    "cryptography>=42.0.0" \
    "pydantic>=2.0.0" \
    "pydantic-settings>=2.0.0"

COPY . .

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
