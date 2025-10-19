# ATS MAFIA Framework

**Advanced Training System for Multi-Agent Interactive Framework**

A comprehensive framework for creating, managing, and training specialized agent profiles for various security scenarios including red team, blue team, and social engineering simulations.

## 🎯 Overview

ATS MAFIA Framework is a sophisticated multi-agent training system designed for cybersecurity education, penetration testing practice, and security team coordination. It provides a modular, extensible platform for creating realistic training scenarios with intelligent agents that can simulate various attack and defense techniques.

## 🆕 What's New

- Profiles API added: /api/v1/profiles via [profile_endpoints.router](api/profile_endpoints.py:400), mounted in [container_app_example.py](api/container_app_example.py:51) with development CORS enabled.
- UI can create agents: Use top menu "Profiles" or Dashboard Quick Action "Launch Profile" to open [ui/profiles.html](ui/profiles.html:1).
- Architecture and sequence diagrams: see [docs/API_INTERACTIONS.md](docs/API_INTERACTIONS.md:1).

## 🚀 Key Features

### Core Components

- **Training Orchestrator**: Manages training sessions, scenario execution, and progress tracking
- **Profile Management System**: Handles agent profile creation, validation, and lifecycle management
- **Tool Extension System**: Manages tool integrations and custom tool implementations
- **Agent Communication Protocol**: Enables secure agent-to-agent messaging and coordination
- **Logging and Audit Trail**: Comprehensive logging for compliance and performance analysis

### Agent Capabilities

- **Red Team Operations**: Penetration testing, vulnerability assessment, exploitation
- **Blue Team Defense**: Incident response, threat hunting, security monitoring
- **Social Engineering**: Phishing simulation, social engineering tactics
- **Custom Profiles**: Extensible profile system for specialized roles

### Training Scenarios

- **Network Penetration Testing**: Comprehensive network security exercises
- **Incident Response**: Real-world incident simulation and response
- **Threat Hunting**: Advanced threat detection and analysis
- **Custom Scenarios**: Flexible scenario creation and execution

## 📁 Project Structure

```
ats_mafia_framework/
├── core/                    # Core framework components
│   ├── orchestrator.py      # Training Orchestrator
│   ├── profile_manager.py   # Profile Management System
│   ├── tool_system.py      # Tool Extension System
│   ├── communication.py    # Agent communication
│   └── logging.py          # Logging and audit
├── profiles/               # Agent profile implementations
│   └── red_team_operator.json
├── scenarios/              # Training scenario definitions
│   └── basic_penetration_test.json
├── tools/                  # Custom tool implementations
│   └── network_scanner.py
├── ui/                     # User interface components
├── voice/                  # Voice processing and synthesis
├── api/                    # External API interfaces
├── config/                 # Configuration files
│   └── default.yaml
└── docs/                   # Documentation and guides
```

## 🔌 API Overview

- Profiles: /api/v1/profiles via [profile_endpoints.router](api/profile_endpoints.py:400)
- Containers: /api/v1/containers via [container_endpoints.router](api/container_endpoints.py:114)
- Scenarios: /api/scenarios via [scenario_endpoints.router](api/scenario_endpoints.py:56)
- Sandbox: /api/sandbox via [sandbox_endpoints.router](api/sandbox_endpoints.py:19)
- LLM/Analytics (Flask blueprint): /api/llm via [llm_bp](api/llm_endpoints.py:19)
- Diagrams: [docs/API_INTERACTIONS.md](docs/API_INTERACTIONS.md:1)

## 🧭 Profiles API Quick Reference

Endpoints:
- GET /api/v1/profiles → list
- GET /api/v1/profiles/{id} → get
- POST /api/v1/profiles → create
- PUT /api/v1/profiles/{id} → update
- DELETE /api/v1/profiles/{id} → delete
- POST /api/v1/profiles/{id}/activate → activate
- POST /api/v1/profiles/{id}/deactivate → deactivate
- POST /api/v1/profiles/validate → validate
- GET /api/v1/profiles/search?q=... → search

