# syntax=docker/dockerfile:1.7
ARG PYTHON_VERSION=3.11

# --- Stage 1: build Tailwind assets ---
FROM alpine:3.20 AS assets
WORKDIR /app

RUN apk add --no-cache curl libstdc++ libgcc

# Copy only what Tailwind needs to scan
COPY app/static/css ./app/static/css
COPY app/templates   ./app/templates
COPY app/static/js   ./app/static/js
COPY tailwind.config.js ./

# Official musl binary
RUN curl -fsSL -o /usr/local/bin/tailwindcss \
      https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-linux-x64-musl \
 && chmod +x /usr/local/bin/tailwindcss \
 && tailwindcss --help >/dev/null

# Compile using your tw.css (works with v4 @source)
RUN if [ -f tailwind.config.js ]; then \
      tailwindcss -c tailwind.config.js \
        -i app/static/css/tw.css -o app/static/css/tw.build.css --minify ; \
    else \
      tailwindcss \
        -i app/static/css/tw.css -o app/static/css/tw.build.css --minify ; \
    fi

# --- Stage 2: runtime ---
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

# App code
COPY . .
# Freshly built Tailwind CSS
COPY --from=assets /app/app/static/css/tw.build.css app/static/css/tw.build.css

# Run as non-root
RUN useradd --create-home --uid 1000 appuser
USER appuser

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
