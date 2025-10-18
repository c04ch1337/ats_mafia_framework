# Kali Linux Sandbox Integration

## Overview

The Kali Linux Sandbox provides ATS MAFIA agents with access to **real security tools** running in isolated Docker containers. This transforms training from simulation to hands-on experience with actual penetration testing tools.

## Features

- ✅ **600+ Real Security Tools** - Access to full Kali Linux arsenal
- ✅ **Complete Isolation** - Sandboxed containers with network segmentation
- ✅ **Security Controls** - Command validation, rate limiting, breakout detection
- ✅ **Resource Management** - CPU/memory limits, automatic cleanup
- ✅ **Audit Logging** - Complete command history and security events
- ✅ **Snapshot Support** - Save and restore sandbox states
- ✅ **API Integration** - RESTful API for programmatic access

## Quick Start

### Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- 8GB RAM (minimum)
- 20GB disk space

### Launch Sandbox

```bash
# Start all services including Kali sandbox
docker-compose up -d

# Verify sandbox is running
docker ps | grep kali

# Check sandbox status via API
curl http://localhost:5000/api/sandbox/status
```

### First Command

```bash
# Execute nmap scan
curl -X POST http://localhost:5000/api/sandbox/execute \
  -H "Content-Type: application/json" \
  -d '{
    "command": "nmap -sS -p 80,443 172.25.0.10",
    "user_id": "agent_001",
    "timeout": 300
  }'
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  ATS MAFIA Framework                     │
│                                                          │
│  ┌──────────────────────────────────────────────┐       │
│  │           Sandbox Security Layer             │       │
│  │  • Command Validator                         │       │
│  │  • Security Monitor                          │       │
│  │  • Rate Limiter                              │       │
│  │  • Breakout Detector                         │       │
│  └──────────────────┬───────────────────────────┘       │
│                     │                                    │
└─────────────────────┼────────────────────────────────────┘
                      │
                      ▼
        ┌─────────────────────────────┐
        │    Kali Linux Container     │
        │  ┌──────────────────────┐   │
        │  │ nmap                 │   │
        │  │ metasploit           │   │
        │  │ sqlmap               │   │
        │  │ hydra                │   │
        │  │ burpsuite            │   │
        │  │ wireshark            │   │
        │  │ ... 600+ tools       │   │
        │  └──────────────────────┘   │
        └─────────────────────────────┘
```

## Available Tools

### Reconnaissance
- **nmap** - Network scanner and port mapper
- **masscan** - Fast port scanner
- **dnsenum** - DNS enumeration
- **whois** - Domain information lookup
- **traceroute** - Network path discovery

### Exploitation
- **metasploit** - Exploitation framework
- **sqlmap** - SQL injection tool
- **searchsploit** - Exploit database search
- **msfvenom** - Payload generator

### Web Testing
- **nikto** - Web server scanner
- **dirb** - Web directory bruteforcer
- **wpscan** - WordPress scanner
- **burpsuite** - Web proxy and scanner

### Password Attacks
- **hydra** - Network login cracker
- **john** - Password cracker
- **hashcat** - Hash cracker
- **crunch** - Wordlist generator

### Sniffing & Monitoring
- **wireshark** - Network protocol analyzer
- **tcpdump** - Packet capture
- **ettercap** - Network sniffer

[Full tool list in tool_whitelist.py](./tool_whitelist.py)

## Usage Examples

### Network Scanning

```python
from ats_mafia_framework.tools.remote import NmapRemoteTool

# Initialize nmap tool
nmap = NmapRemoteTool()

# Quick scan of common ports
result = nmap.quick_scan('172.25.0.10')

# Full port scan
result = nmap.full_scan('172.25.0.10')

# Service version detection
result = nmap.version_scan('172.25.0.10', ports='1-1000')
```

### SQL Injection Testing

```python
from ats_mafia_framework.tools.remote import SqlmapRemoteTool

# Initialize sqlmap
sqlmap = SqlmapRemoteTool()

# Test for SQL injection
result = sqlmap.execute(
    url='http://target.local/login.php',
    data='username=admin&password=test',
    level=3,
    risk=2
)
```

### Password Attacks

