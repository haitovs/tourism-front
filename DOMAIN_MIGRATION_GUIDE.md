# Domain Migration Guide: New Domain Configuration

## Overview

This document outlines the complete domain migration from current domains to the new domain structure:

-   **turkmenchina.com** - Main site (theme: main)
-   **travel-turkmenistan.com** - Site B (theme: site-b)
-   **tcbfe.com** - Redirect to turkmenchina.com

## Frontend Changes Completed ✅

### 1. Environment Files Updated

-   `.env.docker`: Updated for production with new domains and local backend URL
-   `.env`: Updated for local development with new domains added

### 2. Docker Configuration

-   `Dockerfile`: Updated default `BACKEND_BASE_URL` to use local backend
-   `docker-compose.yml`: Fixed network configuration to match backend (`tourism`)

### 3. Domain Mapping

New `SITE_MAP_RAW` configuration:

```
turkmenchina.com:main:1,travel-turkmenistan.com:site-b:2
```

## Backend Changes Required ⚠️

### Update Backend CORS Configuration

In your backend project's `.env.docker`, update `CORS_ALLOW_ORIGINS`:

```
CORS_ALLOW_ORIGINS=https://akyoltm.shop,https://www.akyoltm.shop,https://china.akyoltm.shop,https://www.china.akyoltm.shop,https://tourism.akyoltm.shop,https://www.tourism.akyoltm.shop,https://china.oguzforum.com,https://travel.oguzforum.com,https://turkmenchina.com,https://www.turkmenchina.com,https://travel-turkmenistan.com,https://www.travel-turkmenistan.com
```

**Keep existing domains** to maintain admin panel access via `api.akyoltm.shop`.

## Server Configuration Required ⚠️

### 1. Nginx Reverse Proxy Configuration

Create nginx configuration for the three domains:

```nginx
# turkmenchina.com - Main site
server {
    listen 80;
    listen [::]:80;
    server_name turkmenchina.com www.turkmenchina.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name turkmenchina.com www.turkmenchina.com;

    # SSL certificates (required)
    ssl_certificate /path/to/turkmenchina.com.crt;
    ssl_certificate_key /path/to/turkmenchina.com.key;

    location / {
        proxy_pass http://127.0.0.1:8081;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# travel-turkmenistan.com - Site B
server {
    listen 80;
    listen [::]:80;
    server_name travel-turkmenistan.com www.travel-turkmenistan.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name travel-turkmenistan.com www.travel-turkmenistan.com;

    # SSL certificates (required)
    ssl_certificate /path/to/travel-turkmenistan.com.crt;
    ssl_certificate_key /path/to/travel-turkmenistan.com.key;

    location / {
        proxy_pass http://127.0.0.1:8081;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# tcbfe.com - Redirect to turkmenchina.com
server {
    listen 80;
    listen [::]:80;
    server_name tcbfe.com www.tcbfe.com;
    return 301 https://turkmenchina.com$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name tcbfe.com www.tcbfe.com;

    # SSL certificates (required)
    ssl_certificate /path/to/tcbfe.com.crt;
    ssl_certificate_key /path/to/tcbfe.com.key;

    # Permanent redirect to turkmenchina.com
    return 301 https://turkmenchina.com$request_uri;
}
```

### 2. SSL Certificates Required

You need to obtain SSL certificates for:

-   `turkmenchina.com` + `www.turkmenchina.com`
-   `travel-turkmenistan.com` + `www.travel-turkmenistan.com`
-   `tcbfe.com` + `www.tcbfe.com`

**Recommended**: Use Let's Encrypt with Certbot:

```bash
# Install certbot if not already installed
sudo apt update
sudo apt install certbot python3-certbot-nginx

# Obtain certificates
sudo certbot --nginx -d turkmenchina.com -d www.turkmenchina.com
sudo certbot --nginx -d travel-turkmenistan.com -d www.travel-turkmenistan.com
sudo certbot --nginx -d tcbfe.com -d www.tcbfe.com
```

### 3. Docker Network Configuration

Ensure both frontend and backend containers can communicate. From your backend configuration, both should use the `tourism` network.

## Deployment Steps

### 1. Backend Updates

1. Update backend `.env.docker` with new CORS origins
2. Rebuild and restart backend container

### 2. Frontend Updates

1. All frontend files are already updated ✅
2. Rebuild and restart frontend container:

    ```bash
    docker compose down
    docker compose build --no-cache
    docker compose up -d
    ```

### 3. Server Configuration

1. Set up nginx configuration
2. Obtain SSL certificates
3. Test domain resolution
4. Update DNS records if needed

### 4. Testing Checklist

-   [ ] turkmenchina.com loads with main theme
-   [ ] travel-turkmenistan.com loads with site-b theme
-   [ ] tcbfe.com redirects to turkmenchina.com
-   [ ] API calls work with local backend
-   [ ] Admin panel accessible via api.akyoltm.shop
-   [ ] SSL certificates valid for all domains
-   [ ] HTTPS redirects working properly

## Docker Commands for Deployment

```bash
# Stop current containers
docker compose down

# Build with no cache to ensure latest changes
docker compose build --no-cache

# Start services
docker compose up -d

# Check logs
docker compose logs -f

# Check container status
docker compose ps
```

## Network Troubleshooting

If containers can't communicate:

```bash
# Check network exists
docker network ls

# Create network if needed
docker network create tourism

# Connect containers to network
docker network connect tourism tourism-backend-1
docker network connect tourism tourism-frontend-1
```

## Notes

1. **Theme Mapping**:

    - `turkmenchina.com` → uses `main` theme (site ID: 1)
    - `travel-turkmenistan.com` → uses `site-b` theme (site ID: 2)

2. **Backend Communication**: Frontend now uses `http://backend:8000` for API calls within Docker network

3. **Admin Access**: Admin panel remains accessible via `api.akyoltm.shop`

4. **Local Development**: Local `.env` file includes new domains alongside localhost for testing
