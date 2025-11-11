# syntax=docker/dockerfile:1.7
ARG PYTHON_VERSION=3.11

# ------------------------------
# Stage 1: build Tailwind assets (standalone CLI on Alpine)
# ------------------------------
FROM alpine:3.20 AS assets
WORKDIR /app

# curl to download the CLI + runtime libs the musl binary needs
RUN apk add --no-cache curl libstdc++ libgcc

# Copy only what Tailwind needs
COPY app/static/css ./app/static/css
COPY app/templates   ./app/templates
COPY app/static/js   ./app/static/js
COPY tailwind.config.js ./  

# Download the musl build of Tailwind and verify it runs
RUN curl -fsSL -o /usr/local/bin/tailwindcss \
      https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-linux-x64-musl \
 && chmod +x /usr/local/bin/tailwindcss \
 && /usr/local/bin/tailwindcss --help >/dev/null

# Build CSS
RUN if [ -f tailwind.config.js ]; then \
      /usr/local/bin/tailwindcss -c tailwind.config.js \
        -i app/static/css/tw.css -o app/static/css/tw.build.css --minify ; \
    else \
      /usr/local/bin/tailwindcss \
        -i app/static/css/tw.css -o app/static/css/tw.build.css --minify ; \
    fi

# ------------------------------
# Stage 2: runtime image
# ------------------------------
FROM python:${PYTHON_VERSION}-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ENV=prod \
    APP_NAME="Expo Site" \
    BACKEND_BASE_URL="http://backend:8000"

WORKDIR /app

RUN apt-get update \
 && apt-get install -y --no-install-recommends libpq5 curl \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

COPY . .
COPY --from=assets /app/app/static/css/tw.build.css app/static/css/tw.build.css

RUN useradd --create-home --uid 1000 appuser
USER appuser

EXPOSE 8000
CMD ["gunicorn", "app.main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
