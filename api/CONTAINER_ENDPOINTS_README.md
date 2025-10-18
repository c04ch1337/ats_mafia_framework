# Container Lifecycle Management API

Production-grade REST API for managing container orchestration, health monitoring, and profile-based container preparation.

## Overview

This API provides comprehensive endpoints for:
- **Profile-based container preparation** - Automatically start required containers for profiles
- **Container lifecycle management** - Start, stop, and monitor individual containers
- **Pool status monitoring** - Monitor hot/warm/cold container pools
- **Health checking** - Verify orchestrator and container health
- **Performance metrics** - Track container lifecycle operations
- **Configuration management** - Hot-reload pool configurations

## Quick Start

### Installation

```bash
# Install FastAPI and dependencies
pip install fastapi uvicorn[standard] docker pyyaml

# Install the framework
pip install -e .
```

### Running the API

```bash
# Using the example application
uvicorn ats_mafia_framework.api.container_app_example:app --reload --host 0.0.0.0 --port 8000

# Or integrate into your own FastAPI app
from fastapi import FastAPI
from ats_mafia_framework.api.container_endpoints import router

app = FastAPI()
app.include_router(router)
```

### Interactive Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Profile Container Management

#### POST `/api/v1/containers/prepare`

Prepare all containers required for a profile.

**Request:**
```json
{
  "profile_id": "red_team_operator",
  "force_restart": false
}
```

**Response (200 OK):**
```json
{
  "profile_id": "red_team_operator",
  "containers": {
    "ats_network_nmap": {
      "status": "ready",
      "healthy": true,
      "estimated_time": 0
    },
    "ats_recon_amass": {
      "status": "ready",
      "healthy": true,
      "estimated_time": 0
    }
  },
  "all_ready": true,
  "estimated_wait_seconds": 0,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Use Case:**
```python
import requests

# Prepare containers for a profile
response = requests.post(
    "http://localhost:8000/api/v1/containers/prepare",
    json={
        "profile_id": "red_team_operator",
        "force_restart": False
    }
)

if response.json()["all_ready"]:
    print("All containers ready!")
else:
    print(f"Wait ~{response.json()['estimated_wait_seconds']}s for containers to start")
