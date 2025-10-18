"""
Security Control Bypass System
⚠️ TOP SECRET - REQUIRES ACTIVE BACKDOOR SESSION ⚠️

Allows temporary bypass of specific security controls with
valid backdoor session token.

All bypass actions are fully audited and cannot be disabled.
"""

import secrets
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from enum import Enum
from pathlib import Path

from .backdoor_system import AdminBackdoor


class BypassableControl(Enum):
    """
    Controls that can be temporarily bypassed by admins.
    
    Note: AUDIT_LOGGING can NEVER be bypassed - this is hardcoded.
    """
    SIMULATION_MODE = "simulation_mode"
    COMMAND_WHITELIST = "command_whitelist"
    RATE_LIMITING = "rate_limiting"
    NETWORK_ISOLATION = "network_isolation"
    RESOURCE_LIMITS = "resource_limits"
    FILE_SYSTEM_RESTRICTIONS = "file_system_restrictions"
    CONTAINER_ESCAPE_PREVENTION = "container_escape_prevention"
    # Note: audit_logging CANNOT be bypassed


class SecurityBypass:
    """Manage temporary security control bypasses."""
    
    BYPASS_LOG_FILE = Path("logs/security_bypass_audit.log")
    ACTIVE_BYPASSES_FILE = Path("ats_mafia_framework/admin/.active_bypasses.json")
    
    # Maximum bypass duration (in minutes)
    MAX_BYPASS_DURATION = 15
    
    def __init__(self, backdoor_system: AdminBackdoor):
        """
        Initialize security bypass system.
        
        Args:
            backdoor_system: AdminBackdoor instance for session verification
        """
        self.backdoor = backdoor_system
        self.active_bypasses = {}
        self._ensure_log_exists()
        self._load_bypasses()
    
    def _ensure_log_exists(self):
        """Ensure bypass audit log exists."""
        if not self.BYPASS_LOG_FILE.parent.exists():
            self.BYPASS_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        if not self.BYPASS_LOG_FILE.exists():
            with open(self.BYPASS_LOG_FILE, 'w') as f:
                header = {
                    'log_initialized': datetime.now().isoformat(),
                    'version': '1.0',
                    'type': 'security_bypass_audit_log'
                }
                f.write(json.dumps(header) + '\n')
    
    def _load_bypasses(self):
        """Load active bypasses from file."""
        if self.ACTIVE_BYPASSES_FILE.exists():
            try:
                with open(self.ACTIVE_BYPASSES_FILE, 'r') as f:
                    self.active_bypasses = json.load(f)
            except:
                self.active_bypasses = {}
        else:
            self.active_bypasses = {}
            self.ACTIVE_BYPASSES_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    def _save_bypasses(self):
        """Save active bypasses to file."""
        with open(self.ACTIVE_BYPASSES_FILE, 'w') as f:
            json.dump(self.active_bypasses, f, indent=2)
    
    def bypass_control(
        self,
        session_token: str,
        control: BypassableControl,
        reason: str,
        duration_minutes: int = 15
    ) -> Optional[str]:
        """
        Temporarily bypass a security control.
        
        Requires valid session token and detailed reason.
        All bypass attempts are logged regardless of success.
        
        Args:
            session_token: Valid admin backdoor session token
            control: The control to bypass (from BypassableControl enum)
            reason: Detailed justification (required, min 50 characters)
            duration_minutes: Bypass duration (max 15 minutes)
        
        Returns:
            Bypass ID if successful, None otherwise
        """
        bypass_attempt = {
            'timestamp': datetime.now().isoformat(),
            'control': control.value,
            'reason': reason,
            'duration_requested': duration_minutes,
            'success': False,
            'failure_reason': None
        }
        
        try:
            # Validate reason length
            if len(reason) < 50:
                bypass_attempt['failure_reason'] = 'INSUFFICIENT_JUSTIFICATION'
                self._log_bypass_attempt(bypass_attempt)
                return None
            
            # Enforce maximum duration
            if duration_minutes > self.MAX_BYPASS_DURATION:
                bypass_attempt['failure_reason'] = f'DURATION_EXCEEDS_MAX ({duration_minutes} > {self.MAX_BYPASS_DURATION})'
                self._log_bypass_attempt(bypass_attempt)
                return None
            
            # Verify session
            if not self.backdoor.verify_session(session_token):
                bypass_attempt['failure_reason'] = 'INVALID_SESSION'
                self._log_bypass_attempt(bypass_attempt)
                return None
            
            # Check if control is already bypassed
            if self.is_control_bypassed(control):
                bypass_attempt['failure_reason'] = 'ALREADY_BYPASSED'
                self._log_bypass_attempt(bypass_attempt)
                return None
            
            # Create bypass record
            bypass_id = secrets.token_hex(16)
            created_at = datetime.now()
            expires_at = created_at + timedelta(minutes=duration_minutes)
            
            bypass_record = {
                'bypass_id': bypass_id,
                'control': control.value,
                'reason': reason,
                'created_at': created_at.isoformat(),
                'expires_at': expires_at.isoformat(),
                'session_token_hash': hashlib.sha256(session_token.encode()).hexdigest(),
                'revoked': False
            }
            
            self.active_bypasses[bypass_id] = bypass_record
            self._save_bypasses()
            
            # Update attempt record
            bypass_attempt['success'] = True
            bypass_attempt['bypass_id'] = bypass_id
            bypass_attempt['expires_at'] = expires_at.isoformat()
            
            # Log bypass (cannot be disabled)
            self._log_bypass_attempt(bypass_attempt)
            
            # Alert security team
            self._alert_bypass_activated(bypass_record)
            
            return bypass_id
            
        except Exception as e:
            bypass_attempt['failure_reason'] = f'EXCEPTION: {str(e)}'
            self._log_bypass_attempt(bypass_attempt)
            return None
    
    def restore_control(self, bypass_id: str, session_token: str) -> bool:
        """
        Manually restore a bypassed control before expiration.
        
        Args:
            bypass_id: ID of bypass to restore
            session_token: Valid admin session token
        
        Returns:
            True if restored successfully, False otherwise
        """
        restore_attempt = {
            'timestamp': datetime.now().isoformat(),
            'bypass_id': bypass_id,
            'success': False
        }
        
        try:
            # Verify session
            if not self.backdoor.verify_session(session_token):
                restore_attempt['failure_reason'] = 'INVALID_SESSION'
                self._log_restore_attempt(restore_attempt)
                return False
            
            # Check if bypass exists
            if bypass_id not in self.active_bypasses:
                restore_attempt['failure_reason'] = 'BYPASS_NOT_FOUND'
                self._log_restore_attempt(restore_attempt)
                return False
            
            bypass_record = self.active_bypasses[bypass_id]
            bypass_record['restored_at'] = datetime.now().isoformat()
            bypass_record['revoked'] = True
            
            self._save_bypasses()
            
            restore_attempt['success'] = True
            restore_attempt['control'] = bypass_record['control']
            
            self._log_restore_attempt(restore_attempt)
            self._alert_bypass_restored(bypass_record)
            
            return True
            
        except Exception as e:
            restore_attempt['failure_reason'] = f'EXCEPTION: {str(e)}'
            self._log_restore_attempt(restore_attempt)
            return False
    
    def is_control_bypassed(self, control: BypassableControl) -> bool:
        """
        Check if a control is currently bypassed.
        
        Args:
            control: The control to check
        
        Returns:
            True if bypassed and not expired, False otherwise
        """
        # Clean up expired bypasses first
        self._cleanup_expired_bypasses()
        
        # Check active bypasses
        for bypass_record in self.active_bypasses.values():
            if bypass_record['control'] == control.value:
                # Check if not revoked
                if not bypass_record.get('revoked', False):
                    # Check if not expired
                    expires_at = datetime.fromisoformat(bypass_record['expires_at'])
                    if datetime.now() < expires_at:
                        return True
        
        return False
    
    def get_active_bypasses(self) -> List[Dict]:
        """
        Get list of currently active bypasses.
        
        Returns:
            List of active bypass records (sanitized)
        """
        self._cleanup_expired_bypasses()
        
        active = []
        for bypass_id, bypass_record in self.active_bypasses.items():
            if not bypass_record.get('revoked', False):
                expires_at = datetime.fromisoformat(bypass_record['expires_at'])
                if datetime.now() < expires_at:
                    active.append({
                        'bypass_id': bypass_id,
                        'control': bypass_record['control'],
                        'created_at': bypass_record['created_at'],
                        'expires_at': bypass_record['expires_at'],
                        'reason': bypass_record['reason'][:100] + '...'  # Truncated
                    })
        
        return active
    
    def revoke_all_bypasses(self, session_token: str) -> bool:
        """
        Emergency revocation of all active bypasses.
        
        Args:
            session_token: Valid admin session token
        
        Returns:
            True if successful, False otherwise
        """
        revocation = {
            'timestamp': datetime.now().isoformat(),
            'event': 'EMERGENCY_BYPASS_REVOCATION',
            'success': False
        }
        
        try:
            # Verify session
            if not self.backdoor.verify_session(session_token):
                revocation['failure_reason'] = 'INVALID_SESSION'
                self._log_system_event(revocation)
                return False
            
            # Revoke all bypasses
            count = 0
            for bypass_id in list(self.active_bypasses.keys()):
                self.active_bypasses[bypass_id]['revoked'] = True
                self.active_bypasses[bypass_id]['revoked_at'] = datetime.now().isoformat()
                count += 1
            
            self._save_bypasses()
            
            revocation['success'] = True
            revocation['bypasses_revoked'] = count
            
            self._log_system_event(revocation)
            self._alert_all_bypasses_revoked(count)
            
            return True
            
        except Exception as e:
            revocation['failure_reason'] = f'EXCEPTION: {str(e)}'
            self._log_system_event(revocation)
            return False
    
    def _cleanup_expired_bypasses(self):
        """Remove expired bypasses from active list."""
        current_time = datetime.now()
        expired_ids = []
        
        for bypass_id, bypass_record in self.active_bypasses.items():
            expires_at = datetime.fromisoformat(bypass_record['expires_at'])
            if current_time > expires_at:
                expired_ids.append(bypass_id)
        
        for bypass_id in expired_ids:
            bypass_record = self.active_bypasses[bypass_id]
            bypass_record['expired'] = True
            
            # Log expiration
            self._log_system_event({
                'event': 'BYPASS_EXPIRED',
                'bypass_id': bypass_id,
                'control': bypass_record['control'],
                'timestamp': current_time.isoformat()
            })
    
    def _log_bypass_attempt(self, attempt: Dict):
        """Log bypass attempt to audit log."""
        log_entry = {
            'type': 'BYPASS_ATTEMPT',
            **attempt
        }
        
        with open(self.BYPASS_LOG_FILE, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def _log_restore_attempt(self, attempt: Dict):
        """Log restore attempt to audit log."""
        log_entry = {
            'type': 'RESTORE_ATTEMPT',
            **attempt
        }
        
        with open(self.BYPASS_LOG_FILE, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def _log_system_event(self, event: Dict):
        """Log system event to audit log."""
        log_entry = {
            'type': 'SYSTEM_EVENT',
            **event
        }
        
        with open(self.BYPASS_LOG_FILE, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def _alert_bypass_activated(self, bypass_record: Dict):
        """Alert security team that a bypass was activated."""
        alert = {
            'SECURITY_ALERT': 'CONTROL_BYPASSED',
            'severity': 'CRITICAL',
            'timestamp': datetime.now().isoformat(),
            'control': bypass_record['control'],
            'bypass_id': bypass_record['bypass_id'],
            'expires_at': bypass_record['expires_at'],
            'reason': bypass_record['reason']
        }
        
        # Log to security alerts
        alert_file = Path("logs/security_alerts.log")
        alert_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(alert_file, 'a') as f:
            f.write(json.dumps(alert) + '\n')
        
        # TODO: Implement real alerting
        # - Email security team
        # - Post to Slack/Teams
        # - Create incident in PagerDuty
        # - Forward to SIEM
    
    def _alert_bypass_restored(self, bypass_record: Dict):
        """Alert security team that a bypass was restored."""
        alert = {
            'SECURITY_ALERT': 'CONTROL_RESTORED',
            'severity': 'HIGH',
            'timestamp': datetime.now().isoformat(),
            'control': bypass_record['control'],
            'bypass_id': bypass_record['bypass_id'],
            'restored_at': bypass_record.get('restored_at')
        }
        
        alert_file = Path("logs/security_alerts.log")
        with open(alert_file, 'a') as f:
            f.write(json.dumps(alert) + '\n')
    
    def _alert_all_bypasses_revoked(self, count: int):
        """Alert security team that all bypasses were revoked."""
        alert = {
            'SECURITY_ALERT': 'ALL_BYPASSES_REVOKED',
            'severity': 'CRITICAL',
            'timestamp': datetime.now().isoformat(),
            'bypasses_revoked': count
        }
        
        alert_file = Path("logs/security_alerts.log")
        with open(alert_file, 'a') as f:
            f.write(json.dumps(alert) + '\n')


def get_bypassable_controls() -> List[Dict[str, str]]:
    """
    Get list of all bypassable controls with descriptions.
    
    Returns:
        List of control information
    """
    controls = []
    
    for control in BypassableControl:
        description = {
            BypassableControl.SIMULATION_MODE: "Allow real operations instead of simulated ones",
            BypassableControl.COMMAND_WHITELIST: "Execute non-whitelisted commands",
            BypassableControl.RATE_LIMITING: "Remove rate limits on API calls and operations",
            BypassableControl.NETWORK_ISOLATION: "Allow access to external networks",
            BypassableControl.RESOURCE_LIMITS: "Increase container resource limits (CPU, memory)",
            BypassableControl.FILE_SYSTEM_RESTRICTIONS: "Access files outside designated areas",
            BypassableControl.CONTAINER_ESCAPE_PREVENTION: "Allow privileged container operations"
        }.get(control, "No description available")
        
        controls.append({
            'control': control.value,
            'name': control.name,
            'description': description
        })
    
    return controls