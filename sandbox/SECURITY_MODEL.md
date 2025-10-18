# Kali Linux Sandbox Security Model

## Overview

The ATS MAFIA Framework's Kali Linux Sandbox provides agents with access to real security tools while maintaining strict security controls to prevent abuse and unauthorized access.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     ATS MAFIA Framework                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Agents     │  │  Orchestrator│  │  UI/API      │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │              │
│         └──────────────────┴──────────────────┘              │
│                            │                                 │
│                            ▼                                 │
│  ┌─────────────────────────────────────────────────────┐    │
│  │         Sandbox Security Layer                      │    │
│  │  ┌─────────────┐  ┌──────────────┐  ┌───────────┐  │    │
│  │  │  Command    │  │   Security   │  │   Rate    │  │    │
│  │  │  Validator  │  │   Monitor    │  │  Limiter  │  │    │
│  │  └─────────────┘  └──────────────┘  └───────────┘  │    │
│  └─────────────────────────────────────────────────────┘    │
│                            │                                 │
└────────────────────────────┼─────────────────────────────────┘
                             │
                             ▼
            ┌────────────────────────────────┐
            │   Docker Network Isolation     │
            │  ┌──────────────────────────┐  │
            │  │ Training Network         │  │
            │  │ 172.25.0.0/16           │  │
            │  │  ┌──────────────┐       │  │
            │  │  │ Kali Sandbox │       │  │
            │  │  └──────────────┘       │  │
            │  │  ┌──────────────┐       │  │
            │  │  │ Target VMs   │       │  │
            │  │  └──────────────┘       │  │
            │  └──────────────────────────┘  │
            └────────────────────────────────┘
```

## Security Controls

### 1. Container Isolation

**Mechanism:**
- Containers run with `no-new-privileges:true`
- All capabilities dropped (`cap_drop: ALL`)
- Only essential capabilities added (`NET_ADMIN`, `NET_RAW`, `NET_BIND_SERVICE`)
- No privileged mode access
- Read-only sandbox code mount

**Protection Against:**
- Container escape attempts
- Privilege escalation
- Host system access
- Unauthorized capability usage

### 2. Command Validation

**Three-Layer Validation:**

**Layer 1: Whitelist Check**
- Only approved tools can be executed
- 100+ security tools in approved list
- Tools categorized by function (recon, exploitation, etc.)

**Layer 2: Pattern Matching**
- Dangerous commands blocked (`rm -rf`, `dd`, etc.)
- Shell metacharacters filtered
- Command injection patterns detected
- File system access restrictions

**Layer 3: Security Monitor**
- Real-time command analysis
- Breakout attempt detection
- Suspicious pattern identification
- User behavior tracking

**Example Blocked Patterns:**
```regex
/dev/mem           # Memory device access
docker.sock        # Docker socket
nsenter            # Namespace manipulation
/proc/1/           # Init process access
chmod +s           # SUID bit setting
```

### 3. Network Segmentation

**Training Network (172.25.0.0/16):**
- Isolated from production networks
- Inter-container communication allowed
- Controlled external access
- Firewall rules enforced

**Isolated Network (172.26.0.0/16):**
- No external internet access
- Fully air-gapped environment
- For high-risk operations
- Target machine containment

**Firewall Rules:**
```bash
# Default rules applied to containers
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
iptables -A INPUT -i lo -j ACCEPT
iptables -A INPUT -s 172.25.0.0/16 -j ACCEPT
iptables -A OUTPUT -d 172.25.0.0/16 -j ACCEPT
iptables -A INPUT -j DROP
iptables -P FORWARD DROP
```

### 4. Resource Limits

**Per-Container Limits:**
- CPU: 2 cores maximum
- Memory: 4GB maximum
- Disk I/O: Rate limited
- Network bandwidth: Throttled

**Purpose:**
- Prevent resource exhaustion
- Ensure fair usage
- Protect host system
- Enable multi-tenancy

### 5. Rate Limiting

**Per-User Limits:**
- 100 commands per 5 minutes
- Automatic blocking on violation
- Cooldown period enforcement
- Audit log of all attempts

**Implementation:**
```python
# Sliding window rate limiter
if command_count > 100 in last_5_minutes:
    block_user()
    audit_log_violation()
```

### 6. Audit Logging

**All Events Logged:**
- Command execution (success/failure)
- Security violations
- Resource usage
- Network activity
- User actions

**Log Format:**
```json
{
  "timestamp": "2025-10-18T01:00:00Z",
  "user_id": "agent_001",
  "container_id": "abc123def456",
  "command": "nmap -sS 172.25.0.10",
  "status": "ALLOWED",
  "threat_level": "LOW",
  "execution_time": 45.2
}
```

**Log Retention:**
- Minimum 90 days
- Immutable once written
- Encrypted at rest
- Regular backup

### 7. Breakout Detection

**Monitored Indicators:**
- Docker socket access attempts
- Namespace manipulation (`nsenter`, `unshare`)
- Bind mount operations
- SUID binary searches
- Kernel memory access
- Cgroup escape techniques

**Response Actions:**
1. Immediate command blocking
2. User account suspension
3. Container quarantine
4. Alert generation
5. Forensic logging

**Example Detection:**
```python
def detect_breakout_attempt(command):
    indicators = [
        r'docker\.sock',
        r'nsenter',
        r'/proc/1/',
        r'cgroup.*release_agent'
    ]
    for indicator in indicators:
        if re.search(indicator, command):
            return True
    return False
