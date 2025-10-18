# ATS MAFIA Framework - Integration Guide

## Phase 6: UI-Backend Integration & Docker Deployment

This guide covers the complete setup, deployment, and usage of the ATS MAFIA Framework with full UI-backend integration.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Docker Deployment](#docker-deployment)
3. [Environment Configuration](#environment-configuration)
4. [UI Features](#ui-features)
5. [API Endpoints](#api-endpoints)
6. [WebSocket Communication](#websocket-communication)
7. [Troubleshooting](#troubleshooting)
8. [Development Setup](#development-setup)

---

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- At least one LLM API key (OpenAI, Anthropic, or Google)
- 8GB RAM minimum, 16GB recommended
- Modern web browser (Chrome, Firefox, Safari, or Edge)

### 3-Step Deployment

```bash
# 1. Clone and navigate to the project
cd ats_mafia_framework

# 2. Configure environment variables
cp .env.example .env
# Edit .env and add your API keys

# 3. Launch with Docker Compose
docker-compose up -d
```

Access the UI at: `http://localhost:8501`

---

## Docker Deployment

### Configuration Files

#### docker-compose.yml
The main orchestration file includes:
- ATS MAFIA Framework service
- Redis for caching
- PostgreSQL for data persistence
- Configured volumes and networking

#### Dockerfile
Builds the framework container with:
- Python 3.10 base image
- All required dependencies
- Network scanning tools (nmap, scapy)
- WebSocket support

### Services

| Service | Port | Purpose |
|---------|------|---------|
| ATS MAFIA | 8501 | Streamlit UI |
| API Server | 5000 | REST API |
| WebSocket | 8080 | Real-time updates |
| Redis | 6379 | Caching & sessions |
| PostgreSQL | 5432 | Data storage |

### Docker Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f ats-mafia-framework

# Stop services
docker-compose down

# Rebuild after changes
docker-compose up -d --build

# Access container shell
docker-compose exec ats-mafia-framework bash
```

---

## Environment Configuration

### Required Variables

Create a `.env` file from `.env.example`:

```bash
# LLM API Keys (at least one required)
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
GOOGLE_API_KEY=your-google-key

# Database Configuration
POSTGRES_PASSWORD=your-secure-password
REDIS_PASSWORD=optional-redis-password

# Budget Settings
DEFAULT_SESSION_BUDGET=10.0
BUDGET_ALERT_THRESHOLD=80
```

### Optional Variables

```bash
# Model Configuration
MODEL_CACHE_DIR=/app/.cache/models
DEFAULT_LLM_PROVIDER=openai
DEFAULT_LLM_MODEL=gpt-4

# System Configuration
ATS_MAFIA_LOG_LEVEL=INFO
MAX_CONCURRENT_SESSIONS=10
SESSION_TIMEOUT=60

# Security
JWT_SECRET_KEY=generate-a-secure-random-string
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

---

## UI Features

### 1. Dashboard (Overview)

**Location:** `http://localhost:8501`

**Features:**
- Real-time system status
- Active training sessions
- Performance metrics
- Quick actions

**Usage:**
```javascript
// Dashboard automatically loads on page load
// Real-time updates via WebSocket
```

### 2. Scenarios Page

**Location:** `/templates/scenarios.html`

**Features:**
- Browse available scenarios
- View scenario details
- Launch training sessions
- Configure session parameters

**Workflow:**
1. Select a scenario from the grid
2. Click "Launch Scenario"
3. Configure session name, model, and budget
4. Monitor progress in real-time

### 3. Tools Arsenal

**Location:** `/templates/tools.html`

**Features:**
- Browse all available tools
- Filter by category and status
- View tool details and parameters
- Execute tools with custom parameters
- View execution history

**Example Tool Execution:**
```javascript
// Tools are executed via the UI
// 1. Select tool from grid
// 2. Click "Execute"
// 3. Fill in parameters
// 4. View results in real-time
```

### 4. LLM Management

**Location:** `/templates/llm_management.html`

**Features:**
- Browse available models
- Compare model features and costs
- Monitor spending and budget
- Get model recommendations
- Track token usage

**Cost Monitoring:**
- Real-time cost tracking
- Budget alerts at 80% threshold
- Daily/monthly spending trends
- Per-session cost breakdown

### 5. Analytics Dashboard

**Features:**
- Operator performance metrics
- Success rate tracking
- Leaderboards
- Session analysis
- Cost breakdown

---

## API Endpoints

### Base URL
```
http://localhost:5000/api/v1
```

### Authentication

```javascript
// Login
POST /auth/login
Body: { "username": "user", "password": "pass" }
Response: { "access_token": "...", "refresh_token": "..." }

// Refresh Token
POST /auth/refresh
Body: { "refresh_token": "..." }
```

### Scenarios

```javascript
// Get all scenarios
GET /scenarios
Response: [{ id, name, description, difficulty, ... }]

// Get scenario details
GET /scenarios/{scenarioId}

// Create scenario
POST /scenarios
Body: { name, description, objectives, ... }
```

### Tools

```javascript
// Get all tools
GET /tools?category=scanning
Response: [{ name, category, description, status, ... }]

// Get tool details
GET /tools/{toolName}

// Execute tool
POST /tools/{toolName}/execute
Body: { parameters: { target: "192.168.1.1" } }
Response: { status: "success", output: "...", execution_time: 1.5 }

// Get execution history
GET /tools/history
GET /tools/{toolName}/history
```

### LLM Models

```javascript
// Get available models
GET /llm/models?provider=openai
Response: [{ name, provider, context_window, cost_per_1k_tokens, ... }]

// Get model details
GET /llm/models/{provider}/{modelName}

// Get recommendation
POST /llm/recommend
Body: { task_type: "coding", priority: "balanced", max_budget: 10 }

// Get cost summary
GET /llm/costs/summary?timeframe=30d
Response: { total_spend, avg_session_cost, total_tokens, ... }
```

### Training Sessions

```javascript
// Create session
POST /training/sessions
Body: { scenario_id, name, model, budget }
Response: { id, status, created_at, ... }

// Get session status
GET /training/sessions/{sessionId}

// Stop session
POST /training/sessions/{sessionId}/stop

// Get session costs
GET /training/sessions/{sessionId}/costs
```

### Analytics

```javascript
// Get operator performance
GET /analytics/operators/{operatorId}/performance?timeframe=30d

// Get session analysis
GET /analytics/sessions/{sessionId}

// Get leaderboard
GET /analytics/leaderboard?category=xp&limit=10

// Get cost breakdown
GET /analytics/costs/breakdown?timeframe=30d
```

---

## WebSocket Communication

### Connection

```javascript
// JavaScript client connection
const ws = new WebSocket('ws://localhost:8080/ws?client_id=unique_id');

ws.onopen = () => {
    console.log('Connected to ATS MAFIA server');
};

ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    handleMessage(message);
};
```

### Message Types

#### Client → Server

```javascript
// Subscribe to topic
{
    "type": "subscribe",
    "topic": "system_status"
}

// Join training session
{
    "type": "join_session",
    "session_id": "session-123"
}

// Send heartbeat
{
    "type": "ping",
    "timestamp": 1234567890
}

// Voice command
{
    "type": "voice_command",
    "command": "start"
}
```

#### Server → Client

```javascript
// Connection confirmation
{
    "type": "connected",
    "client_id": "client_abc123",
    "timestamp": "2024-01-15T10:30:00Z"
}

// Training update
{
    "type": "training_update",
    "session_id": "session-123",
    "data": {
        "progress": 75,
        "status": "running",
        "metrics": { ... }
    }
}

// System status
{
    "type": "system_status",
    "data": {
        "status": "operational",
        "cpu_usage": 45,
        "memory_usage": 60,
        "active_sessions": 3
    }
}

// Cost alert
{
    "type": "cost_alert",
    "data": {
        "session_id": "session-123",
        "current_cost": 8.50,
        "budget": 10.00,
        "percentage": 85
    }
}
```

### Using the Real-Time Manager

```javascript
// The UI automatically initializes the real-time manager
const rtManager = window.atsRealtime;

// Subscribe to events
rtManager.subscribe('training_update', (data) => {
    console.log('Training update:', data);
    updateUI(data);
});

// Join a session for updates
rtManager.joinSession('session-123');

// Check connection status
const status = rtManager.getStatus();
console.log('Connected:', status.connected);
console.log('Latency:', status.latency, 'ms');
```

---

## Troubleshooting

### Common Issues

#### 1. Cannot Connect to UI

**Problem:** Browser shows connection error

**Solutions:**
```bash
# Check if containers are running
docker-compose ps

# Check logs
docker-compose logs ats-mafia-framework

# Restart services
docker-compose restart
```

#### 2. WebSocket Connection Fails

**Problem:** Real-time updates not working

**Solutions:**
- Check browser console for WebSocket errors
- Verify port 8080 is accessible
- Check firewall settings
- Ensure WebSocket URL matches deployment

```javascript
// Check WebSocket status in browser console
console.log(window.atsRealtime.getStatus());
```

#### 3. API Endpoints Return 404

**Problem:** API calls fail

**Solutions:**
```bash
# Verify API server is running
curl http://localhost:5000/api/v1/system/health

# Check API logs
docker-compose logs ats-mafia-framework | grep API

# Restart API service
docker-compose restart ats-mafia-framework
```

#### 4. LLM API Key Errors

**Problem:** "API key not configured" error

**Solutions:**
```bash
# Check environment variables
docker-compose exec ats-mafia-framework printenv | grep API_KEY

# Update .env file and restart
docker-compose down
docker-compose up -d
```

#### 5. High Memory Usage

**Problem:** System running slow

**Solutions:**
```bash
# Check resource usage
docker stats

# Limit container resources in docker-compose.yml
services:
  ats-mafia-framework:
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2.0'
```

### Debug Mode

Enable debug logging:

```bash
# In .env file
DEBUG_MODE=true
ATS_MAFIA_LOG_LEVEL=DEBUG

# Restart services
docker-compose restart
```

### Health Checks

```bash
# Check all services
curl http://localhost:5000/api/v1/system/health

# Check WebSocket
wscat -c ws://localhost:8080/ws?client_id=test

# Check database
docker-compose exec postgres pg_isready
```

---

## Development Setup

### Local Development (Without Docker)

```bash
# Install dependencies
pip install -r ats_mafia_framework/requirements.txt
pip install python-nmap scapy websockets fastapi uvicorn

# Set environment variables
export OPENAI_API_KEY=your-key
export PYTHONPATH=$(pwd)

# Run API server
uvicorn ats_mafia_framework.api.main:app --reload --port 5000

# Run WebSocket server
python -m ats_mafia_framework.api.websocket_server

# Serve UI (in another terminal)
cd ats_mafia_framework/ui
python -m http.server 8501
```

### Running Tests

```bash
# Run all tests
pytest ats_mafia_framework/tests/

# Run integration tests only
pytest ats_mafia_framework/tests/test_ui_integration.py -v

# Run with coverage
pytest --cov=ats_mafia_framework --cov-report=html
```

### UI Development

```bash
# Watch for JavaScript changes
cd ats_mafia_framework/ui/js
# Use your preferred build tool or live server

# Test WebSocket locally
node websocket-test-client.js
```

---

## Best Practices

### Security

1. **Never commit API keys** - Use `.env` file (in `.gitignore`)
2. **Use strong passwords** for database
3. **Enable HTTPS** in production
4. **Rotate JWT secrets** regularly
5. **Implement rate limiting** for API endpoints

### Performance

1. **Monitor resource usage** regularly
2. **Set session budgets** to control costs
3. **Use Redis caching** for frequently accessed data
4. **Limit concurrent sessions** based on resources
5. **Clean up old sessions** periodically

### Cost Management

1. **Set monthly budgets** in LLM management
2. **Enable budget alerts** at 80%
3. **Review cost reports** weekly
4. **Choose appropriate models** for tasks
5. **Monitor token usage** per session

---

## Support

### Documentation
- API Documentation: `http://localhost:5000/docs`
- WebSocket API: See `/api/websocket_server.py`
- UI Components: See `/ui/js/*_controller.js`

### Logs
```bash
# All logs
docker-compose logs -f

# Specific service
docker-compose logs -f ats-mafia-framework

# Last 100 lines
docker-compose logs --tail=100
```

### Community
- GitHub Issues: Report bugs and feature requests
- Discussions: Ask questions and share ideas
- Wiki: Community-contributed guides

---

## Next Steps

1. **Explore the UI** - Familiarize yourself with all features
2. **Try a scenario** - Launch your first training session
3. **Configure budget** - Set spending limits in LLM management
4. **Monitor analytics** - Track performance and costs
5. **Customize** - Modify scenarios and add tools

---

## Changelog

### Phase 6 (Current)
- ✅ Complete UI-backend integration
- ✅ Docker deployment configuration
- ✅ Real-time WebSocket communication
- ✅ Tool browser and execution
- ✅ LLM model management
- ✅ Cost monitoring and budget alerts
- ✅ Analytics dashboard
- ✅ Integration tests

### Future Enhancements
- Advanced scenario editor
- Custom tool development interface
- Multi-user support with role-based access
- Enhanced voice system integration
- Performance optimization
- Additional LLM provider support

---

**Last Updated:** 2024-01-15
**Version:** 1.0.0 (Phase 6 Complete)