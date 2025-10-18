# ATS MAFIA Framework

**Advanced Training System for Multi-Agent Interactive Framework**

A comprehensive framework for creating, managing, and training specialized agent profiles for various security scenarios including red team, blue team, and social engineering simulations.

## 🎯 Overview

ATS MAFIA Framework is a sophisticated multi-agent training system designed for cybersecurity education, penetration testing practice, and security team coordination. It provides a modular, extensible platform for creating realistic training scenarios with intelligent agents that can simulate various attack and defense techniques.

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

### Step-by-Step Docker Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/atsmafia/framework.git
   cd ats_mafia_framework
   ```

2. **Configure environment variables**
   ```bash
   # Copy the example environment file
   cp .env.example .env
   
   # Edit .env with your preferred settings
   # At minimum, configure:
   # - FRAMEWORK_ENV (development/production)
   # - LOG_LEVEL (INFO/DEBUG)
   # - PHONE_PROVIDER (mock/twilio/plivo)
   ```
   
   See the [`.env.example`](.env.example) file for all available configuration options.

3. **Build the Docker image**
   ```bash
   docker-compose -f docker-compose.personal-assistant.yml build
   ```

4. **Start the services**
   ```bash
   # Start in detached mode (background)
   docker-compose -f docker-compose.personal-assistant.yml up -d
   
   # Or start with logs visible (foreground)
   docker-compose -f docker-compose.personal-assistant.yml up
   ```

5. **Verify the services are running**
   ```bash
   docker-compose -f docker-compose.personal-assistant.yml ps
   ```

### Accessing Services

Once Docker containers are running, you can access:

- **API Server**: http://localhost:5000
- **WebSocket Server**: ws://localhost:8080
- **UI Dashboard**: http://localhost:8501

### Managing Docker Containers

**View logs:**
```bash
# View all logs
docker-compose -f docker-compose.personal-assistant.yml logs

# View logs for specific service
docker logs ats-mafia-personal-assistant

# Follow logs in real-time
docker logs -f ats-mafia-personal-assistant
```

**Stop containers:**
```bash
docker-compose -f docker-compose.personal-assistant.yml down
```

**Restart containers:**
```bash
docker-compose -f docker-compose.personal-assistant.yml restart
```

**Stop and remove all data:**
```bash
docker-compose -f docker-compose.personal-assistant.yml down -v
```

**Rebuild after code changes:**
```bash
docker-compose -f docker-compose.personal-assistant.yml up -d --build
```

### Docker Advantages

✅ **No manual system dependency installation** - Docker image includes portaudio19-dev, espeak, and all required libraries
✅ **Consistent environment** - Same setup across development, staging, and production
✅ **Easy updates** - Simply rebuild the image to apply changes
✅ **Isolated execution** - Framework runs in its own container environment
✅ **Resource management** - Built-in resource limits and monitoring

## 🚀 Quick Start

### Quick Start with Docker (Recommended)

The fastest way to get started with the ATS MAFIA Framework:

```bash
# 1. Copy and configure environment file
cp .env.example .env
# Edit .env with your settings (at minimum: FRAMEWORK_ENV, PHONE_PROVIDER)

# 2. Build and start services
docker-compose -f docker-compose.personal-assistant.yml up -d

# 3. View logs to confirm startup
docker logs -f ats-mafia-personal-assistant

# 4. Access the services
# - API: http://localhost:5000
# - WebSocket: ws://localhost:8080
# - UI: http://localhost:8501
```

That's it! The framework is now running with all dependencies configured.

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