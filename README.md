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

### Prerequisites

- Python 3.8 or higher
- pip package manager
- Optional: Docker for containerized deployment

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/atsmafia/framework.git
   cd ats_mafia_framework
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install the framework**
   ```bash
   pip install -e .
   ```

4. **Verify installation**
   ```bash
   python -c "import ats_mafia_framework; print('Installation successful!')"
   ```

## 🚀 Quick Start

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

- [User Guide](docs/user_guide.md) - Comprehensive user documentation
- [API Reference](docs/api_reference.md) - Complete API documentation
- [Developer Guide](docs/developer_guide.md) - Development and extension guide
- [Configuration Guide](docs/configuration.md) - Detailed configuration options

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