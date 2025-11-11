# syntax=docker/dockerfile:1.7
ARG PYTHON_VERSION=3.11

# ------------------------------
# Stage 1: build Tailwind assets (Tailwind v4)
# ------------------------------
FROM node:20-alpine AS assets
WORKDIR /app
ENV NODE_ENV=production \
    BROWSERSLIST_IGNORE_OLD_DATA=1

# Copy what Tailwind needs
COPY app/static/css ./app/static/css
COPY app/templates   ./app/templates
COPY app/static/js   ./app/static/js
COPY tailwind.config.js ./ 

# Ensure a local install and use the local binary (avoid npx ambiguity)
RUN npm init -y >/dev/null 2>&1 || true
RUN npm install --no-audit --no-fund tailwindcss@latest

# Build CSS (use config if present)
RUN if [ -f tailwind.config.js ]; then \
      ./node_modules/.bin/tailwindcss -c tailwind.config.js \
        -i app/static/css/tw.css \
        -o app/static/css/tw.build.css \
        --minify ; \
    else \
      ./node_modules/.bin/tailwindcss \
        -i app/static/css/tw.css \
        -o app/static/css/tw.build.css \
        --minify ; \
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

# Runtime deps
RUN apt-get update \
 && apt-get install -y --no-install-recommends libpq5 curl \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Overwrite Tailwind build with freshly compiled asset
COPY --from=assets /app/app/static/css/tw.build.css app/static/css/tw.build.css

# Non-root user (UID 1000 for consistency)
RUN useradd --create-home --uid 1000 appuser
USER appuser

EXPOSE 8000
CMD ["gunicorn", "app.main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