```python
from ats_mafia_framework.tools.remote import HydraRemoteTool

# Initialize hydra
hydra = HydraRemoteTool()

# SSH brute force
result = hydra.execute(
    target='172.25.0.10',
    service='ssh',
    username='admin',
    password_list='/usr/share/wordlists/rockyou.txt'
)
```

### Web Security Scanning

```python
from ats_mafia_framework.tools.remote import BurpSuiteRemoteTool

# Initialize burpsuite proxy
burp = BurpSuiteRemoteTool()

# Scan web application
result = burp.scan_url(
    url='http://target.local',
    scan_type='active'
)
```

## API Reference

### Status Endpoints

```bash
# Get sandbox status
GET /api/sandbox/status

# Health check
GET /api/sandbox/health

# List available tools
GET /api/sandbox/tools

# Get tool information
GET /api/sandbox/tools/{tool_name}
```

### Execution Endpoints

```bash
# Execute command
POST /api/sandbox/execute
{
  "command": "nmap -sS 172.25.0.10",
  "user_id": "agent_001",
  "timeout": 300
}

# List sandboxes
GET /api/sandbox/list

# Get container metrics
GET /api/sandbox/metrics/{container_id}
```

### Session Management

```bash
# Create ephemeral sandbox
POST /api/sandbox/session/{session_id}/create
{
  "session_id": "training_001",
  "cpu_limit": "2.0",
  "memory_limit": "4g"
}

# Destroy sandbox
DELETE /api/sandbox/session/{session_id}
```

### Security Endpoints

```bash
# Get audit log
GET /api/sandbox/security/audit-log?user_id=agent_001&limit=100

# Get security report
GET /api/sandbox/security/report

# Unblock user
POST /api/sandbox/security/unblock/{user_id}
```

### Snapshot Endpoints

```bash
# Create snapshot
POST /api/sandbox/snapshot/{container_id}?snapshot_name=backup_001

# Restore from snapshot
POST /api/sandbox/restore/{snapshot_id}?session_id=restored_001
```

## Security

### Command Validation

All commands go through three-layer validation:

1. **Whitelist Check** - Tool must be approved
2. **Pattern Matching** - Dangerous patterns blocked
3. **Security Monitor** - Real-time threat detection

```python
# Example: Blocked commands
"rm -rf /"              # Destructive operations
"docker ps"             # Container access
"cat /etc/shadow"       # Sensitive file access
"nc -l 4444"           # Reverse shell listeners
```

### Rate Limiting

- 100 commands per 5 minutes per user
- Automatic blocking on violation
- Cooldown period before unblock

### Network Isolation

- Training network: 172.25.0.0/16
- Isolated network: 172.26.0.0/16
- Firewall rules enforced
- External access controlled

See [SECURITY_MODEL.md](./SECURITY_MODEL.md) for complete details.

## Configuration

### Docker Compose Settings

```yaml
services:
  kali-sandbox:
    image: kalilinux/kali-rolling:latest
    container_name: ats_kali_sandbox
    networks:
      - ats-training-network
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - NET_ADMIN
      - NET_RAW
      - NET_BIND_SERVICE
```

### Environment Variables

```bash
# Sandbox configuration
export SANDBOX_CONTAINER_NAME=ats_kali_sandbox
export SANDBOX_MAX_CPU=2.0
export SANDBOX_MAX_MEMORY=4G
export SANDBOX_NETWORK=ats-training-network

# Rate limiting
export RATE_LIMIT_MAX_COMMANDS=100
export RATE_LIMIT_WINDOW_MINUTES=5

# Audit logging
export AUDIT_LOG_PATH=/tmp/ats_sandbox_audit.log
export AUDIT_LOG_RETENTION_DAYS=90
```

## Troubleshooting

### Container Won't Start

```bash
# Check Docker status
docker ps -a | grep kali

# View container logs
docker logs ats_kali_sandbox

# Restart container
docker restart ats_kali_sandbox
```

### Command Execution Fails

```bash
# Verify container is running
curl http://localhost:5000/api/sandbox/status

# Check if tool is installed
curl http://localhost:5000/api/sandbox/tools/nmap

# Review audit log
tail -f /tmp/ats_sandbox_audit.log
```

### Rate Limit Issues

