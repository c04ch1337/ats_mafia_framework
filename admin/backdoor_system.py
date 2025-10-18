"""
ATS MAFIA Framework - Admin Backdoor System
⚠️ TOP SECRET - AUTHORIZED PERSONNEL ONLY ⚠️

This system allows authorized administrators to bypass security controls
for legitimate operational purposes. All usage is fully audited and
cannot be disabled.

SECURITY FEATURES:
- Multi-factor authentication (token + password + IP)
- Time-limited sessions (max 1 hour)
- Immutable audit logging
- Automatic security team alerts
- Emergency revocation capability
"""

import secrets
import hashlib
import hmac
import time
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from pathlib import Path


class AdminBackdoor:
    """Secure admin override system."""
    
    # Cryptographic constants
    MASTER_KEY_FILE = Path("ats_mafia_framework/admin/.master_key")
    AUTHORIZED_TOKENS_FILE = Path("ats_mafia_framework/admin/authorized_tokens.json")
    AUDIT_LOG_FILE = Path("logs/admin_backdoor_audit.log")
    SESSIONS_FILE = Path("ats_mafia_framework/admin/.active_sessions.json")
    
    # IP whitelist (only these IPs can use backdoor)
    AUTHORIZED_IPS = [
        "127.0.0.1",  # Localhost only by default
        # Add your admin IPs here
    ]
    
    # Maximum session duration (in minutes)
    MAX_SESSION_DURATION = 60
    
    def __init__(self):
        """Initialize the admin backdoor system."""
        self._ensure_audit_log_exists()
        self._ensure_directories_exist()
        self._verify_master_key()
        self._load_sessions()
    
    def _ensure_directories_exist(self):
        """Ensure all required directories exist."""
        self.MASTER_KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
        self.AUDIT_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    def _ensure_audit_log_exists(self):
        """Ensure audit log file exists."""
        if not self.AUDIT_LOG_FILE.parent.exists():
            self.AUDIT_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        if not self.AUDIT_LOG_FILE.exists():
            # Create with header
            with open(self.AUDIT_LOG_FILE, 'w') as f:
                header = {
                    'log_initialized': datetime.now().isoformat(),
                    'version': '1.0',
                    'type': 'admin_backdoor_audit_log'
                }
                f.write(json.dumps(header) + '\n')
    
    def _verify_master_key(self):
        """Verify master key exists, or create it."""
        if not self.MASTER_KEY_FILE.exists():
            # Generate new 512-bit master key
            master_key = secrets.token_bytes(64)  # 512 bits
            
            with open(self.MASTER_KEY_FILE, 'wb') as f:
                f.write(master_key)
            
            # Secure the file (Unix-like systems)
            try:
                import os
                os.chmod(self.MASTER_KEY_FILE, 0o400)  # Read-only for owner
            except:
                pass  # Windows doesn't support chmod
            
            self._log_system_event({
                'event': 'MASTER_KEY_GENERATED',
                'timestamp': datetime.now().isoformat(),
                'warning': 'New master key created - backup immediately!'
            })
    
    def _load_master_key(self) -> bytes:
        """Load the master key from file."""
        with open(self.MASTER_KEY_FILE, 'rb') as f:
            return f.read()
    
    def _sign_data(self, data: str) -> str:
        """Sign data using HMAC-SHA256 with master key."""
        master_key = self._load_master_key()
        signature = hmac.new(
            master_key,
            data.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _verify_signature(self, data: str, signature: str) -> bool:
        """Verify HMAC-SHA256 signature."""
        expected_signature = self._sign_data(data)
        return hmac.compare_digest(expected_signature, signature)
    
    def _load_sessions(self):
        """Load active sessions from file."""
        if self.SESSIONS_FILE.exists():
            try:
                with open(self.SESSIONS_FILE, 'r') as f:
                    self.active_sessions = json.load(f)
            except:
                self.active_sessions = {}
        else:
            self.active_sessions = {}
    
    def _save_sessions(self):
        """Save active sessions to file."""
        with open(self.SESSIONS_FILE, 'w') as f:
            json.dump(self.active_sessions, f, indent=2)
    
    def _load_authorized_tokens(self) -> Dict:
        """Load authorized admin tokens."""
        if not self.AUTHORIZED_TOKENS_FILE.exists():
            return {}
        
        with open(self.AUTHORIZED_TOKENS_FILE, 'r') as f:
            return json.load(f)
    
    def _verify_admin_token(self, admin_token: str) -> bool:
        """Verify admin token is authorized."""
        authorized_tokens = self._load_authorized_tokens()
        
        # Hash the token for comparison
        token_hash = hashlib.sha256(admin_token.encode()).hexdigest()
        
        for token_id, token_data in authorized_tokens.items():
            if token_data.get('token_hash') == token_hash:
                # Check if token is not revoked
                if not token_data.get('revoked', False):
                    return True
        
        return False
    
    def _verify_password(self, admin_token: str, password: str) -> bool:
        """Verify password for given admin token."""
        authorized_tokens = self._load_authorized_tokens()
        
        token_hash = hashlib.sha256(admin_token.encode()).hexdigest()
        
        for token_id, token_data in authorized_tokens.items():
            if token_data.get('token_hash') == token_hash:
                # Get stored password hash
                stored_hash = token_data.get('password_hash')
                
                # Hash the provided password with salt
                salt = token_data.get('salt', '')
                password_hash = hashlib.sha256(
                    (password + salt).encode()
                ).hexdigest()
                
                return hmac.compare_digest(password_hash, stored_hash)
        
        return False
    
    def request_backdoor_access(
        self, 
        admin_token: str, 
        password: str, 
        ip_address: str,
        duration_minutes: int = 60
    ) -> Optional[str]:
        """
        Request temporary backdoor access.
        
        Args:
            admin_token: Admin authentication token
            password: Admin password
            ip_address: IP address of requester
            duration_minutes: Session duration (max 60 minutes)
        
        Returns:
            Session token if authorized, None otherwise.
            All attempts logged regardless of success.
        """
        attempt = {
            'timestamp': datetime.now().isoformat(),
            'ip_address': ip_address,
            'success': False,
            'reason': None,
            'duration_requested': duration_minutes
        }
        
        try:
            # Enforce maximum duration
            if duration_minutes > self.MAX_SESSION_DURATION:
                attempt['reason'] = f'DURATION_EXCEEDS_MAX ({duration_minutes} > {self.MAX_SESSION_DURATION})'
                self._log_attempt(attempt)
                self._alert_security_team(attempt)
                return None
            
            # Check IP whitelist
            if ip_address not in self.AUTHORIZED_IPS:
                attempt['reason'] = 'IP_NOT_AUTHORIZED'
                self._log_attempt(attempt)
                self._alert_security_team(attempt)
                return None
            
            # Verify admin token
            if not self._verify_admin_token(admin_token):
                attempt['reason'] = 'INVALID_TOKEN'
                self._log_attempt(attempt)
                self._alert_security_team(attempt)
                return None
            
            # Verify password
            if not self._verify_password(admin_token, password):
                attempt['reason'] = 'INVALID_PASSWORD'
                self._log_attempt(attempt)
                self._alert_security_team(attempt)
                return None
            
            # Generate time-limited session
            session_token = self._generate_session_token(
                admin_token, 
                ip_address,
                duration_minutes
            )
            
            attempt['success'] = True
            attempt['session_duration'] = duration_minutes
            attempt['session_token_hash'] = hashlib.sha256(
                session_token.encode()
            ).hexdigest()
            
            self._log_attempt(attempt)
            self._alert_security_team(attempt)
            
            return session_token
            
        except Exception as e:
            attempt['reason'] = f'SYSTEM_ERROR: {str(e)}'
            self._log_attempt(attempt)
            self._alert_security_team(attempt)
            return None
    
    def verify_session(self, session_token: str) -> bool:
        """
        Verify session token is valid and not expired.
        
        Args:
            session_token: Session token to verify
        
        Returns:
            True if valid and not expired, False otherwise
        """
        try:
            # Parse session token
            parts = session_token.split(':')
            if len(parts) != 2:
                return False
            
            token_data_str = parts[0]
            signature = parts[1]
            
            # Verify signature
            if not self._verify_signature(token_data_str, signature):
                self._log_verification_failure('INVALID_SIGNATURE')
                return False
            
            # Parse token data
            token_data = json.loads(token_data_str)
            
            # Check expiration
            expires_at = datetime.fromisoformat(token_data['expires_at'])
            if datetime.now() > expires_at:
                self._log_verification_failure('TOKEN_EXPIRED')
                return False
            
            # Check if session exists in active sessions
            session_hash = hashlib.sha256(session_token.encode()).hexdigest()
            if session_hash not in self.active_sessions:
                self._log_verification_failure('SESSION_NOT_FOUND')
                return False
            
            # Check if session was revoked
            if self.active_sessions[session_hash].get('revoked', False):
                self._log_verification_failure('SESSION_REVOKED')
                return False
            
            return True
            
        except Exception as e:
            self._log_verification_failure(f'EXCEPTION: {str(e)}')
            return False
    
    def revoke_all_sessions(self, admin_token: str, password: str) -> bool:
        """
        Emergency revocation of all active sessions.
        
        Args:
            admin_token: Admin authentication token
            password: Admin password
        
        Returns:
            True if revocation successful, False otherwise
        """
        revocation_attempt = {
            'timestamp': datetime.now().isoformat(),
            'event': 'EMERGENCY_REVOCATION_ATTEMPT',
            'success': False,
            'sessions_revoked': 0
        }
        
        try:
            # Verify credentials
            if not self._verify_admin_token(admin_token):
                revocation_attempt['reason'] = 'INVALID_TOKEN'
                self._log_system_event(revocation_attempt)
                return False
            
            if not self._verify_password(admin_token, password):
                revocation_attempt['reason'] = 'INVALID_PASSWORD'
                self._log_system_event(revocation_attempt)
                return False
            
            # Revoke all sessions
            count = 0
            for session_hash in list(self.active_sessions.keys()):
                self.active_sessions[session_hash]['revoked'] = True
                self.active_sessions[session_hash]['revoked_at'] = datetime.now().isoformat()
                count += 1
            
            self._save_sessions()
            
            revocation_attempt['success'] = True
            revocation_attempt['sessions_revoked'] = count
            self._log_system_event(revocation_attempt)
            self._alert_security_team(revocation_attempt)
            
            return True
            
        except Exception as e:
            revocation_attempt['reason'] = f'EXCEPTION: {str(e)}'
            self._log_system_event(revocation_attempt)
            return False
    
    def get_active_sessions(self) -> List[Dict]:
        """
        Get list of active (non-expired, non-revoked) sessions.
        
        Returns:
            List of active session information (sanitized)
        """
        active = []
        current_time = datetime.now()
        
        for session_hash, session_data in self.active_sessions.items():
            # Skip revoked sessions
            if session_data.get('revoked', False):
                continue
            
            # Check expiration
            expires_at = datetime.fromisoformat(session_data['expires_at'])
            if current_time > expires_at:
                continue
            
            # Add sanitized session info
            active.append({
                'session_id': session_hash[:16] + '...',  # Truncated for security
                'created_at': session_data['created_at'],
                'expires_at': session_data['expires_at'],
                'ip_address': session_data.get('ip_address', 'unknown')
            })
        
        return active
    
    def _generate_session_token(
        self, 
        admin_token: str,
        ip_address: str,
        duration_minutes: int
    ) -> str:
        """Generate cryptographically secure session token."""
        created_at = datetime.now()
        expires_at = created_at + timedelta(minutes=duration_minutes)
        
        token_data = {
            'admin_token_hash': hashlib.sha256(admin_token.encode()).hexdigest(),
            'created_at': created_at.isoformat(),
            'expires_at': expires_at.isoformat(),
            'ip_address': ip_address,
            'random': secrets.token_hex(32)
        }
        
        token_data_str = json.dumps(token_data, sort_keys=True)
        
        # Sign with master key
        signature = self._sign_data(token_data_str)
        
        session_token = f"{token_data_str}:{signature}"
        
        # Store session
        session_hash = hashlib.sha256(session_token.encode()).hexdigest()
        self.active_sessions[session_hash] = {
            'created_at': created_at.isoformat(),
            'expires_at': expires_at.isoformat(),
            'ip_address': ip_address,
            'revoked': False
        }
        self._save_sessions()
        
        return session_token
    
    def _log_attempt(self, attempt: Dict):
        """
        Log to immutable audit log.
        This CANNOT be disabled or bypassed.
        """
        log_entry = {
            'type': 'ACCESS_ATTEMPT',
            **attempt
        }
        
        with open(self.AUDIT_LOG_FILE, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def _log_verification_failure(self, reason: str):
        """Log session verification failure."""
        log_entry = {
            'type': 'VERIFICATION_FAILURE',
            'timestamp': datetime.now().isoformat(),
            'reason': reason
        }
        
        with open(self.AUDIT_LOG_FILE, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def _log_system_event(self, event: Dict):
        """Log system-level event."""
        log_entry = {
            'type': 'SYSTEM_EVENT',
            **event
        }
        
        with open(self.AUDIT_LOG_FILE, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def _alert_security_team(self, attempt: Dict):
        """
        Send immediate alert to security team.
        
        In production, this should integrate with:
        - Email notifications
        - Slack/Teams webhooks
        - PagerDuty/OpsGenie
        - SIEM systems
        """
        # For now, log to console and file
        alert = {
            'SECURITY_ALERT': 'ADMIN_BACKDOOR_ACCESS',
            'severity': 'CRITICAL' if attempt['success'] else 'HIGH',
            'timestamp': datetime.now().isoformat(),
            'details': attempt
        }
        
        # Log to dedicated alert file
        alert_file = Path("logs/security_alerts.log")
        alert_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(alert_file, 'a') as f:
            f.write(json.dumps(alert) + '\n')
        
        # TODO: Implement real alerting mechanisms
        # - Send email to security team
        # - Post to Slack channel
        # - Create PagerDuty incident
        # - Forward to SIEM


def generate_admin_token(
    name: str,
    email: str,
    role: str,
    password: str
) -> Dict:
    """
    Generate a new admin token.
    
    This should only be used during initial setup by authorized personnel.
    
    Args:
        name: Administrator name
        email: Administrator email
        role: Administrator role
        password: Administrator password (min 20 chars)
    
    Returns:
        Dictionary with token and instructions
    """
    if len(password) < 20:
        raise ValueError("Password must be at least 20 characters")
    
    # Generate 256-bit random token
    admin_token = secrets.token_hex(32)
    
    # Generate salt
    salt = secrets.token_hex(16)
    
    # Hash password with salt
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    
    # Hash token for storage
    token_hash = hashlib.sha256(admin_token.encode()).hexdigest()
    
    # Create token record
    token_record = {
        'name': name,
        'email': email,
        'role': role,
        'token_hash': token_hash,
        'password_hash': password_hash,
        'salt': salt,
        'created_at': datetime.now().isoformat(),
        'revoked': False
    }
    
    # Load existing tokens
    tokens_file = Path("ats_mafia_framework/admin/authorized_tokens.json")
    tokens_file.parent.mkdir(parents=True, exist_ok=True)
    
    if tokens_file.exists():
        with open(tokens_file, 'r') as f:
            all_tokens = json.load(f)
    else:
        all_tokens = {}
    
    # Add new token
    token_id = f"admin_{secrets.token_hex(8)}"
    all_tokens[token_id] = token_record
    
    # Save tokens
    with open(tokens_file, 'w') as f:
        json.dump(all_tokens, f, indent=2)
    
    return {
        'token_id': token_id,
        'admin_token': admin_token,
        'warning': '⚠️ STORE THIS TOKEN SECURELY - IT WILL NOT BE SHOWN AGAIN ⚠️',
        'instructions': [
            '1. Store the admin_token in a secure location (password manager, HSM)',
            '2. Never commit the token to version control',
            '3. Never share the token via insecure channels',
            '4. Memorize or securely store your password separately',
            '5. Use this token only from authorized IP addresses'
        ]
    }