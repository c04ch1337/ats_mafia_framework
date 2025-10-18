"""
Security Monitor
Monitor sandbox for suspicious activity and prevent malicious actions.
"""

import re
import logging
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


class SecurityMonitor:
    """Monitor sandbox containers for security threats and suspicious activity."""
    
    def __init__(self):
        """Initialize security monitor."""
        self.audit_log = []
        self.rate_limits = {}
        self.blocked_users = set()
        self.suspicious_patterns = self._initialize_suspicious_patterns()
        logger.info("SecurityMonitor initialized")
    
    def _initialize_suspicious_patterns(self) -> List[str]:
        """Initialize patterns that indicate suspicious activity."""
        return [
            r'/etc/passwd',
            r'/etc/shadow',
            r'docker\.sock',
            r'breakout',
            r'escape',
            r'privilege.*escalation',
            r'spawn.*shell',
            r'reverse.*shell',
            r'nc.*-[el]',
            r'python.*-c.*socket',
            r'perl.*-e.*socket',
            r'/proc/self',
            r'cgroup',
            r'namespace',
            r'pivot_root',
            r'mount.*proc',
        ]
    
    def monitor_command(
        self,
        user_id: str,
        command: str,
        container_id: str
    ) -> Dict[str, any]:
        """
        Monitor and analyze command for security threats.
        
        Args:
            user_id: User executing the command
            command: Command to monitor
            container_id: Container where command will execute
            
        Returns:
            Dict with monitoring results and threat assessment
        """
        timestamp = datetime.utcnow()
        
        # Check if user is blocked
        if user_id in self.blocked_users:
            logger.warning(f"Blocked user {user_id} attempted command execution")
            return {
                'allowed': False,
                'reason': 'User is blocked due to previous violations',
                'threat_level': 'CRITICAL'
            }
        
        # Check rate limits
        rate_check = self.rate_limit_check(user_id)
        if not rate_check['allowed']:
            logger.warning(f"Rate limit exceeded for user {user_id}")
            return {
                'allowed': False,
                'reason': rate_check['reason'],
                'threat_level': 'MEDIUM'
            }
        
        # Detect breakout attempts
        if self.detect_breakout_attempt(command):
            logger.critical(f"Container breakout attempt detected: {command}")
            self.audit_log_event({
                'timestamp': timestamp.isoformat(),
                'user_id': user_id,
                'container_id': container_id,
                'command': command,
                'threat': 'BREAKOUT_ATTEMPT',
                'action': 'BLOCKED'
            })
            # Block user after breakout attempt
            self.blocked_users.add(user_id)
            return {
                'allowed': False,
                'reason': 'Container breakout attempt detected',
                'threat_level': 'CRITICAL'
            }
        
        # Check for suspicious patterns
        suspicious_findings = []
        for pattern in self.suspicious_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                suspicious_findings.append(pattern)
        
        if suspicious_findings:
            logger.warning(f"Suspicious command patterns detected: {suspicious_findings}")
            self.audit_log_event({
                'timestamp': timestamp.isoformat(),
                'user_id': user_id,
                'container_id': container_id,
                'command': command,
                'threat': 'SUSPICIOUS_PATTERNS',
                'patterns': suspicious_findings,
                'action': 'FLAGGED'
            })
        
        # Log the command
        self.audit_log_event({
            'timestamp': timestamp.isoformat(),
            'user_id': user_id,
            'container_id': container_id,
            'command': command,
            'status': 'MONITORED'
        })
        
        return {
            'allowed': True,
            'warnings': suspicious_findings,
            'threat_level': 'LOW' if not suspicious_findings else 'MEDIUM'
        }
    
    def detect_breakout_attempt(self, command: str) -> bool:
        """
        Detect container escape/breakout attempts.
        
        Args:
            command: Command to analyze
            
        Returns:
            True if breakout attempt detected
        """
        breakout_indicators = [
            r'docker\.sock',  # Docker socket access
            r'/var/run/docker',  # Docker runtime access
            r'nsenter',  # Namespace entry
            r'unshare',  # Namespace manipulation
            r'mount.*--bind',  # Bind mounts
            r'chroot.*/',  # Root directory change
            r'/proc/1/',  # Init process access
            r'cgroup.*release_agent',  # Cgroup escape
            r'find.*-perm.*4000',  # SUID binary search
            r'chmod.*\+s',  # SUID bit setting
            r'/dev/mem',  # Memory device access
            r'/dev/kmem',  # Kernel memory access
            r'iptables.*DOCKER',  # Docker iptables manipulation
        ]
        
        for indicator in breakout_indicators:
            if re.search(indicator, command, re.IGNORECASE):
                logger.critical(f"Breakout indicator detected: {indicator}")
                return True
        
        return False
    
    def rate_limit_check(self, user_id: str, max_commands: int = 100, window_minutes: int = 5) -> Dict[str, any]:
        """
        Check if user has exceeded rate limits.
        
        Args:
            user_id: User to check
            max_commands: Maximum commands allowed in window
            window_minutes: Time window in minutes
            
        Returns:
            Dict with rate limit check results
        """
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=window_minutes)
        
        # Initialize user's rate limit tracking if not exists
        if user_id not in self.rate_limits:
            self.rate_limits[user_id] = []
        
        # Remove old entries outside window
        self.rate_limits[user_id] = [
            ts for ts in self.rate_limits[user_id]
            if datetime.fromisoformat(ts) > window_start
        ]
        
        # Check if limit exceeded
        current_count = len(self.rate_limits[user_id])
        
        if current_count >= max_commands:
            return {
                'allowed': False,
                'reason': f'Rate limit exceeded: {current_count}/{max_commands} commands in {window_minutes} minutes',
                'current_count': current_count,
                'limit': max_commands
            }
        
        # Add current timestamp
        self.rate_limits[user_id].append(now.isoformat())
        
        return {
            'allowed': True,
            'current_count': current_count + 1,
            'limit': max_commands,
            'remaining': max_commands - current_count - 1
        }
    
    def audit_log_event(self, event: Dict[str, any]):
        """
        Log security event to audit log.
        
        Args:
            event: Event details to log
        """
        self.audit_log.append(event)
        
        # Write to persistent log file
        try:
            with open('/tmp/ats_sandbox_audit.log', 'a') as f:
                f.write(json.dumps(event) + '\n')
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")
    
    def get_audit_log(
        self,
        user_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, any]]:
        """
        Retrieve audit log entries.
        
        Args:
            user_id: Optional filter by user
            limit: Maximum entries to return
            
        Returns:
            List of audit log entries
        """
        logs = self.audit_log
        
        if user_id:
            logs = [log for log in logs if log.get('user_id') == user_id]
        
        return logs[-limit:]
    
    def get_security_report(self) -> Dict[str, any]:
        """
        Generate security report with statistics.
        
        Returns:
            Dict with security statistics
        """
        total_events = len(self.audit_log)
        
        # Count by threat type
        threats = {}
        for event in self.audit_log:
            threat = event.get('threat', 'NONE')
            threats[threat] = threats.get(threat, 0) + 1
        
        # Count blocked users
        blocked_count = len(self.blocked_users)
        
        # Get recent critical events
        recent_critical = [
            event for event in self.audit_log[-100:]
            if event.get('threat') in ['BREAKOUT_ATTEMPT', 'CRITICAL']
        ]
        
        return {
            'total_events': total_events,
            'threats_by_type': threats,
            'blocked_users_count': blocked_count,
            'blocked_users': list(self.blocked_users),
            'recent_critical_events': recent_critical,
            'generated_at': datetime.utcnow().isoformat()
        }
    
    def unblock_user(self, user_id: str) -> bool:
        """
        Unblock a previously blocked user.
        
        Args:
            user_id: User to unblock
            
        Returns:
            True if user was unblocked
        """
        if user_id in self.blocked_users:
            self.blocked_users.remove(user_id)
            logger.info(f"User {user_id} unblocked")
            self.audit_log_event({
                'timestamp': datetime.utcnow().isoformat(),
                'user_id': user_id,
                'action': 'UNBLOCKED',
                'performed_by': 'admin'
            })
            return True
        return False
    
    def clear_rate_limits(self, user_id: Optional[str] = None):
        """
        Clear rate limit tracking.
        
        Args:
            user_id: Specific user to clear, or None for all
        """
        if user_id:
            self.rate_limits.pop(user_id, None)
            logger.info(f"Rate limits cleared for user {user_id}")
        else:
            self.rate_limits.clear()
            logger.info("All rate limits cleared")
    
    def export_audit_log(self, filepath: str) -> bool:
        """
        Export audit log to file.
        
        Args:
            filepath: Path to export file
            
        Returns:
            True if export successful
        """
        try:
            with open(filepath, 'w') as f:
                json.dump(self.audit_log, f, indent=2)
            logger.info(f"Audit log exported to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to export audit log: {e}")
            return False


__all__ = ['SecurityMonitor']