```

## Threat Model

### Threats Mitigated

1. **Container Escape**
   - Mitigation: Capability restrictions, SELinux/AppArmor, namespace isolation
   - Risk Level: Critical
   - Detection: Breakout attempt monitoring

2. **Resource Exhaustion**
   - Mitigation: CPU/memory limits, rate limiting
   - Risk Level: High
   - Detection: Resource usage monitoring

3. **Lateral Movement**
   - Mitigation: Network segmentation, firewall rules
   - Risk Level: High
   - Detection: Network traffic analysis

4. **Command Injection**
   - Mitigation: Input validation, command whitelisting
   - Risk Level: Medium
   - Detection: Pattern matching

5. **Information Disclosure**
   - Mitigation: Audit logging, access controls
   - Risk Level: Medium
   - Detection: Log analysis

### Residual Risks

1. **Zero-Day Exploits**
   - Risk: Unpatched vulnerabilities in tools
   - Mitigation: Regular updates, isolated network
   - Acceptance: Minimal risk in training environment

2. **Social Engineering**
   - Risk: Malicious commands from compromised agents
   - Mitigation: Rate limiting, audit logging, user monitoring
   - Acceptance: Monitoring and response procedures

## Security Best Practices

### For Administrators

1. **Regular Updates**
   ```bash
   # Update Kali container monthly
   docker pull kalilinux/kali-rolling:latest
   docker-compose down
   docker-compose up -d
   ```

2. **Log Monitoring**
   ```bash
   # Review audit logs daily
   tail -f /tmp/ats_sandbox_audit.log
   
   # Check for security violations
   grep "BREAKOUT_ATTEMPT" /tmp/ats_sandbox_audit.log
   ```

3. **Resource Monitoring**
   ```bash
   # Monitor container resources
   docker stats ats_kali_sandbox
   
   # Check for resource abuse
   docker inspect ats_kali_sandbox
   ```

4. **Network Inspection**
   ```bash
   # Verify network isolation
   docker network inspect ats-training-network
   
   # Check firewall rules
   docker exec ats_kali_sandbox iptables -L
   ```

### For Users

1. **Command Safety**
   - Always validate targets are in training network
   - Avoid destructive operations
   - Use appropriate scan intensities
   - Report suspicious behavior

2. **Resource Consciousness**
   - Limit concurrent scans
   - Use appropriate timeouts
   - Clean up after operations
   - Respect rate limits

3. **Ethical Usage**
   - Only scan authorized targets
   - Follow training scenarios
   - Document all actions
   - Report vulnerabilities responsibly

## Incident Response

### Detection

**Automated Alerts:**
- Breakout attempts
- Rate limit violations
- Resource exhaustion
- Unusual command patterns

### Response Procedure

1. **Immediate Actions**
   - Block offending user
   - Quarantine container
   - Preserve logs
   - Alert administrators

2. **Investigation**
   - Review audit logs
   - Analyze command history
   - Check resource usage
   - Identify root cause

3. **Remediation**
   - Patch vulnerabilities
   - Update rules
   - Restore from snapshot if needed
   - Implement additional controls

4. **Post-Incident**
   - Document incident
   - Update procedures
   - User notification
   - Lessons learned session

## Compliance

### Logging Requirements

- All commands logged with timestamps
- User identification required
- Retention minimum 90 days
- Regular backup to secure storage

### Access Control

- Role-based access control (RBAC)
- Multi-factor authentication (MFA) recommended
- Least privilege principle
- Regular access reviews

### Audit Trail

- Immutable log entries
- Cryptographic signatures
- Chain of custody maintenance
- Regular compliance audits

## Testing Security Controls

### Validation Tests

```bash
# Test 1: Verify command validation
curl -X POST http://localhost:5000/api/sandbox/execute \
  -H "Content-Type: application/json" \
  -d '{"command":"rm -rf /", "user_id":"test"}'
# Expected: 400 Bad Request

# Test 2: Verify rate limiting
for i in {1..150}; do
  curl -X POST http://localhost:5000/api/sandbox/execute \
    -H "Content-Type: application/json" \
    -d "{\"command\":\"echo test\", \"user_id\":\"test\"}"
done
# Expected: 403 Forbidden after 100 requests

# Test 3: Verify network isolation
docker exec ats_kali_sandbox ping -c 1 8.8.8.8
# Expected: Network unreachable (if isolated mode)

# Test 4: Verify breakout detection
curl -X POST http://localhost:5000/api/sandbox/execute \
  -H "Content-Type: application/json" \
  -d '{"command":"docker ps", "user_id":"test"}'
# Expected: 403 Forbidden - Breakout attempt detected
```

## Security Checklist

### Pre-Deployment
- [ ] Docker daemon secured
- [ ] Network isolation configured
- [ ] Resource limits set
- [ ] Audit logging enabled
- [ ] Backup procedures tested
- [ ] Incident response plan documented

### Operational
- [ ] Regular security updates
- [ ] Log review (daily)
- [ ] Resource monitoring (continuous)
- [ ] User access review (weekly)
- [ ] Backup verification (weekly)
- [ ] Security scan (monthly)

### Post-Incident
- [ ] Logs preserved
- [ ] Root cause identified
- [ ] Remediation implemented
- [ ] Documentation updated
- [ ] Team notification sent
- [ ] Lessons learned documented

## References

- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
- [OWASP Container Security](https://owasp.org/www-project-docker-top-10/)
- [CIS Docker Benchmark](https://www.cisecurity.org/benchmark/docker)
- [Kali Linux Documentation](https://www.kali.org/docs/)

---

**Last Updated:** 2025-10-18  
**Version:** 1.0  
**Maintainer:** ATS MAFIA Security Team