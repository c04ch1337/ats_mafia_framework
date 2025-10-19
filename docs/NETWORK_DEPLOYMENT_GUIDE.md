# Network Deployment Guide for ATS MAFIA UI

This guide explains how to configure ATS MAFIA when the UI is accessed from a different machine or network location than the Docker host.

## Problem

When you access the UI from `http://192.168.1.100:8501` but the API tries to call `http://localhost:8000`, the browser cannot reach the backend because "localhost" refers to the client machine, not the Docker host.

## Solution: Environment-Based Configuration

The framework now supports automatic hostname detection and environment variable configuration.

### Quick Setup

1. **Create `.env` file** (copy from `.env.example`):
   ```bash
   cp .env.example .env
   ```

2. **Set your Docker host IP** in `.env`:
   ```bash
   # Find your Docker host IP address
   # On Windows: ipconfig
   # On Linux/Mac: ifconfig or ip addr
   
   # Set it in .env
   DOCKER_HOST_IP=192.168.1.100
   ```

3. **Restart docker-compose**:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

4. **Access the UI** from any device on your network:
   ```
   http://192.168.1.100:8501/index.html
   http://192.168.1.100:8501/profiles.html
   ```

## How It Works

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│  UI Container Startup                                    │
│  1. env-inject.sh runs                                   │
│  2. Reads DOCKER_HOST_IP, API_HOST, etc. from env        │
│  3. Generates ui/js/env.js with window.ENV               │
│  4. http.server starts on port 8501                      │
└─────────────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────┐
│  Browser Loads Page                                      │
│  1. Loads env.js → sets window.ENV                       │
│  2. Loads config.js → creates window.ATS_CONFIG from ENV │
│  3. Loads api-client.js → uses ATS_CONFIG.apiBaseURL     │
│  4. Loads main.js → applies config to window.atsAPI      │
└─────────────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────┐
│  API Calls Use Correct Hostname                          │
│  POST http://192.168.1.100:8000/api/v1/profiles ✓        │
└─────────────────────────────────────────────────────────┘
```

### Configuration Files

#### 1. [ui/env-inject.sh](../ui/env-inject.sh)
Shell script that runs at container startup to generate `ui/js/env.js` from environment variables.

#### 2. [ui/js/env.js](../ui/js/env.js) (auto-generated)
Contains `window.ENV` with runtime configuration:
```javascript
window.ENV = {
    API_HOST: '192.168.1.100',
    API_PORT: '8000',
    API_PROTOCOL: 'http',
    WEBSOCKET_HOST: '192.168.1.100',
    WEBSOCKET_PORT: '8080',
    WEBSOCKET_PROTOCOL: 'ws',
    ENVIRONMENT: 'production'
};
```

#### 3. [ui/js/config.js](../ui/js/config.js)
Merges `window.ENV` with defaults to create `window.ATS_CONFIG`:
```javascript
window.ATS_CONFIG = {
    apiBaseURL: 'http://192.168.1.100:8000/api/v1',
    websocketURL: 'ws://192.168.1.100:8080/ws',
    theme: 'dark',
    autoRefresh: true,
    // ... more settings
};
```

#### 4. Client Code
- [ATSAPIClient](../ui/js/api-client.js) - Auto-detects hostname and port, or uses `ATS_CONFIG.apiBaseURL`
- [ATSApplication](../ui/js/main.js) - Loads `window.ATS_CONFIG` into app config
- [ATSProfiles](../ui/js/profiles.js) - Uses configured API base for create/update/delete

### Docker Compose Configuration

The UI container command in [docker-compose.yml](../docker-compose.yml) now runs:
```yaml
command: sh -c "sh /app/ats_mafia_framework/ui/env-inject.sh && cd /app/ats_mafia_framework/ui && python -m http.server 8501 --bind 0.0.0.0"
```

Environment variables injected:
```yaml
environment:
  - API_HOST=${DOCKER_HOST_IP:-ats-mafia-api}
  - API_PORT=8000
  - API_PROTOCOL=http
  - WEBSOCKET_HOST=${DOCKER_HOST_IP:-ats-mafia-websocket}
  - WEBSOCKET_PORT=8080
  - WEBSOCKET_PROTOCOL=ws
```

## Deployment Scenarios

### Scenario 1: Local Development (localhost)
**No .env needed** - defaults work.

Access: `http://localhost:8501`
API calls: `http://localhost:8000/api/v1/*`

### Scenario 2: Local Network (LAN)
**Set DOCKER_HOST_IP in .env**

```bash
# .env
DOCKER_HOST_IP=192.168.1.100
```