```

#### GET `/api/v1/containers/status/{profile_id}`

Get status of all containers for a profile.

**Response (200 OK):**
```json
{
  "profile_id": "red_team_operator",
  "containers": {
    "ats_network_nmap": {
      "container_name": "ats_network_nmap",
      "status": "running",
      "pool": "warm",
      "healthy": true,
      "uptime_seconds": 3600.5,
      "last_used": "2024-01-15T10:30:00Z",
      "metrics": null
    }
  },
  "ready": true,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Use Case:**
```python
# Poll for container readiness
import time

profile_id = "red_team_operator"
while True:
    response = requests.get(f"http://localhost:8000/api/v1/containers/status/{profile_id}")
    data = response.json()
    
    if data["ready"]:
        print("All containers ready!")
        break
    
    print("Waiting for containers...")
    time.sleep(2)
```

### Individual Container Control

#### POST `/api/v1/containers/start`

Start a specific container.

**Request:**
```json
{
  "container_name": "ats_network_nmap",
  "wait_for_health": true,
  "timeout": 120
}
```

**Response (202 Accepted):**
```json
{
  "message": "Container ats_network_nmap is starting",
  "container_name": "ats_network_nmap",
  "wait_for_health": true,
  "estimated_time": 20
}
```

#### POST `/api/v1/containers/stop`

Stop a specific container.

**Request:**
```json
{
  "container_name": "ats_network_nmap",
  "force": false,
  "timeout": 30
}
```

**Response (200 OK):**
```json
{
  "message": "Container ats_network_nmap stopped successfully",
  "container_name": "ats_network_nmap"
}
```

### Pool Status Monitoring

#### GET `/api/v1/containers/pools/{pool_type}`

Get status of a container pool (hot/warm/cold).

**Pool Types:**
- `hot` - Always running core services
- `warm` - On-demand with TTL
- `cold` - Rarely used, started only when needed

**Response (200 OK):**
```json
{
  "pool_type": "warm",
  "description": "Warm pool - frequently used tools with TTL management",
  "containers": [
    "ats_network_nmap",
    "ats_recon_amass",
    "ats_web_zap"
  ],
  "active_count": 2,
  "total_count": 3,
  "health_check_interval": 60,
  "ttl_seconds": 1800
}
```

**Use Case:**
```python
# Monitor all pools
for pool_type in ['hot', 'warm', 'cold']:
    response = requests.get(f"http://localhost:8000/api/v1/containers/pools/{pool_type}")
    pool = response.json()
    print(f"{pool['pool_type'].upper()}: {pool['active_count']}/{pool['total_count']} active")
```

### Metrics and Monitoring

#### GET `/api/v1/containers/metrics`

Get orchestrator performance metrics.

**Response (200 OK):**
```json
{
  "total_starts": 45,
  "total_stops": 23,
  "total_failures": 2,
  "average_startup_time": 15.3,
  "active_containers": 8,
  "pool_distribution": {
    "hot": 4,
    "warm": 3,
    "cold": 1
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### GET `/api/v1/containers/health`

Health check endpoint for monitoring.

**Response (200 OK - Healthy):**
```json
{
  "status": "healthy",
  "initialized": true,
  "cleanup_task_running": true,
  "active_containers": 8,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Response (503 Service Unavailable - Unhealthy):**
```json
{
  "detail": "Orchestrator not initialized"
}
```

### Configuration Management

#### POST `/api/v1/containers/reload-config`

Reload container pool configuration from YAML without restarting.

**Response (200 OK):**
```json
{
  "message": "Configuration reloaded successfully",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Use Case:**
```bash
# 1. Update container_pools.yaml
vim ats_mafia_framework/config/container_pools.yaml

# 2. Reload configuration
curl -X POST http://localhost:8000/api/v1/containers/reload-config
```

## Integration Examples

### Frontend Integration

```javascript
// React/Vue/Angular example
class ContainerManager {
  constructor(baseUrl = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
  }

  async prepareProfile(profileId) {
    const response = await fetch(`${this.baseUrl}/api/v1/containers/prepare`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ profile_id: profileId, force_restart: false })
    });
    return response.json();
  }

  async pollProfileStatus(profileId, maxAttempts = 30) {
    for (let i = 0; i < maxAttempts; i++) {
      const response = await fetch(
        `${this.baseUrl}/api/v1/containers/status/${profileId}`
      );
      const data = await response.json();
      
      if (data.ready) {
        return data;
      }
      
      await new Promise(resolve => setTimeout(resolve, 2000));
    }
    throw new Error('Timeout waiting for containers');
  }

  async getMetrics() {
    const response = await fetch(`${this.baseUrl}/api/v1/containers/metrics`);
    return response.json();
  }
}

// Usage
const manager = new ContainerManager();

// Prepare and wait for profile
async function startProfile(profileId) {
  console.log(`Preparing containers for ${profileId}...`);
  await manager.prepareProfile(profileId);
  
  console.log('Waiting for containers to be ready...');
  const status = await manager.pollProfileStatus(profileId);
  
  console.log('All containers ready!', status);
}
```

### Python Client

```python
import requests
import time
from typing import Dict, Any

