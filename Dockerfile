# syntax=docker/dockerfile:1.7
ARG PYTHON_VERSION=3.11
FROM python:${PYTHON_VERSION}-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ENV=prod \
    APP_NAME="Expo Site" \
    BACKEND_BASE_URL="http://backend:8000"

WORKDIR /app

# Small runtime deps
RUN apt-get update \
 && apt-get install -y --no-install-recommends libpq5 curl \
 && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Project (includes your prebuilt app/static/css/tw.build.css)
COPY . .

# Run as non-root
RUN useradd --create-home --uid 1000 appuser
USER appuser

EXPOSE 8000
CMD ["gunicorn","app.main:app","--workers","4","--worker-class","uvicorn.workers.UvicornWorker","--bind","0.0.0.0:8000"]