Access from any device: `http://192.168.1.100:8501`
API calls: `http://192.168.1.100:8000/api/v1/*`

### Scenario 3: Remote Server
**Set DOCKER_HOST_IP to public IP or domain**

```bash
# .env
DOCKER_HOST_IP=server.example.com
```

Access: `http://server.example.com:8501`
API calls: `http://server.example.com:8000/api/v1/*`

### Scenario 4: Production with Reverse Proxy
**Set protocol and paths**

```bash
# .env
DOCKER_HOST_IP=api.example.com
API_PROTOCOL=https
```

Configure nginx/traefik to route:
- `https://api.example.com/` → UI container :8501
- `https://api.example.com/api/` → API container :8000

## Troubleshooting

### Issue: 404 on /api/v1/profiles

**Check:**
1. Backend is running: `docker-compose ps`
2. Backend health: `curl http://192.168.1.100:8000/health`
3. API docs: Open `http://192.168.1.100:8000/docs` and verify `/api/v1/profiles` endpoints exist

**Fix:**
```bash
# Restart API container
docker-compose restart ats-mafia-api
```

### Issue: CORS errors

**Check:**
- CORS is enabled in [api/container_app_example.py](../api/container_app_example.py)
- `allow_credentials=False` for file:// origins

**Verify CORS headers:**
```bash
curl -H "Origin: http://192.168.1.100:8501" \
     -H "Access-Control-Request-Method: POST" \
     -X OPTIONS \
     http://192.168.1.100:8000/api/v1/profiles
```

### Issue: Wrong API hostname in browser

**Check Console logs:**
```javascript
// Should show:
"ATSApplication: loaded config with apiBaseURL = http://192.168.1.100:8000/api/v1"
"ATSAPIClient: normalized baseURL to http://192.168.1.100:8000/api/v1"
```

**Manual override (temporary):**
Open DevTools console:
```javascript
localStorage.setItem('ats_config', JSON.stringify({ 
    apiBaseURL: 'http://192.168.1.100:8000/api/v1' 
}));
location.reload();
```

### Issue: env.js not generated

**Check UI container startup:**
```bash
docker-compose logs ats-mafia-ui | grep env-inject
```

**Should see:**
```
Generated env.js with API_HOST=192.168.1.100, API_PORT=8000
```

**Manual generation:**
```bash
docker-compose exec ats-mafia-ui sh /app/ats_mafia_framework/ui/env-inject.sh
```

## Verification Steps

After configuration:

1. **Check env.js was generated:**
   ```bash
   docker-compose exec ats-mafia-ui cat /app/ats_mafia_framework/ui/js/env.js
   ```
   
   Should contain your DOCKER_HOST_IP.

2. **Open browser DevTools Console** on `http://YOUR_IP:8501/profiles.html`
   
   Should see:
   ```
   Environment configuration loaded: {API_HOST: "192.168.1.100", ...}
   ATS MAFIA Configuration loaded: {apiBaseURL: "http://192.168.1.100:8000/api/v1", ...}
   ATSApplication: loaded config with apiBaseURL = http://192.168.1.100:8000/api/v1
   ATSAPIClient: normalized baseURL to http://192.168.1.100:8000/api/v1
   ```

3. **Test Profile Creation:**
   - Click "Create Profile"
   - Fill form and submit
   - Check Network tab: POST should go to `http://YOUR_IP:8000/api/v1/profiles`
   - Should return 201 Created

4. **Verify API Documentation:**
   Open `http://YOUR_IP:8000/docs`
   - Should show FastAPI interactive docs
   - Should list `/api/v1/profiles` endpoints

## Files Modified

- [docker-compose.yml](../docker-compose.yml) - Added DOCKER_HOST_IP support
- [.env.example](../.env.example) - Added DOCKER_HOST_IP documentation
- [ui/env-inject.sh](../ui/env-inject.sh) - Environment injection script
- [ui/js/env.js](../ui/js/env.js) - Auto-generated from env vars (gitignored)
- [ui/js/config.js](../ui/js/config.js) - Configuration loader
- [ui/js/api-client.js](../ui/js/api-client.js) - Hostname-aware base URL
- [ui/js/main.js](../ui/js/main.js) - Reads window.ATS_CONFIG
- [ui/index.html](../ui/index.html) - Loads config.js first
- [ui/profiles.html](../ui/profiles.html) - Loads config.js first

## See Also

- [API Interactions Documentation](API_INTERACTIONS.md) - System architecture and sequences
- [README.md](../README.md) - Main framework documentation