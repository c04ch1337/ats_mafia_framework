# ATS MAFIA Framework - Tool Catalog

This document provides comprehensive documentation for all tools in the ATS MAFIA Framework. All tools operate in **SIMULATION MODE ONLY** for training and educational purposes.

## Table of Contents

- [Overview](#overview)
- [RED TEAM Tools](#red-team-tools)
- [BLUE TEAM Tools](#blue-team-tools)
- [SOCIAL ENGINEERING Tools](#social-engineering-tools)
- [UTILITY Tools](#utility-tools)
- [Safety & Ethics](#safety--ethics)
- [Usage Examples](#usage-examples)

## Overview

The ATS MAFIA Framework includes 21 specialized tools across 4 categories:
- **RED TEAM**: 8 offensive security tools
- **BLUE TEAM**: 7 defensive security tools
- **SOCIAL ENGINEERING**: 3 social engineering tools
- **UTILITIES**: 3 utility and support tools

### Tool Categories

- **RECONNAISSANCE**: Information gathering and target profiling
- **EXPLOITATION**: Simulated vulnerability exploitation
- **POST_EXPLOITATION**: Persistence, privilege escalation, data exfiltration
- **EVASION**: Detection evasion and anti-forensics
- **DEFENSE**: Security hardening and vulnerability scanning
- **MONITORING**: Network and system monitoring
- **INVESTIGATION**: Forensics and threat hunting
- **RESPONSE**: Incident response automation
- **SOCIAL_ENGINEERING**: Human-factor attack simulation
- **UTILITIES**: Supporting tools and reporting

### Risk Levels

- **SAFE**: No risk, read-only operations
- **LOW_RISK**: Minimal risk, limited scope
- **MEDIUM_RISK**: Moderate risk, requires oversight
- **HIGH_RISK**: Significant risk, requires authorization
- **CRITICAL**: Maximum risk, requires explicit approval

---

## RED TEAM Tools

### 1. Stealth Scanner

**ID**: `stealth_scanner`  
**Category**: RECONNAISSANCE  
**Risk Level**: MEDIUM_RISK

Advanced port and service scanning with evasion techniques.

**Features**:
- TCP SYN scanning simulation
- UDP scanning simulation
- Service version detection
- Timing controls (paranoid, sneaky, polite, normal, aggressive)
- Decoy IP generation
- Fragmented packet simulation

**Parameters**:
```json
{
  "target": "192.168.1.0/24",
  "scan_type": "syn",
  "ports": "1-1000",
  "timing": "sneaky",
  "use_decoys": true,
  "fragment_packets": false
}
```

**Example Output**:
```json
{
  "open_ports": [22, 80, 443],
  "services_detected": {"22": "ssh", "80": "http", "443": "https"},
  "evasion_techniques_used": ["SYN scan", "Decoy IPs", "Timing: sneaky"],
  "estimated_detection_probability": 0.35
}
```

---

### 2. OSINT Collector

**ID**: `osint_collector`  
**Category**: RECONNAISSANCE  
**Risk Level**: LOW_RISK

Open-source intelligence gathering for target profiling.

**Features**:
- Domain enumeration
- Subdomain discovery
- Email harvesting (simulated)
- Social media reconnaissance
- Technology stack identification
- Credential leak checking

**Parameters**:
```json
{
  "target": "example.com",
  "depth": "standard",
  "include_subdomains": true,
  "check_breaches": true,
  "social_media": true
}
```

---

### 3. Vulnerability Exploiter

**ID**: `vulnerability_exploiter`  
**Category**: EXPLOITATION  
**Risk Level**: CRITICAL

Simulated exploitation framework with CVE-based exploit selection.

**Features**:
- CVE-based exploit selection
- Payload generation simulation
- Success probability calculation
- Sandbox execution (no actual exploitation)

**Parameters**:
```json
{
  "target": "192.168.1.100",
  "vulnerability": "buffer_overflow",
  "exploit_type": "remote",
  "payload": "reverse_shell",
  "stealth_mode": false
}
```

---

### 4. Persistence Installer

**ID**: `persistence_installer`  
**Category**: POST_EXPLOITATION  
**Risk Level**: HIGH_RISK

Simulates establishing persistent access mechanisms.

**Features**:
- Registry key manipulation (simulated)
- Scheduled task creation (simulated)
- Service installation (simulated)
- Backdoor deployment techniques

**Parameters**:
```json
{
  "target": "WORKSTATION-01",
  "mechanism": "scheduled_task",
  "stealth_level": "medium"
}
```

---

### 5. Data Exfiltrator

**ID**: `data_exfiltrator`  
**Category**: POST_EXPLOITATION  
**Risk Level**: HIGH_RISK

Simulates data extraction and exfiltration techniques.

**Features**:
- File discovery and classification
- Data compression and encryption
- Covert channel selection (DNS, HTTPS, ICMP)
- Bandwidth throttling simulation

**Parameters**:
```json
{
  "target": "FILE-SERVER-01",
  "data_type": "documents",
  "channel": "https",
  "compress": true,
  "encrypt": true,
  "throttle_mbps": 1.0
}
```

---

### 6. Privilege Escalator

**ID**: `privilege_escalator`  
**Category**: POST_EXPLOITATION  
**Risk Level**: HIGH_RISK

Simulates privilege escalation techniques.

**Features**:
- Vulnerability scanning for privilege escalation
- Exploitation path recommendation
- Credential harvesting simulation
- Token manipulation

**Parameters**:
```json
{
  "target": "WORKSTATION-02",
  "current_level": "user",
  "target_level": "admin",
  "technique": "service_misconfiguration"
}
```

---

### 7. Anti-Forensics

**ID**: `anti_forensics`  
**Category**: EVASION  
**Risk Level**: HIGH_RISK

Simulates techniques for covering tracks and evading forensic analysis.

**Features**:
- Log deletion/modification (simulated)
- Timestamp manipulation (simulated)
- Memory scrubbing (simulated)
- Artifact removal (simulated)

**Parameters**:
```json
{
  "target": "COMPROMISED-HOST",
  "operations": ["clear_logs", "modify_timestamps", "remove_artifacts"],
  "aggressiveness": "moderate"
}
```

---

### 8. Payload Obfuscator

**ID**: `payload_obfuscator`  
**Category**: EVASION  
**Risk Level**: MEDIUM_RISK

Simulates payload obfuscation for detection evasion.

**Features**:
- Code obfuscation techniques
- Polymorphic payload generation
- AV evasion scoring
- Multiple encoding methods

**Parameters**:
```json
{
  "payload": "test_payload",
  "techniques": ["base64", "xor", "polymorphic"],
  "obfuscation_level": "medium",
  "preserve_functionality": true
}
```

---

## BLUE TEAM Tools

### 9. Network Monitor

**ID**: `network_monitor`  
**Category**: MONITORING  
**Risk Level**: SAFE

Real-time network surveillance and anomaly detection.

**Features**:
- Traffic analysis and anomaly detection
- Protocol analysis
- Intrusion detection
- Bandwidth monitoring

**Parameters**:
```json
{
  "interface": "eth0",
  "duration": 60,
  "alert_threshold": 0.8,
  "protocols": ["tcp", "udp", "icmp"]
}
```

---

### 10. Log Analyzer

**ID**: `log_analyzer`  
**Category**: INVESTIGATION  
**Risk Level**: SAFE

Multi-source log correlation and security event detection.

**Features**:
- Multi-source log aggregation
- Pattern matching for IOCs
- Timeline reconstruction
- Anomaly detection

**Parameters**:
```json
{
  "log_sources": ["windows_events", "syslog", "firewall"],
  "time_range_hours": 24
}
```

---

### 11. Forensic Analyzer

**ID**: `forensic_analyzer`  
**Category**: FORENSICS  
**Risk Level**: SAFE

Digital forensics and artifact analysis.

**Features**:
- Disk image analysis (simulated)
- Memory forensics (simulated)
- File carving and recovery
- Artifact timeline generation

**Parameters**:
```json
{
  "target": "evidence.img",
  "analysis_type": "disk"
}
```

---

### 12. Threat Hunter

**ID**: `threat_hunter`  
**Category**: INVESTIGATION  
**Risk Level**: SAFE

Proactive threat hunting using MITRE ATT&CK techniques.

**Features**:
- IOC searching across systems
- Behavior pattern analysis
- APT technique detection (MITRE ATT&CK)
- Lateral movement detection

**Parameters**:
```json
{
  "target": "NETWORK-SEGMENT-A"
}
```

---

### 13. Vulnerability Scanner

**ID**: `vulnerability_scanner`  
**Category**: DEFENSE  
**Risk Level**: SAFE

Security assessment and vulnerability scanning.

**Features**:
- Port scanning
- Service enumeration
- CVE matching
- Configuration analysis

**Parameters**:
```json
{
  "target": "webserver.local"
}
```

---

### 14. Security Hardener

**ID**: `security_hardener`  
**Category**: DEFENSE  
**Risk Level**: LOW_RISK

System hardening and security configuration.

**Features**:
- Configuration audit
- CIS benchmark compliance
- Hardening recommendations
- Patch management simulation

**Parameters**:
```json
{
  "target": "SERVER-01"
}
```

---

### 15. Incident Responder

**ID**: `incident_responder`  
**Category**: RESPONSE  
**Risk Level**: MEDIUM_RISK

Automated incident response and containment.

**Features**:
- Containment actions simulation
- Evidence collection
- Remediation steps
- Communication templates

**Parameters**:
```json
{
  "incident_type": "malware"
}
```

---

## SOCIAL ENGINEERING Tools

### 16. Pretext Generator

**ID**: `pretext_generator`  
**Category**: SOCIAL_ENGINEERING  
**Risk Level**: MEDIUM_RISK

Creates believable pretexts for social engineering scenarios.

**Features**:
- Role-based pretext templates
- Background story generation
- Credential fabrication
- Organizational chart simulation

**Parameters**:
```json
{
  "scenario": "it_support"
}
```

---

### 17. Phishing Crafter

**ID**: `phishing_crafter`  
**Category**: SOCIAL_ENGINEERING  
**Risk Level**: MEDIUM_RISK

Email and message creation for phishing simulations.

**Features**:
- Template selection
- Target personalization
- Urgency/authority tactics
- Link obfuscation techniques

**Parameters**:
```json
{
  "template": "urgent_security"
}
```

---

### 18. Voice Modulator

**ID**: `voice_modulator`  
**Category**: SOCIAL_ENGINEERING  
**Risk Level**: LOW_RISK

Voice manipulation for vishing simulations.

**Features**:
- Voice parameter adjustment (pitch, speed, accent)
- Emotional tone control
- Background noise injection
- Integration with Puppet Master profile

**Parameters**:
```json
{
  "profile": "professional"
}
```

---

## UTILITY Tools

### 19. Report Generator

**ID**: `report_generator`  
**Category**: UTILITIES  
**Risk Level**: SAFE

Professional security assessment report creation.

**Features**:
- Multiple templates (pentest, incident response, audit)
- Executive summary generation
- Finding severity classification
- Remediation prioritization

**Parameters**:
```json
{
  "report_type": "pentest",
  "format": "pdf"
}
```

---

### 20. Credential Manager

**ID**: `credential_manager`  
**Category**: UTILITIES  
**Risk Level**: SAFE

Secure credential handling and password analysis.

**Features**:
- Encrypted credential storage simulation
- Password generation
- Hash cracking simulation
- Credential strength analysis

**Parameters**:
```json
{
  "operation": "analyze",
  "count": 10
}
```

---

### 21. Network Mapper

**ID**: `network_mapper`  
**Category**: UTILITIES  
**Risk Level**: SAFE

Network visualization and topology discovery.

**Features**:
- Topology discovery
- Asset inventory
- Network diagram generation
- Attack path visualization

**Parameters**:
```json
{
  "target_network": "192.168.0.0/16",
  "depth": 3
}
```

---

## Safety & Ethics

### CRITICAL SAFETY REQUIREMENTS

**ALL TOOLS MUST**:
- ✅ Operate in SIMULATION MODE ONLY
- ✅ Include safety controls and warnings
- ✅ Log all executions for audit trails
- ✅ Validate permissions before execution
- ✅ Include rate limiting where appropriate
- ✅ Respect tool restrictions per profile
- ✅ Provide clear disclaimers about training context

### Ethical Usage Guidelines

1. **Training Only**: All tools are for educational and training purposes
2. **No Actual Attacks**: No real exploitation or system modification
3. **Authorization Required**: Only use with explicit permission
4. **Audit Trails**: All executions are logged
5. **Responsible Disclosure**: Follow responsible disclosure practices

---

## Usage Examples

### Basic Tool Execution

```python
from ats_mafia_framework.core.tool_system import get_tool_registry

# Get tool registry
registry = get_tool_registry()

# Get a tool
tool = registry.get_tool('stealth_scanner')

# Execute tool
parameters = {
    'target': '192.168.1.0/24',
    'scan_type': 'syn',
    'timing': 'sneaky'
}

context = {
    'execution_id': 'demo-001',
    'permissions': ['read', 'execute'],
    'agent_id': 'shadow'
}

result = await registry.execute_tool(
    tool_id='stealth_scanner',
    parameters=parameters,
    context=context
)

print(f"Success: {result.success}")
print(f"Result: {result.result}")
```

### Tool Chaining

```python
from ats_mafia_framework.core.tool_system import ToolChaining

# Define chain
chain = [
    {
        'name': 'reconnaissance',
        'tool_id': 'osint_collector',
        'parameters': {'target': 'example.com', 'depth': 'standard'}
    },
    {
        'name': 'scanning',
        'tool_id': 'stealth_scanner',
        'parameters': {
            'target': '${reconnaissance.domain_info.ip_address}',
            'scan_type': 'comprehensive'
        }
    }
]

# Execute chain
chaining = ToolChaining(registry)
results = await chaining.execute_chain(chain, context)
```

### Validation

```python
from ats_mafia_framework.tools.validation import ToolValidator

validator = ToolValidator()

# Validate tool
is_valid, error = validator.validate_tool(tool)

if is_valid:
    print("Tool passed validation")
else:
    print(f"Validation failed: {error}")
```

---

## Additional Resources

- **Tool System Documentation**: See `core/tool_system.py`
- **Validation Framework**: See `tools/validation/tool_validator.py`
- **Testing Framework**: See `tools/validation/tool_tester.py`
- **API Documentation**: See `api/tool_endpoints.py`
- **CLI Documentation**: See `cli/tool_commands.py`

---

**Version**: 1.0.0  
**Last Updated**: 2024  
**Framework**: ATS MAFIA - Advanced Training System for Multi-Agent Intelligent Adversarial Framework Interaction Automation