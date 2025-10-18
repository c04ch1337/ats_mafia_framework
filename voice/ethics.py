"""
ATS MAFIA Framework Ethics Safeguards

This module provides ethical safeguards and compliance monitoring for voice interactions
in the ATS MAFIA framework, ensuring responsible use in training scenarios.
"""

import os
import asyncio
import logging
import time
import uuid
import json
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone

from ..config.settings import FrameworkConfig
from ..core.logging import AuditLogger, AuditEventType, SecurityLevel


class InteractionType(Enum):
    """Types of interactions."""
    TRAINING = "training"
    TESTING = "testing"
    DEMONSTRATION = "demonstration"
    RESEARCH = "research"
    SIMULATION = "simulation"


class ComplianceLevel(Enum):
    """Compliance levels."""
    COMPLIANT = "compliant"
    WARNING = "warning"
    VIOLATION = "violation"
    CRITICAL = "critical"


class RiskLevel(Enum):
    """Risk levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ScopeType(Enum):
    """Scope types for interactions."""
    CONTROLLED = "controlled"
    SUPERVISED = "supervised"
    SANDBOXED = "sandboxed"
    ISOLATED = "isolated"


@dataclass
class ComplianceRule:
    """Compliance rule for ethical validation."""
    rule_id: str
    name: str
    description: str
    interaction_types: List[InteractionType]
    scope_types: List[ScopeType]
    conditions: Dict[str, Any]
    violation_level: ComplianceLevel
    enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'rule_id': self.rule_id,
            'name': self.name,
            'description': self.description,
            'interaction_types': [t.value for t in self.interaction_types],
            'scope_types': [s.value for s in self.scope_types],
            'conditions': self.conditions,
            'violation_level': self.violation_level.value,
            'enabled': self.enabled
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ComplianceRule':
        """Create from dictionary."""
        return cls(
            rule_id=data['rule_id'],
            name=data['name'],
            description=data['description'],
            interaction_types=[InteractionType(t) for t in data['interaction_types']],
            scope_types=[ScopeType(s) for s in data['scope_types']],
            conditions=data['conditions'],
            violation_level=ComplianceLevel(data['violation_level']),
            enabled=data.get('enabled', True)
        )


@dataclass
class ComplianceResult:
    """Result of compliance validation."""
    rule_id: str
    rule_name: str
    compliant: bool
    violation_level: ComplianceLevel
    risk_level: RiskLevel
    details: Dict[str, Any]
    recommendations: List[str]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'rule_id': self.rule_id,
            'rule_name': self.rule_name,
            'compliant': self.compliant,
            'violation_level': self.violation_level.value,
            'risk_level': self.risk_level.value,
            'details': self.details,
            'recommendations': self.recommendations,
            'timestamp': self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ComplianceResult':
        """Create from dictionary."""
        return cls(
            rule_id=data['rule_id'],
            rule_name=data['rule_name'],
            compliant=data['compliant'],
            violation_level=ComplianceLevel(data['violation_level']),
            risk_level=RiskLevel(data['risk_level']),
            details=data['details'],
            recommendations=data['recommendations'],
            timestamp=datetime.fromisoformat(data['timestamp'])
        )


@dataclass
class InteractionSession:
    """Session for tracking interactions."""
    session_id: str
    interaction_id: str
    interaction_type: InteractionType
    scope_id: str
    scope_type: ScopeType
    participant_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    compliance_results: List[ComplianceResult] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'session_id': self.session_id,
            'interaction_id': self.interaction_id,
            'interaction_type': self.interaction_type.value,
            'scope_id': self.scope_id,
            'scope_type': self.scope_type.value,
            'participant_id': self.participant_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'compliance_results': [result.to_dict() for result in self.compliance_results],
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InteractionSession':
        """Create from dictionary."""
        return cls(
            session_id=data['session_id'],
            interaction_id=data['interaction_id'],
            interaction_type=InteractionType(data['interaction_type']),
            scope_id=data['scope_id'],
            scope_type=ScopeType(data['scope_type']),
            participant_id=data['participant_id'],
            start_time=datetime.fromisoformat(data['start_time']),
            end_time=datetime.fromisoformat(data['end_time']) if data.get('end_time') else None,
            compliance_results=[ComplianceResult.from_dict(r) for r in data.get('compliance_results', [])],
            metadata=data.get('metadata', {})
        )
    
    def get_duration(self) -> float:
        """Get session duration in seconds."""
        end_time = self.end_time or datetime.now(timezone.utc)
        return (end_time - self.start_time).total_seconds()
    
    def get_compliance_summary(self) -> Dict[str, Any]:
        """Get compliance summary for the session."""
        if not self.compliance_results:
            return {
                'total_rules': 0,
                'compliant_rules': 0,
                'violations': 0,
                'warnings': 0,
                'critical_violations': 0,
                'overall_compliance': ComplianceLevel.COMPLIANT
            }
        
        total_rules = len(self.compliance_results)
        compliant_rules = sum(1 for r in self.compliance_results if r.compliant)
        violations = sum(1 for r in self.compliance_results if r.violation_level == ComplianceLevel.VIOLATION)
        warnings = sum(1 for r in self.compliance_results if r.violation_level == ComplianceLevel.WARNING)
        critical_violations = sum(1 for r in self.compliance_results if r.violation_level == ComplianceLevel.CRITICAL)
        
        # Determine overall compliance
        if critical_violations > 0:
            overall_compliance = ComplianceLevel.CRITICAL
        elif violations > 0:
            overall_compliance = ComplianceLevel.VIOLATION
        elif warnings > 0:
            overall_compliance = ComplianceLevel.WARNING
        else:
            overall_compliance = ComplianceLevel.COMPLIANT
        
        return {
            'total_rules': total_rules,
            'compliant_rules': compliant_rules,
            'violations': violations,
            'warnings': warnings,
            'critical_violations': critical_violations,
            'overall_compliance': overall_compliance.value
        }


class ComplianceEngine:
    """Engine for validating compliance with ethical rules."""
    
    def __init__(self, config: FrameworkConfig):
        """
        Initialize the compliance engine.
        
        Args:
            config: Framework configuration
        """
        self.config = config
        self.logger = logging.getLogger("compliance_engine")
        
        # Compliance rules
        self.rules: Dict[str, ComplianceRule] = {}
        
        # Load default rules
        self._load_default_rules()
    
    def _load_default_rules(self) -> None:
        """Load default compliance rules."""
        # Training environment rule
        self.rules['training_environment'] = ComplianceRule(
            rule_id='training_environment',
            name='Training Environment Validation',
            description='Ensures interactions occur in controlled training environment',
            interaction_types=[InteractionType.TRAINING, InteractionType.SIMULATION],
            scope_types=[ScopeType.CONTROLLED, ScopeType.SUPERVISED, ScopeType.SANDBOXED, ScopeType.ISOLATED],
            conditions={
                'requires_supervisor': True,
                'requires_consent': True,
                'requires_recording_notification': True
            },
            violation_level=ComplianceLevel.CRITICAL
        )
        
        # Consent rule
        self.rules['participant_consent'] = ComplianceRule(
            rule_id='participant_consent',
            name='Participant Consent',
            description='Ensures participants have given informed consent',
            interaction_types=[InteractionType.TRAINING, InteractionType.TESTING, InteractionType.RESEARCH],
            scope_types=[ScopeType.CONTROLLED, ScopeType.SUPERVISED, ScopeType.SANDBOXED, ScopeType.ISOLATED],
            conditions={
                'requires_explicit_consent': True,
                'requires_documentation': True,
                'requires_withdrawal_option': True
            },
            violation_level=ComplianceLevel.CRITICAL
        )
        
        # Data protection rule
        self.rules['data_protection'] = ComplianceRule(
            rule_id='data_protection',
            name='Data Protection',
            description='Ensures participant data is protected',
            interaction_types=[InteractionType.TRAINING, InteractionType.TESTING, InteractionType.RESEARCH],
            scope_types=[ScopeType.CONTROLLED, ScopeType.SUPERVISED, ScopeType.SANDBOXED, ScopeType.ISOLATED],
            conditions={
                'requires_encryption': True,
                'requires_anonymization': True,
                'requires_secure_storage': True,
                'retention_limit_days': 30
            },
            violation_level=ComplianceLevel.VIOLATION
        )
        
        # Recording notification rule
        self.rules['recording_notification'] = ComplianceRule(
            rule_id='recording_notification',
            name='Recording Notification',
            description='Ensures participants are notified of recording',
            interaction_types=[InteractionType.TRAINING, InteractionType.TESTING, InteractionType.DEMONSTRATION],
            scope_types=[ScopeType.CONTROLLED, ScopeType.SUPERVISED, ScopeType.SANDBOXED, ScopeType.ISOLATED],
            conditions={
                'requires_notification': True,
                'requires_explicit_acknowledgment': True
            },
            violation_level=ComplianceLevel.WARNING
        )
        
        # Time limit rule
        self.rules['time_limit'] = ComplianceRule(
            rule_id='time_limit',
            name='Interaction Time Limit',
            description='Ensures interactions don\'t exceed time limits',
            interaction_types=[InteractionType.TRAINING, InteractionType.TESTING, InteractionType.SIMULATION],
            scope_types=[ScopeType.CONTROLLED, ScopeType.SUPERVISED, ScopeType.SANDBOXED, ScopeType.ISOLATED],
            conditions={
                'max_duration_minutes': 60,
                'requires_breaks': True,
                'break_interval_minutes': 20
            },
            violation_level=ComplianceLevel.WARNING
        )
        
        # Content boundaries rule
        self.rules['content_boundaries'] = ComplianceRule(
            rule_id='content_boundaries',
            name='Content Boundaries',
            description='Ensures content stays within appropriate boundaries',
            interaction_types=[InteractionType.TRAINING, InteractionType.TESTING, InteractionType.SIMULATION],
            scope_types=[ScopeType.CONTROLLED, ScopeType.SUPERVISED, ScopeType.SANDBOXED, ScopeType.ISOLATED],
            conditions={
                'prohibited_topics': ['illegal_activities', 'harmful_content', 'discrimination'],
                'requires_content_review': True,
                'requires_safe_topic_validation': True
            },
            violation_level=ComplianceLevel.CRITICAL
        )
        
        # Supervisor oversight rule
        self.rules['supervisor_oversight'] = ComplianceRule(
            rule_id='supervisor_oversight',
            name='Supervisor Oversight',
            description='Ensures proper supervisor oversight',
            interaction_types=[InteractionType.TRAINING, InteractionType.TESTING, InteractionType.RESEARCH],
            scope_types=[ScopeType.CONTROLLED, ScopeType.SUPERVISED],
            conditions={
                'requires_active_supervisor': True,
                'requires_supervisor_authentication': True,
                'requires_supervisor_logging': True,
                'requires_intervention_capability': True
            },
            violation_level=ComplianceLevel.VIOLATION
        )
    
    async def validate_interaction(self, 
                                 interaction_id: str,
                                 interaction_type: InteractionType,
                                 scope_id: str,
                                 participant_id: str,
                                 content: Dict[str, Any]) -> List[ComplianceResult]:
        """
        Validate an interaction against compliance rules.
        
        Args:
            interaction_id: ID of the interaction
            interaction_type: Type of interaction
            scope_id: ID of the scope
            participant_id: ID of the participant
            content: Interaction content
            
        Returns:
            List of compliance results
        """
        results = []
        
        for rule in self.rules.values():
            if not rule.enabled:
                continue
            
            # Check if rule applies to this interaction type
            if interaction_type not in rule.interaction_types:
                continue
            
            # Validate rule
            result = await self._validate_rule(rule, interaction_id, scope_id, participant_id, content)
            results.append(result)
        
        return results
    
    async def _validate_rule(self, 
                           rule: ComplianceRule,
                           interaction_id: str,
                           scope_id: str,
                           participant_id: str,
                           content: Dict[str, Any]) -> ComplianceResult:
        """Validate a specific rule."""
        try:
            # Mock validation logic - in a real system, this would be more sophisticated
            compliant = True
            details = {}
            recommendations = []
            
            # Check conditions
            if rule.rule_id == 'training_environment':
                # Check if in controlled environment
                scope_type = content.get('scope_type', 'unknown')
                if scope_type not in ['controlled', 'supervised', 'sandboxed', 'isolated']:
                    compliant = False
                    details['scope_type'] = scope_type
                    recommendations.append("Ensure interaction occurs in controlled environment")
            
            elif rule.rule_id == 'participant_consent':
                # Check if consent was obtained
                consent_obtained = content.get('consent_obtained', False)
                if not consent_obtained:
                    compliant = False
                    details['consent_obtained'] = consent_obtained
                    recommendations.append("Obtain explicit participant consent")
            
            elif rule.rule_id == 'data_protection':
                # Check data protection measures
                encryption_enabled = content.get('encryption_enabled', False)
                anonymization_enabled = content.get('anonymization_enabled', False)
                
                if not encryption_enabled or not anonymization_enabled:
                    compliant = False
                    details.update({
                        'encryption_enabled': encryption_enabled,
                        'anonymization_enabled': anonymization_enabled
                    })
                    recommendations.append("Enable data encryption and anonymization")
            
            elif rule.rule_id == 'recording_notification':
                # Check if recording was notified
                recording_notified = content.get('recording_notified', False)
                if not recording_notified:
                    compliant = False
                    details['recording_notified'] = recording_notified
                    recommendations.append("Notify participants about recording")
            
            elif rule.rule_id == 'time_limit':
                # Check time limits
                duration_minutes = content.get('duration_minutes', 0)
                max_duration = rule.conditions.get('max_duration_minutes', 60)
                
                if duration_minutes > max_duration:
                    compliant = False
                    details.update({
                        'duration_minutes': duration_minutes,
                        'max_duration_minutes': max_duration
                    })
                    recommendations.append(f"Limit interaction duration to {max_duration} minutes")
            
            elif rule.rule_id == 'content_boundaries':
                # Check content boundaries
                content_topics = content.get('topics', [])
                prohibited_topics = rule.conditions.get('prohibited_topics', [])
                
                violations = [topic for topic in content_topics if topic in prohibited_topics]
                if violations:
                    compliant = False
                    details['violations'] = violations
                    recommendations.append("Remove prohibited content topics")
            
            elif rule.rule_id == 'supervisor_oversight':
                # Check supervisor oversight
                supervisor_present = content.get('supervisor_present', False)
                supervisor_authenticated = content.get('supervisor_authenticated', False)
                
                if not supervisor_present or not supervisor_authenticated:
                    compliant = False
                    details.update({
                        'supervisor_present': supervisor_present,
                        'supervisor_authenticated': supervisor_authenticated
                    })
                    recommendations.append("Ensure supervisor is present and authenticated")
            
            # Determine risk level
            if not compliant:
                if rule.violation_level == ComplianceLevel.CRITICAL:
                    risk_level = RiskLevel.CRITICAL
                elif rule.violation_level == ComplianceLevel.VIOLATION:
                    risk_level = RiskLevel.HIGH
                else:
                    risk_level = RiskLevel.MEDIUM
            else:
                risk_level = RiskLevel.LOW
            
            return ComplianceResult(
                rule_id=rule.rule_id,
                rule_name=rule.name,
                compliant=compliant,
                violation_level=rule.violation_level if not compliant else ComplianceLevel.COMPLIANT,
                risk_level=risk_level,
                details=details,
                recommendations=recommendations,
                timestamp=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            self.logger.error(f"Error validating rule {rule.rule_id}: {e}")
            
            return ComplianceResult(
                rule_id=rule.rule_id,
                rule_name=rule.name,
                compliant=False,
                violation_level=ComplianceLevel.VIOLATION,
                risk_level=RiskLevel.HIGH,
                details={'error': str(e)},
                recommendations=["Review rule validation process"],
                timestamp=datetime.now(timezone.utc)
            )
    
    def add_rule(self, rule: ComplianceRule) -> None:
        """Add a compliance rule."""
        self.rules[rule.rule_id] = rule
    
    def remove_rule(self, rule_id: str) -> bool:
        """Remove a compliance rule."""
        if rule_id in self.rules:
            del self.rules[rule_id]
            return True
        return False
    
    def get_rules(self, interaction_type: Optional[InteractionType] = None) -> List[ComplianceRule]:
        """Get compliance rules, optionally filtered by interaction type."""
        rules = list(self.rules.values())
        if interaction_type:
            rules = [r for r in rules if interaction_type in r.interaction_types]
        return rules


class MonitoringEngine:
    """Engine for monitoring interactions in real-time."""
    
    def __init__(self, config: FrameworkConfig):
        """
        Initialize the monitoring engine.
        
        Args:
            config: Framework configuration
        """
        self.config = config
        self.logger = logging.getLogger("monitoring_engine")
        
        # Active sessions
        self.active_sessions: Dict[str, InteractionSession] = {}
        
        # Monitoring statistics
        self.statistics = {
            'total_sessions': 0,
            'active_sessions': 0,
            'compliance_violations': 0,
            'critical_violations': 0
        }
    
    async def start_monitoring(self, 
                              session_id: str,
                              interaction_id: str,
                              interaction_type: InteractionType,
                              scope_id: str,
                              scope_type: ScopeType,
                              participant_id: str,
                              metadata: Dict[str, Any] = None) -> bool:
        """
        Start monitoring an interaction session.
        
        Args:
            session_id: ID of the session
            interaction_id: ID of the interaction
            interaction_type: Type of interaction
            scope_id: ID of the scope
            scope_type: Type of scope
            participant_id: ID of the participant
            metadata: Additional metadata
            
        Returns:
            True if monitoring started successfully, False otherwise
        """
        try:
            # Create session
            session = InteractionSession(
                session_id=session_id,
                interaction_id=interaction_id,
                interaction_type=interaction_type,
                scope_id=scope_id,
                scope_type=scope_type,
                participant_id=participant_id,
                start_time=datetime.now(timezone.utc),
                metadata=metadata or {}
            )
            
            # Store session
            self.active_sessions[session_id] = session
            
            # Update statistics
            self.statistics['total_sessions'] += 1
            self.statistics['active_sessions'] += 1
            
            self.logger.info(f"Started monitoring session {session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting monitoring session {session_id}: {e}")
            return False
    
    async def monitor_event(self, 
                          session_id: str,
                          event_data: Dict[str, Any]) -> List[ComplianceResult]:
        """
        Monitor an event in a session.
        
        Args:
            session_id: ID of the session
            event_data: Event data
            
        Returns:
            List of compliance results
        """
        try:
            if session_id not in self.active_sessions:
                self.logger.warning(f"Session not found: {session_id}")
                return []
            
            session = self.active_sessions[session_id]
            
            # Get compliance engine
            compliance_engine = ComplianceEngine(self.config)
            
            # Validate event
            results = await compliance_engine.validate_interaction(
                interaction_id=session.interaction_id,
                interaction_type=session.interaction_type,
                scope_id=session.scope_id,
                participant_id=session.participant_id,
                content=event_data
            )
            
            # Add results to session
            session.compliance_results.extend(results)
            
            # Update statistics
            for result in results:
                if not result.compliant:
                    self.statistics['compliance_violations'] += 1
                    if result.violation_level == ComplianceLevel.CRITICAL:
                        self.statistics['critical_violations'] += 1
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error monitoring event in session {session_id}: {e}")
            return []
    
    async def end_monitoring(self, session_id: str) -> bool:
        """
        End monitoring of a session.
        
        Args:
            session_id: ID of the session
            
        Returns:
            True if monitoring ended successfully, False otherwise
        """
        try:
            if session_id not in self.active_sessions:
                self.logger.warning(f"Session not found: {session_id}")
                return False
            
            session = self.active_sessions[session_id]
            
            # Update end time
            session.end_time = datetime.now(timezone.utc)
            
            # Update statistics
            self.statistics['active_sessions'] -= 1
            
            # Remove from active sessions
            del self.active_sessions[session_id]
            
            self.logger.info(f"Ended monitoring session {session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error ending monitoring session {session_id}: {e}")
            return False
    
    def get_session(self, session_id: str) -> Optional[InteractionSession]:
        """Get a session by ID."""
        return self.active_sessions.get(session_id)
    
    def get_active_sessions(self) -> List[InteractionSession]:
        """Get all active sessions."""
        return list(self.active_sessions.values())
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get monitoring statistics."""
        return self.statistics.copy()
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        try:
            # End all active sessions
            session_ids = list(self.active_sessions.keys())
            for session_id in session_ids:
                await self.end_monitoring(session_id)
            
            self.logger.info("Monitoring engine cleanup complete")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")