```bash
# Check current rate limits
curl http://localhost:5000/api/sandbox/security/report

# Unblock user
curl -X POST http://localhost:5000/api/sandbox/security/unblock/agent_001
```

### Network Connectivity

```bash
# Test connectivity
docker exec ats_kali_sandbox ping -c 3 172.25.0.10

# Check network configuration
docker network inspect ats-training-network

# Verify firewall rules
docker exec ats_kali_sandbox iptables -L
```

## Maintenance

### Regular Updates

```bash
# Update Kali image (monthly)
docker pull kalilinux/kali-rolling:latest
docker-compose down
docker-compose up -d

# Update tool database
docker exec ats_kali_sandbox apt-get update
docker exec ats_kali_sandbox apt-get upgrade -y
```

### Cleanup Old Sandboxes

```bash
# Via API
curl -X POST http://localhost:5000/api/sandbox/cleanup?max_age_hours=24

# Manual cleanup
docker ps -a --filter "label=ats.mafia.type=ephemeral_sandbox" -q | xargs docker rm -f
```

### Backup and Restore

```bash
# Create snapshot
curl -X POST http://localhost:5000/api/sandbox/snapshot/abc123?snapshot_name=backup_$(date +%Y%m%d)

# List snapshots
docker images | grep ats-mafia/kali-snapshot

# Restore from snapshot
curl -X POST http://localhost:5000/api/sandbox/restore/snapshot_id?session_id=restored_001
```

## Performance Tuning

### Resource Allocation

```yaml
# Adjust in docker-compose.yml
deploy:
  resources:
    limits:
      cpus: '4.0'      # Increase for better performance
      memory: 8G       # Increase for large scans
```

### Parallel Execution

```python
# Execute multiple scans concurrently
from concurrent.futures import ThreadPoolExecutor

targets = ['172.25.0.10', '172.25.0.11', '172.25.0.12']

with ThreadPoolExecutor(max_workers=3) as executor:
    futures = [executor.submit(nmap.quick_scan, target) for target in targets]
    results = [f.result() for f in futures]
```

## Best Practices

### For Administrators

1. **Regular Updates** - Keep Kali image and tools updated
2. **Monitor Logs** - Review audit logs daily
3. **Resource Monitoring** - Track CPU/memory usage
4. **Backup Snapshots** - Create regular snapshots
5. **Security Reviews** - Audit access and permissions monthly

### For Users

1. **Validate Targets** - Ensure targets are in training network
2. **Appropriate Intensity** - Use suitable scan speeds
3. **Clean Up** - Remove temporary files after operations
4. **Report Issues** - Document and report bugs
5. **Ethical Usage** - Follow training guidelines

## Integration with Training Scenarios

```python
# Example: Penetration test scenario
from ats_mafia_framework.scenarios import PenetrationTestScenario
from ats_mafia_framework.tools.remote import NmapRemoteTool, SqlmapRemoteTool

# Define scenario
scenario = PenetrationTestScenario(
    target='172.25.0.10',
    objectives=['recon', 'vulnerability_scan', 'exploitation']
)

# Phase 1: Reconnaissance
nmap = NmapRemoteTool()
recon_results = nmap.full_scan(scenario.target)

# Phase 2: Vulnerability Scanning
if recon_results['success']:
    open_ports = recon_results['parsed']['open_ports']
    # Continue with exploitation...
```

## FAQ

**Q: Can I add custom tools to the sandbox?**
A: Yes, install via `apt-get` and add to whitelist in `tool_whitelist.py`

**Q: How do I increase the rate limit?**
A: Modify `RATE_LIMIT_MAX_COMMANDS` in `security_monitor.py`

**Q: Can multiple agents use the same sandbox?**
A: Yes, but create ephemeral sandboxes per session for isolation

**Q: How do I access tools not in the whitelist?**
A: Request addition via PR after security review

**Q: What happens if container is compromised?**
A: Automatic shutdown, user block, and alert generation

## Support

- **Documentation**: [SECURITY_MODEL.md](./SECURITY_MODEL.md)
- **Issues**: GitHub Issues
- **Security**: security@ats-mafia.local
- **Community**: Discord/Slack

## License

See [LICENSE](../../LICENSE)

---

**Version:** 1.0  
**Last Updated:** 2025-10-18  
**Maintainer:** ATS MAFIA Development Team