class ContainerClient:
    """Python client for Container Management API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def prepare_profile(self, profile_id: str, force_restart: bool = False) -> Dict[str, Any]:
        """Prepare containers for a profile."""
        response = self.session.post(
            f"{self.base_url}/api/v1/containers/prepare",
            json={"profile_id": profile_id, "force_restart": force_restart}
        )
        response.raise_for_status()
        return response.json()
    
    def wait_for_profile(self, profile_id: str, timeout: int = 300) -> bool:
        """Wait for all profile containers to be ready."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            response = self.session.get(
                f"{self.base_url}/api/v1/containers/status/{profile_id}"
            )
            response.raise_for_status()
            
            data = response.json()
            if data["ready"]:
                return True
            
            time.sleep(2)
        
        return False
    
    def start_container(self, container_name: str) -> Dict[str, Any]:
        """Start a specific container."""
        response = self.session.post(
            f"{self.base_url}/api/v1/containers/start",
            json={"container_name": container_name}
        )
        response.raise_for_status()
        return response.json()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get orchestrator metrics."""
        response = self.session.get(f"{self.base_url}/api/v1/containers/metrics")
        response.raise_for_status()
        return response.json()

# Usage
client = ContainerClient()

# Prepare and wait
client.prepare_profile("red_team_operator")
if client.wait_for_profile("red_team_operator"):
    print("Ready to execute!")
```

## Error Handling

All endpoints return appropriate HTTP status codes:

- **200 OK** - Success
- **202 Accepted** - Async operation started
- **400 Bad Request** - Invalid request data
- **404 Not Found** - Resource not found
- **500 Internal Server Error** - Server error
- **503 Service Unavailable** - Service not ready

Error response format:
```json
{
  "detail": "Error message describing what went wrong"
}
```

## Best Practices

1. **Always check health before operations**
   ```python
   response = requests.get("http://localhost:8000/api/v1/containers/health")
   if response.status_code != 200:
       print("Orchestrator not ready")
   ```

2. **Use async operations for container starts**
   - POST /start returns 202 immediately
   - Poll GET /status to check completion

3. **Monitor metrics for performance**
   - Track failure rates
   - Monitor average startup times
   - Watch pool distribution

4. **Handle TTL in warm pool**
   - Containers auto-stop after TTL
   - Re-prepare if needed
   - Monitor last_used timestamps

5. **Use profile preparation for multi-container workflows**
   - Single call prepares all needed containers
   - Parallel startup for efficiency
   - Automatic health checking

## Testing

Run the test suite:

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/test_container_endpoints.py -v

# With coverage
pytest tests/test_container_endpoints.py --cov=ats_mafia_framework.api.container_endpoints
```

## Security Considerations

1. **Authentication** - Add authentication middleware:
   ```python
   from fastapi import Depends, HTTPException
   from fastapi.security import HTTPBearer
   
   security = HTTPBearer()
   
   async def verify_token(token = Depends(security)):
       # Implement token verification
       pass
   
   # Add to endpoints
   @router.post("/prepare", dependencies=[Depends(verify_token)])
   ```

2. **Rate Limiting** - Prevent abuse:
   ```python
   from slowapi import Limiter
   from slowapi.util import get_remote_address
   
   limiter = Limiter(key_func=get_remote_address)
   app.state.limiter = limiter
   ```

3. **CORS** - Configure appropriately:
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://your-domain.com"],  # Specific origins
       allow_credentials=True,
       allow_methods=["GET", "POST"],
       allow_headers=["*"],
   )
   ```

## Troubleshooting

### Container won't start
```python
# Check orchestrator health
response = requests.get("http://localhost:8000/api/v1/containers/health")
print(response.json())

# Check specific container status
response = requests.get("http://localhost:8000/api/v1/containers/status/profile_id")
print(response.json())

# View metrics for errors
response = requests.get("http://localhost:8000/api/v1/containers/metrics")
print(f"Failures: {response.json()['total_failures']}")
```

### Profile not found
- Verify profile_id exists in container_pools.yaml
- Check profile_mappings section
- Reload configuration after changes

### Slow startup times
- Check pool configuration
- Consider moving to warm/hot pool
- Review container health checks
- Check Docker resource limits

## Support

For issues or questions:
- Check logs: orchestrator logs container operations
- Review metrics: /metrics endpoint shows operational stats
- Health check: /health endpoint for quick diagnosis

## License

Part of the ATS MAFIA Framework - See main LICENSE file.