class EthicsSafeguards:
    """
    Main ethics safeguards system for the ATS MAFIA framework.
    
    Coordinates compliance validation and monitoring.
    """
    
    def __init__(self, 
                 config: FrameworkConfig,
                 audit_logger: Optional[AuditLogger] = None):
        """
        Initialize the ethics safeguards.
        
        Args:
            config: Framework configuration
            audit_logger: Audit logger instance
        """
        self.config = config
        self.audit_logger = audit_logger
        self.logger = logging.getLogger("ethics_safeguards")
        
        # Components
        self.compliance_engine = ComplianceEngine(config)
        self.monitoring_engine = MonitoringEngine(config)
        
        # Statistics
        self.statistics = {
            'total_validations': 0,
            'compliance_violations': 0,
            'critical_violations': 0,
            'sessions_monitored': 0
        }
    
    async def validate_interaction(self, 
                                 interaction_id: str,
                                 interaction_type: InteractionType,
                                 scope_id: str,
                                 participant_id: str,
                                 content: Dict[str, Any]) -> List[ComplianceResult]:
        """
        Validate an interaction for compliance.
        
        Args:
            interaction_id: ID of the interaction
            interaction_type: Type of interaction
            scope_id: ID of the scope
            participant_id: ID of the participant
            content: Interaction content
            
        Returns:
            List of compliance results
        """
        try:
            # Validate interaction
            results = await self.compliance_engine.validate_interaction(
                interaction_id=interaction_id,
                interaction_type=interaction_type,
                scope_id=scope_id,
                participant_id=participant_id,
                content=content
            )
            
            # Update statistics
            self.statistics['total_validations'] += 1
            
            # Check for violations
            violations = [r for r in results if not r.compliant]
            if violations:
                self.statistics['compliance_violations'] += len(violations)
                
                critical_violations = [r for r in violations if r.violation_level == ComplianceLevel.CRITICAL]
                if critical_violations:
                    self.statistics['critical_violations'] += len(critical_violations)
                
                # Log to audit
                if self.audit_logger:
                    self.audit_logger.audit(
                        event_type=AuditEventType.SECURITY_EVENT,
                        action="ethics_violation_detected",
                        details={
                            'interaction_id': interaction_id,
                            'interaction_type': interaction_type.value,
                            'participant_id': participant_id,
                            'violations': [r.to_dict() for r in violations]
                        },
                        security_level=SecurityLevel.HIGH
                    )
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error validating interaction {interaction_id}: {e}")
            raise
    
    async def start_monitoring(self, 
                              session_id: str,
                              interaction_id: str,
                              interaction_type: InteractionType,
                              scope_id: str,
                              scope_type: ScopeType,
                              participant_id: str,
                              metadata: Dict[str, Any] = None) -> bool:
        """
        Start monitoring an interaction session.
        
        Args:
            session_id: ID of the session
            interaction_id: ID of the interaction
            interaction_type: Type of interaction
            scope_id: ID of the scope
            scope_type: Type of scope
            participant_id: ID of the participant
            metadata: Additional metadata
            
        Returns:
            True if monitoring started successfully, False otherwise
        """
        try:
            success = await self.monitoring_engine.start_monitoring(
                session_id=session_id,
                interaction_id=interaction_id,
                interaction_type=interaction_type,
                scope_id=scope_id,
                scope_type=scope_type,
                participant_id=participant_id,
                metadata=metadata
            )
            
            if success:
                self.statistics['sessions_monitored'] += 1
                
                # Log to audit
                if self.audit_logger:
                    self.audit_logger.audit(
                        event_type=AuditEventType.SYSTEM_EVENT,
                        action="ethics_monitoring_started",
                        details={
                            'session_id': session_id,
                            'interaction_id': interaction_id,
                            'interaction_type': interaction_type.value,
                            'participant_id': participant_id
                        },
                        security_level=SecurityLevel.MEDIUM
                    )
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error starting monitoring session {session_id}: {e}")
            return False
    
    async def monitor_event(self, 
                          session_id: str,
                          event_data: Dict[str, Any]) -> List[ComplianceResult]:
        """
        Monitor an event in a session.
        
        Args:
            session_id: ID of the session
            event_data: Event data
            
        Returns:
            List of compliance results
        """
        try:
            results = await self.monitoring_engine.monitor_event(session_id, event_data)
            
            # Check for critical violations
            critical_violations = [r for r in results if not r.compliant and r.violation_level == ComplianceLevel.CRITICAL]
            if critical_violations:
                # Log to audit
                if self.audit_logger:
                    self.audit_logger.audit(
                        event_type=AuditEventType.SECURITY_EVENT,
                        action="critical_ethics_violation",
                        details={
                            'session_id': session_id,
                            'violations': [r.to_dict() for r in critical_violations]
                        },
                        security_level=SecurityLevel.CRITICAL
                    )
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error monitoring event in session {session_id}: {e}")
            return []
    
    async def end_monitoring(self, session_id: str) -> bool:
        """
        End monitoring of a session.
        
        Args:
            session_id: ID of the session
            
        Returns:
            True if monitoring ended successfully, False otherwise
        """
        try:
            success = await self.monitoring_engine.end_monitoring(session_id)
            
            if success:
                # Get session for compliance summary
                session = self.monitoring_engine.get_session(session_id)
                if session:
                    compliance_summary = session.get_compliance_summary()
                    
                    # Log to audit
                    if self.audit_logger:
                        self.audit_logger.audit(
                            event_type=AuditEventType.SYSTEM_EVENT,
                            action="ethics_monitoring_ended",
                            details={
                                'session_id': session_id,
                                'duration': session.get_duration(),
                                'compliance_summary': compliance_summary
                            },
                            security_level=SecurityLevel.MEDIUM
                        )
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error ending monitoring session {session_id}: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get ethics safeguards statistics."""
        stats = self.statistics.copy()
        stats.update(self.monitoring_engine.get_statistics())
        return stats
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        try:
            await self.monitoring_engine.cleanup()
            self.logger.info("Ethics safeguards cleanup complete")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")


# Global ethics safeguards instance
_global_ethics_safeguards: Optional[EthicsSafeguards] = None


def get_ethics_safeguards() -> Optional[EthicsSafeguards]:
    """
    Get the global ethics safeguards instance.
    
    Returns:
        Global EthicsSafeguards instance or None if not initialized
    """
    return _global_ethics_safeguards


def initialize_ethics_safeguards(config: FrameworkConfig,
                               audit_logger: Optional[AuditLogger] = None) -> EthicsSafeguards:
    """
    Initialize the global ethics safeguards.
    
    Args:
        config: Framework configuration
        audit_logger: Audit logger instance
        
    Returns:
        Initialized EthicsSafeguards instance
    """
    global _global_ethics_safeguards
    _global_ethics_safeguards = EthicsSafeguards(config, audit_logger)
    return _global_ethics_safeguards


def shutdown_ethics_safeguards() -> None:
    """Shutdown the global ethics safeguards."""
    global _global_ethics_safeguards
    if _global_ethics_safeguards:
        asyncio.create_task(_global_ethics_safeguards.cleanup())
        _global_ethics_safeguards = None