Examples:

- Create:
```bash
curl -X POST http://localhost:8000/api/v1/profiles \
  -H "Content-Type: application/json" \
  -d '{"name":"Agent Zero","type":"red_team","description":"Recon","skill_level":"beginner","specialization":"OSINT","configuration":{"notes":"demo"}}'
```

- List:
```bash
curl http://localhost:8000/api/v1/profiles
```

- Activate:
```bash
curl -X POST http://localhost:8000/api/v1/profiles/PROFILE_ID/activate
```

- Search:
```bash
curl "http://localhost:8000/api/v1/profiles/search?q=agent"
```

Storage note: Profiles persist under profiles/ as JSON; implemented in [api/profile_endpoints.py](api/profile_endpoints.py:1).

## 🛠️ Installation

> **📦 RECOMMENDED: Use Docker for deployment** - Docker handles all system dependencies automatically, including portaudio19-dev for audio processing. See the [Docker Setup](#-docker-setup) section below for the easiest installation method.

### Prerequisites

- Python 3.8 or higher
- pip package manager
- **System dependencies** (for local installation):
  - Ubuntu/Debian: `portaudio19-dev`, `python3-pyaudio`, `espeak`
  - Other platforms: equivalent audio and speech synthesis libraries
- **Recommended**: Docker and Docker Compose for containerized deployment

### Local Installation

> ⚠️ **Warning**: Local installation requires manual installation of system dependencies. System dependencies (like portaudio19-dev) must be installed separately before pip dependencies.

1. **Install system dependencies** (Ubuntu/Debian)
   ```bash
   sudo apt-get update
   sudo apt-get install portaudio19-dev python3-pyaudio espeak
   ```

2. **Clone the repository**
   ```bash
   git clone https://github.com/atsmafia/framework.git
   cd ats_mafia_framework
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install the framework**
   ```bash
   pip install -e .
   ```

5. **Verify installation**
   ```bash
   python -c "import ats_mafia_framework; print('Installation successful!')"
   ```

## 🐳 Docker Setup

Docker is the **recommended deployment method** as it handles all system dependencies automatically, including portaudio19-dev for pyaudio and other audio processing requirements.

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) (20.10 or higher)
- [Docker Compose](https://docs.docker.com/compose/install/) (2.0 or higher)

### Deployment Options

The framework provides three Docker Compose configurations:

1. **Full Framework Deployment** ([`docker-compose.yml`](docker-compose.yml)) - Complete deployment with all services
2. **Personal Assistant Only** ([`docker-compose.personal-assistant.yml`](docker-compose.personal-assistant.yml)) - Standalone Personal Assistant feature
3. **Development Environment** ([`docker-compose.dev.yml`](docker-compose.dev.yml)) - Hot reload and debugging tools

---

## 📦 Full Framework Deployment

Deploy the complete ATS MAFIA Framework with all services including API, UI, database, Redis, WebSocket server, and optional Kali sandbox.

### Services Included

| Service | Port | Description |
|---------|------|-------------|
| **ats-mafia-api** | 8000 | Main FastAPI server with container orchestration |
| **ats-mafia-websocket** | 8080 | WebSocket server for real-time communication |
| **ats-mafia-ui** | 8501 | Streamlit web dashboard |
| **postgres** | 5432 | PostgreSQL database for persistent data |
| **redis** | 6379 | Redis cache and message broker |
| **personal-assistant** | 5000 | Personal Assistant webhook server |
| **kali-sandbox** | - | Kali Linux container for security tools (optional) |

### Quick Start - Full Framework

1. **Clone and configure**
   ```bash
   git clone https://github.com/atsmafia/framework.git
   cd ats_mafia_framework
   
   # Copy and edit environment file
   cp .env.example .env
   # Edit .env: Set DATABASE_PASSWORD, REDIS_PASSWORD, FRAMEWORK_ENV
   ```

2. **Start all services**
   ```bash
   # Start core services (default - WITHOUT Kali sandbox)
   docker-compose up -d
   
   # Start with Kali sandbox included
   docker-compose --profile full up -d
   # OR
   docker-compose --profile sandbox up -d
   ```

3. **Access services**
   - **Main API**: http://localhost:8000 - API documentation at `/docs`
   - **Web UI Dashboard**: http://localhost:8501 - Streamlit interface
   - **WebSocket**: ws://localhost:8080 - Real-time communication
   - **Personal Assistant**: http://localhost:5000 - Phone webhook server
   - **PostgreSQL**: localhost:5432 (user: `ats_user`, db: `ats_mafia`)
   - **Redis**: localhost:6379

4. **View logs and status**
   ```bash
   # View all services
   docker-compose ps
   
   # View logs
   docker-compose logs -f
   
   # View specific service logs
   docker-compose logs -f ats-mafia-api
   ```

5. **Stop services**
   ```bash
   # Stop all services
   docker-compose down
   
   # Stop and remove volumes (deletes all data)
   docker-compose down -v
   ```

### Scaling Services

Scale specific services for higher load:

```bash
# Scale API servers
docker-compose up -d --scale ats-mafia-api=3

# Scale WebSocket servers
docker-compose up -d --scale ats-mafia-websocket=2
```

---

## 🎯 Personal Assistant Only Deployment

Deploy just the Personal Assistant feature for phone integration without the full framework.

### Quick Start - Personal Assistant

```bash
# 1. Configure environment
cp .env.personal-assistant.example .env

# 2. Edit .env with your phone provider settings
# - Set PHONE_PROVIDER (mock/twilio/plivo)
# - Add provider credentials if using Twilio or Plivo

# 3. Start Personal Assistant
docker-compose -f docker-compose.personal-assistant.yml up -d

# 4. Access at http://localhost:5000
# 5. View logs
docker-compose -f docker-compose.personal-assistant.yml logs -f
```

**Services**: Single container with API server, webhook handler, and voice processing.

**Use Case**: Ideal for users who only need the Personal Assistant phone integration feature.

---

## 🛠️ Development Environment

Development deployment with hot reload, debug features, and development tools.

### Features

- ✅ Hot reload for code changes
- ✅ Debug ports exposed (port 5678 for debugpy)
- ✅ Verbose logging (DEBUG level)
- ✅ Code mounted as volumes for live editing
- ✅ Separate dev database and Redis instances
- ✅ Mock phone provider for testing
- ✅ Reduced resource limits
- ✅ Optional dev-tools container

### Quick Start - Development

```bash
# 1. Start development environment
docker-compose -f docker-compose.dev.yml up

# 2. Code changes will auto-reload
# 3. Access services:
#    - API: http://localhost:8000
#    - UI: http://localhost:8501
#    - WebSocket: ws://localhost:8080
#    - PostgreSQL: localhost:5433
#    - Redis: localhost:6380

# 4. Stop with Ctrl+C or:
docker-compose -f docker-compose.dev.yml down
```

### Development with Tools Container

```bash
# Start with dev-tools container
docker-compose -f docker-compose.dev.yml --profile tools up -d

# Access dev-tools container
docker exec -it ats-mafia-dev-tools bash

# Run tests, linting, etc. from within the container
cd /workspace
pytest
```

---

## 🔧 Docker Management Commands

### Common Operations

```bash
# View running containers
docker-compose ps

# View logs
docker-compose logs -f [service_name]

# Restart specific service
docker-compose restart ats-mafia-api

# Rebuild after code changes
docker-compose up -d --build

# Execute commands in container
docker-compose exec ats-mafia-api bash

# View resource usage
docker stats

# Clean up unused resources
docker system prune -a
```

### Kali Sandbox Management

The Kali Linux sandbox is **optional** and uses Docker profiles to prevent automatic startup (it's a large image with security tools). By default, `docker-compose up -d` starts all services **except** Kali.

**Starting Services with Kali Sandbox:**

```bash
# Start ALL services including Kali sandbox (full profile)
docker-compose --profile full up -d

# Start with sandbox profile (includes Kali)
docker-compose --profile sandbox up -d

# Start Kali sandbox only (after other services are running)
docker-compose up -d kali-sandbox
```

**Why is Kali Optional?**
- Large Docker image (2GB+) with pre-installed security tools
- Resource-intensive (4GB RAM limit)
- Only needed for advanced penetration testing scenarios
- Contains tools like nmap, Metasploit, sqlmap, hydra, nikto

**Managing Kali Sandbox:**

```bash
# Check if Kali is running
docker-compose ps kali-sandbox

# View Kali sandbox logs
docker-compose logs -f kali-sandbox

# Access Kali sandbox shell
docker-compose exec kali-sandbox bash

# Stop Kali sandbox only
docker-compose stop kali-sandbox

# Remove Kali sandbox
docker-compose rm -f kali-sandbox

# Restart all services WITHOUT Kali
docker-compose down
docker-compose up -d
```

### Health Checks

```bash
# Check service health
docker-compose ps

# Check specific service health
docker inspect --format='{{.State.Health.Status}}' ats-mafia-api

# View health check logs
docker inspect ats-mafia-api | grep -A 10 Health
```

### Database Operations

```bash
# Access PostgreSQL
docker-compose exec postgres psql -U ats_user -d ats_mafia

# Backup database
docker-compose exec postgres pg_dump -U ats_user ats_mafia > backup.sql

# Restore database
docker-compose exec -T postgres psql -U ats_user ats_mafia < backup.sql

# Access Redis CLI
docker-compose exec redis redis-cli -a your_redis_password
```

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     ATS MAFIA FRAMEWORK                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   Web UI     │    │  WebSocket   │    │ Personal     │      │
│  │  Dashboard   │───▶│   Server     │◀───│ Assistant    │      │
│  │  (Port 8501) │    │ (Port 8080)  │    │ (Port 5000)  │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                    │                    │              │
│         └────────────────────┼────────────────────┘              │
│                              ▼                                   │
│                    ┌──────────────────┐                          │
│                    │   Main API       │                          │
│                    │   Server         │                          │
│                    │  (Port 8000)     │                          │
│                    └──────────────────┘                          │
│                         │         │                              │
│              ┌──────────┘         └──────────┐                  │
│              ▼                                ▼                  │
│     ┌─────────────────┐              ┌─────────────┐            │
│     │   PostgreSQL    │              │    Redis    │            │
│     │   Database      │              │    Cache    │            │
│     │  (Port 5432)    │              │ (Port 6379) │            │
│     └─────────────────┘              └─────────────┘            │
│                                                                   │
│     ┌────────────────────────────────────────────┐              │
│     │         Kali Sandbox (Optional)            │              │
│     │         Security Tools Container           │              │
│     └────────────────────────────────────────────┘              │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Users** access the Web UI Dashboard (port 8501)
2. **UI** communicates with API Server (port 8000) for data operations
3. **WebSocket Server** (port 8080) provides real-time updates to UI
4. **Personal Assistant** (port 5000) handles phone calls via webhooks
5. **PostgreSQL** stores persistent data (sessions, profiles, analytics)
6. **Redis** provides caching and pub/sub messaging
7. **Kali Sandbox** executes security tools in isolated environment

---

## 🚀 Docker Advantages

✅ **No manual system dependency installation** - Docker image includes portaudio19-dev, espeak, and all required libraries
✅ **Consistent environment** - Same setup across development, staging, and production
✅ **Easy updates** - Simply rebuild the image to apply changes
✅ **Isolated execution** - Framework runs in its own container environment
✅ **Resource management** - Built-in resource limits and monitoring
✅ **Microservices architecture** - Each component runs independently
✅ **Easy scaling** - Scale individual services as needed
✅ **Data persistence** - Volumes preserve data across restarts

## 🚀 Quick Start

### Quick Start with Docker (Recommended)

The fastest way to get started with the ATS MAFIA Framework:

**Option 1: Full Framework (All Services)**
```bash
# 1. Clone and configure
git clone https://github.com/atsmafia/framework.git
cd ats_mafia_framework
cp .env.example .env
# Edit .env: Set DATABASE_PASSWORD, REDIS_PASSWORD

# 2. Start core services (WITHOUT Kali sandbox)
docker-compose up -d

# 2a. OR start with Kali sandbox
docker-compose --profile full up -d

# 3. Access services
# - Main API: http://localhost:8000/docs
# - Web UI: http://localhost:8501
# - WebSocket: ws://localhost:8080
# - Personal Assistant: http://localhost:5000
```

**Option 2: Personal Assistant Only**
```bash
# 1. Configure
cp .env.personal-assistant.example .env
# Edit .env with phone provider settings

# 2. Start Personal Assistant
docker-compose -f docker-compose.personal-assistant.yml up -d

# 3. Access at http://localhost:5000
```

**Option 3: Development Environment**
```bash
# Start with hot reload and debugging
docker-compose -f docker-compose.dev.yml up
```

That's it! The framework is now running with all dependencies configured.

For more detailed instructions, see the [Docker Setup](#-docker-setup) section above.

### Create Your First Agent (Profile)

- Run backend (Docker): `docker-compose up` to expose http://localhost:8000.
- Open [ui/index.html](ui/index.html:1), then use the top menu "Profiles" or Dashboard Quick Action "Launch Profile" to open [ui/profiles.html](ui/profiles.html:1).
- On [ui/profiles.html](ui/profiles.html:1), click "Create Profile", fill in the fields, and submit to create an agent.

Base URL defaults and overrides:
- Client default base: [ATSAPIClient()](ui/js/api-client.js:6) = "/api/v1".
- Runtime override: [ATSApplication.loadConfiguration()](ui/js/main.js:64) sets [window.atsAPI.baseURL](ui/js/main.js:84) from [ATSApplication.config.apiBaseURL](ui/js/main.js:11).
- Development default: http://localhost:8000/api/v1.

### Basic Usage

```python
import asyncio
from ats_mafia_framework import (
    FrameworkConfig,
    TrainingOrchestrator,
    ProfileManager,
    ToolRegistry,
    CommunicationProtocol,
    AuditLogger
)

async def main():
    # Initialize configuration
    config = FrameworkConfig.from_file("config/default.yaml")
    
    # Initialize core components
    audit_logger = AuditLogger(config)
    profile_manager = ProfileManager(config, audit_logger)
    tool_registry = ToolRegistry(config)
    communication = CommunicationProtocol("main_agent", config, audit_logger)
    
    # Initialize orchestrator
    orchestrator = TrainingOrchestrator(
        config, profile_manager, tool_registry, communication, audit_logger
    )
    
    # Start communication server
    await communication.start_server()
    
    # List available scenarios
    scenarios = orchestrator.list_scenarios()
    print(f"Available scenarios: {len(scenarios)}")
    
    # Create a training session
    session_id = await orchestrator.create_session(
        name="Basic Penetration Test",
        description="Introduction to network penetration testing",
        scenario_id="basic_penetration_test",
        agent_configs=[
            {
                "profile_id": "red_team_operator",
                "role": "attacker"
            }
        ]
    )
    
    if session_id:
        print(f"Created session: {session_id}")
        
        # Start the session
        await orchestrator.start_session(session_id)
        
        # Monitor session progress
        session = orchestrator.get_session(session_id)
        print(f"Session status: {session.status}")
    
    # Cleanup
    await communication.stop_server()

if __name__ == "__main__":
    asyncio.run(main())
```

### Command Line Interface

```bash
# List available profiles
ats-mafia profile list

# List available scenarios
ats-mafia scenario list

# Start a training session
ats-mafia orchestrator start --scenario basic_penetration_test --profile red_team_operator

# View session status
ats-mafia orchestrator status --session <session_id>
```

## 📊 Configuration

The framework uses a hierarchical configuration system with YAML/JSON support. Key configuration areas:

### Core Settings
```yaml
core:
  max_concurrent_agents: 10
  session_timeout: 3600
  checkpoint_interval: 300
  recovery_enabled: true
```

### Logging Configuration
```yaml
logging:
  level: "INFO"
  file_path: "logs/ats_mafia.log"
  audit_enabled: true
  audit_file_path: "logs/audit.log"
```

### Communication Settings
```yaml
communication:
  protocol: "websocket"
  host: "localhost"
  port: 8080
  ssl_enabled: false
  max_connections: 100
```

### UI/API Base URL Configuration

- Default client base in [ATSAPIClient()](ui/js/api-client.js:6) is "/api/v1".
- Runtime override from [ATSApplication.config.apiBaseURL](ui/js/main.js:11) is applied in [ATSApplication.loadConfiguration()](ui/js/main.js:64), which updates [window.atsAPI.baseURL](ui/js/main.js:84).
- Set base URL via localStorage for development:
```js
localStorage.setItem('ats_config', JSON.stringify({ apiBaseURL: 'http://localhost:8000/api/v1' }));
location.reload();
```
- WebSocket configuration note remains unchanged.

## 🔧 Customization

### Creating Custom Profiles

```python
from ats_mafia_framework.core.profile_manager import (
    AgentProfile, ProfileMetadata, Capability, PersonalityTrait
)

# Create a custom profile
profile = AgentProfile(
    metadata=ProfileMetadata(
        id="custom_analyst",
        name="Security Analyst",
        description="Specialized security analyst profile",
        version="1.0.0",
        author="Your Team",
        profile_type=ProfileType.BLUE_TEAM
    ),
    capabilities=[
        Capability(
            name="threat_analysis",
            description="Advanced threat analysis capabilities",
            skill_level=SkillLevel.ADVANCED
        )
    ],
    personality=[
        PersonalityTrait(
            trait="analytical_thinking",
            value=0.9,
            description="Strong analytical thinking skills"
        )
    ]
)
```

### Creating Custom Tools

```python
from ats_mafia_framework.core.tool_system import Tool, ToolMetadata, ToolType

class CustomTool(Tool):
    def __init__(self):
        metadata = ToolMetadata(
            id="custom_tool",
            name="Custom Analysis Tool",
            description="Custom security analysis tool",
            tool_type=ToolType.PYTHON
        )
        super().__init__(metadata)
    
    async def execute(self, parameters, context):
        # Tool implementation here
        return ToolExecutionResult(
            tool_id=self.metadata.id,
            success=True,
            result={"analysis": "completed"}
        )
```

### Creating Custom Scenarios

```python
from ats_mafia_framework.core.orchestrator import (
    ScenarioConfig, ScenarioType, ScenarioRunner
)

class CustomScenarioRunner(ScenarioRunner):
    async def execute(self, session):
        # Custom scenario logic here
        return {"success": True, "score": 85}
```

## 🗺️ Diagrams

See [docs/API_INTERACTIONS.md](docs/API_INTERACTIONS.md:1) for Mermaid architecture and sequence diagrams, including:
- Create Profile
- List Profiles
- Container Status
- LLM Models

## 📚 Documentation

### Core Documentation

- [Personal Assistant Docker Guide](docs/PERSONAL_ASSISTANT_DOCKER_GUIDE.md) - Complete Docker deployment guide for Personal Assistant
- [Personal Assistant Phone Provider Guide](docs/PERSONAL_ASSISTANT_PHONE_PROVIDER_GUIDE.md) - Configure Twilio, Plivo, or mock phone providers
- [Phase 4 Analytics README](docs/PHASE4_ANALYTICS_README.md) - Analytics and attack tracking features

### Configuration

- [`.env.example`](.env.example) - Complete environment configuration reference with all available variables
- [`config/default.yaml`](config/default.yaml) - Default YAML configuration file
- [Configuration Guide](docs/configuration.md) - Detailed configuration options

### Additional Resources

- [User Guide](docs/user_guide.md) - Comprehensive user documentation
- [API Reference](docs/api_reference.md) - Complete API documentation
- [Developer Guide](docs/developer_guide.md) - Development and extension guide
- [Knowledge Base README](knowledge/README.md) - Attack framework and knowledge base
- [Sandbox README](sandbox/README.md) - Container and sandbox management
- [Tools README](tools/README.md) - Tool system and extensions

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/test_core.py
pytest tests/test_profiles.py
pytest tests/test_scenarios.py

# Run with coverage
pytest --cov=ats_mafia_framework
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Install development dependencies:
   ```bash
   pip install -e .[dev]
   ```
4. Make your changes
5. Run tests and ensure they pass
6. Submit a pull request

## 📄 License

This project is licensed under the ATS MAFIA Proprietary License. See the [LICENSE](LICENSE) file for details.

## 🔧 Troubleshooting

### Common Issues

**Issue: `ModuleNotFoundError: No module named 'docker'`**
```bash
# Solution: Install docker Python module
pip install docker
```

**Issue: PyAudio installation fails with "portaudio.h not found"**
```bash
# Solution 1 (Recommended): Use Docker - it includes all system dependencies
docker-compose -f docker-compose.personal-assistant.yml up -d

# Solution 2 (Local): Install system dependencies first
# Ubuntu/Debian:
sudo apt-get install portaudio19-dev python3-pyaudio espeak
pip install pyaudio

# macOS:
brew install portaudio
pip install pyaudio
```

**Issue: Container fails to start**
```bash
# Check container logs
docker logs ats-mafia-personal-assistant

# Check container status
docker-compose -f docker-compose.personal-assistant.yml ps

# Rebuild the container
docker-compose -f docker-compose.personal-assistant.yml up -d --build
```

**Issue: Port already in use (5000, 8080, or 8501)**
```bash
# Find what's using the port (example for port 5000)
# Linux/Mac:
lsof -i :5000
# Windows:
netstat -ano | findstr :5000

# Either stop the conflicting service or change ports in .env file:
# API_PORT=5001
# COMMUNICATION_PORT=8081
# UI_PORT=8502
```

**Issue: Changes not reflected after code update**
```bash
# Rebuild Docker containers after code changes
docker-compose -f docker-compose.personal-assistant.yml up -d --build

# For local installation, reinstall the package
pip install -e .
```

**Issue: Permission denied when running Docker commands**
```bash
# Linux: Add user to docker group
sudo usermod -aG docker $USER
# Log out and back in for changes to take effect

# Or run with sudo (not recommended for regular use)
sudo docker-compose -f docker-compose.personal-assistant.yml up -d
```

**Issue: Container health check failures**
```bash
# Check container health
docker inspect --format='{{.State.Health.Status}}' ats-mafia-personal-assistant

# View detailed health check logs
docker inspect ats-mafia-personal-assistant | grep -A 10 Health

# Restart unhealthy containers
docker-compose -f docker-compose.personal-assistant.yml restart
```

### UI/API Integration Issues

- 404 on /api/v1/profiles:
  - Ensure the backend is running and the profiles router is mounted in [api/container_app_example.py](api/container_app_example.py:1).
- CORS/preflight errors:
  - Development CORS is enabled in [api/container_app_example.py](api/container_app_example.py:1). If running a different app, enable FastAPI CORSMiddleware similarly.
- Base URL mismatch:
  - Confirm [ATSApplication.config.apiBaseURL](ui/js/main.js:11) or the localStorage override matches http://localhost:8000/api/v1.
- UI “Launch Profile” button:
  - This opens [ui/profiles.html](ui/profiles.html:1) to create agents (temporary SPA redirect).

### Getting Help

If you encounter issues not covered here:

1. Check the logs: `docker logs ats-mafia-personal-assistant` or `logs/ats_mafia.log`
2. Review the [documentation](docs/) for your specific feature
3. Search [GitHub Issues](https://github.com/atsmafia/framework/issues)
4. Open a new issue with:
   - Error messages and logs
   - Steps to reproduce
   - Environment details (OS, Docker version, Python version)

## 🆘 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/atsmafia/framework/issues)
- **Discussions**: [GitHub Discussions](https://github.com/atsmafia/framework/discussions)
- **Email**: support@atsmafia.com

## 🗺️ Roadmap

### Version 1.1.0 (Planned)
- Enhanced UI dashboard
- Additional tool integrations
- Performance optimizations
- Extended scenario library

### Version 1.2.0 (Planned)
- Machine learning integration
- Advanced analytics
- Cloud deployment options
- Multi-language support

## 🏆 Acknowledgments

- The ATS MAFIA development team
- Contributors from the security community
- Open source projects that make this framework possible

## 📈 Metrics

- **Framework Version**: 1.0.0
- **Python Support**: 3.8+
- **Supported Platforms**: Windows, Linux, macOS
- **License**: Proprietary

---

**ATS MAFIA Framework** - *Advanced Training System for Multi-Agent Interactive Framework*

*Empowering the next generation of cybersecurity professionals through intelligent training simulations.*
---
## Enabling the Kali Sandbox via Docker Compose Profiles

Kali is an optional service gated behind Docker Compose profiles so the default stack stays lean. The Kali service declares its profiles in [docker-compose.yml](docker-compose.yml:525-528). By default, it is not started unless you enable one of the profiles it belongs to (full or sandbox).

Start Kali on demand
- Windows cmd.exe:
  - set "COMPOSE_PROFILES=full" &amp;&amp; docker compose up -d kali-sandbox
- Windows PowerShell:
  - $env:COMPOSE_PROFILES = "full"; docker compose up -d kali-sandbox
- Linux/macOS bash/zsh:
  - COMPOSE_PROFILES=full docker compose up -d kali-sandbox
- Cross-shell alternative (no env var needed):
  - docker compose --profile full up -d kali-sandbox

Start the full framework with Kali enabled
- Windows cmd.exe:
  - set "COMPOSE_PROFILES=full" &amp;&amp; docker compose up -d
- Windows PowerShell:
  - $env:COMPOSE_PROFILES = "full"; docker compose up -d
- Linux/macOS:
  - COMPOSE_PROFILES=full docker compose up -d
- Alternative:
  - docker compose --profile full up -d

Make Kali start by default on every run
- Place the following line into a .env file at the repository root:
  - COMPOSE_PROFILES=full
- Then run:
  - docker compose up -d
Notes:
- Docker Compose automatically reads .env in the project root and honors COMPOSE_PROFILES for profile activation.
- To set a persistent Windows user environment variable instead of .env:
  - setx COMPOSE_PROFILES full
  - Open a new terminal for it to take effect.

Verify that Kali is running
- docker compose ps kali-sandbox
  - Expect “Up” (no Healthy state is defined for Kali). First boot may be slow due to tool installation inside the container.

Troubleshooting: Kali restarts in a loop
- If you see Restarting (100), check logs:
  - docker compose logs --tail=100 kali-sandbox
- The Kali service is hardened with capability drops and no-new-privileges as defined in [docker-compose.yml](docker-compose.yml:501-509). On some hosts, apt-get may fail due to blocked privilege transitions, causing restarts.
- Options:
  1) Re-run the start command; transient apt mirror issues can resolve on retry.
  2) Temporarily relax the hardening in your local copy of [docker-compose.yml](docker-compose.yml:501-509) and re-up if your environment blocks apt’s privilege changes.
  3) Build a custom Kali image that pre-installs tools and uses a simpler CMD, then reference it in an override compose file.

Conceptual model recap
- Services without profiles are always included in the default stack.
- Services with profiles (like Kali in [docker-compose.yml](docker-compose.yml:482-528)) are included only when a matching profile is activated via COMPOSE_PROFILES or --profile.
---