# syntax=docker/dockerfile:1.7

ARG PYTHON_VERSION=3.11

# ------------------------------
# Stage 1: build Tailwind assets
# ------------------------------
FROM node:20-alpine AS assets
WORKDIR /app

# Copy only the bits Tailwind needs for scanning
COPY tailwind.config.js ./
COPY app/templates ./app/templates
COPY app/static/css ./app/static/css
COPY app/static/js ./app/static/js

RUN npm install tailwindcss@3.4.10
RUN npx tailwindcss \
    -c tailwind.config.js \
    -i app/static/css/tw.css \
    -o app/static/css/tw.build.css \
    --minify

# ------------------------------
# Stage 2: runtime image
# ------------------------------
FROM python:${PYTHON_VERSION}-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    ENV=prod \
    APP_NAME="Expo Site" \
    BACKEND_BASE_URL="http://backend:8000"

WORKDIR /app

# Install system deps needed by psycopg2-binary and runtime tooling
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy project source
COPY . .

# Overwrite Tailwind build with freshly compiled asset
COPY --from=assets /app/app/static/css/tw.build.css app/static/css/tw.build.css

# Create non-root user
RUN useradd --create-home appuser
USER appuser

EXPOSE 8000

CMD ["gunicorn", "app.main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
