"""
Real-time ATT&CK Technique Usage Tracker
Monitors and logs techniques used during training sessions
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field, asdict
import logging
import json
from pathlib import Path


@dataclass
class TechniqueExecution:
    """Record of a technique execution during training"""
    technique_id: str
    technique_name: str
    tactic: str
    timestamp: datetime
    agent_id: str
    session_id: str
    success: bool
    detection_triggered: bool
    execution_time_seconds: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class VoiceTechniqueExecution(TechniqueExecution):
    """Voice-specific technique execution tracking for Puppet Master"""
    call_id: str = ""
    call_duration_seconds: float = 0.0
    target_response_type: str = "unknown"  # cooperative, suspicious, hostile
    credential_obtained: bool = False
    information_gathered: Dict[str, Any] = field(default_factory=dict)
    persona_used: str = "default"
    psychological_triggers_used: List[str] = field(default_factory=list)
    voice_recording_path: Optional[str] = None
    transcript_path: Optional[str] = None


class TechniqueTracker:
    """
    Track ATT&CK technique usage in real-time during training sessions
    
    Features:
    - Real-time technique execution logging
    - Session-level and agent-level statistics
    - Success/detection rate tracking
    - Integration with audit logging
    - Persistent storage of execution history
    """
    
    def __init__(self, attack_framework, audit_logger=None, storage_path: Optional[str] = None):
        """
        Initialize technique tracker
        
        Args:
            attack_framework: ATTACKFramework instance
            audit_logger: Optional audit logger for compliance
            storage_path: Optional path for persistent storage
        """
        self.attack = attack_framework
        self.audit_logger = audit_logger
        self.logger = logging.getLogger("technique_tracker")
        self.storage_path = storage_path or "ats_mafia_framework/analytics/data/technique_executions.json"
        
        # In-memory storage
        self.executions: List[TechniqueExecution] = []
        self.session_techniques: Dict[str, List[str]] = {}
        self.agent_techniques: Dict[str, List[str]] = {}
        
        # Load existing executions if storage exists
        self._load_executions()
    
    def record_technique(self,
                        technique_id: str,
                        agent_id: str,
                        session_id: str,
                        success: bool,
                        detection_triggered: bool,
                        execution_time: float,
                        metadata: Optional[Dict] = None) -> None:
        """
        Record technique execution
        
        Args:
            technique_id: ATT&CK technique ID (e.g., 'T1055')
            agent_id: Agent identifier
            session_id: Training session identifier
            success: Whether execution was successful
            detection_triggered: Whether blue team detected the technique
            execution_time: Execution time in seconds
            metadata: Additional execution metadata
        """
        
        # Validate technique exists
        technique = self.attack.get_technique(technique_id)
        if not technique:
            self.logger.warning(f"Unknown technique ID: {technique_id}")
            return
        
        # Create execution record
        execution = TechniqueExecution(
            technique_id=technique_id,
            technique_name=technique['name'],
            tactic=technique['tactics'][0] if technique['tactics'] else 'unknown',
            timestamp=datetime.now(),
            agent_id=agent_id,
            session_id=session_id,
            success=success,
            detection_triggered=detection_triggered,
            execution_time_seconds=execution_time,
            metadata=metadata or {}
        )
        
        # Store execution
        self.executions.append(execution)
        
        # Update session tracking
        if session_id not in self.session_techniques:
            self.session_techniques[session_id] = []
        self.session_techniques[session_id].append(technique_id)
        
        # Update agent tracking
        if agent_id not in self.agent_techniques:
            self.agent_techniques[agent_id] = []
        self.agent_techniques[agent_id].append(technique_id)
        
        # Audit log
        if self.audit_logger:
            self.audit_logger.audit(
                event_type="TECHNIQUE_EXECUTED",
                action=f"technique_{technique_id}_executed",
                details={
                    'technique_id': technique_id,
                    'technique_name': technique['name'],
                    'tactic': execution.tactic,
                    'agent_id': agent_id,
                    'session_id': session_id,
                    'success': success,
                    'detected': detection_triggered,
                    'execution_time': execution_time
                },
                security_level="LOW"
            )
        
        # Log execution
        self.logger.info(
            f"Technique executed: {technique_id} ({technique['name']}) "
            f"by {agent_id} in session {session_id} - "
            f"{'SUCCESS' if success else 'FAILED'}"
            f"{' [DETECTED]' if detection_triggered else ''}"
        )
        
        # Persist to storage
        self._save_executions()
    
    def get_session_coverage(self, session_id: str) -> Dict[str, Any]:
        """
        Get ATT&CK coverage for a specific training session
        
        Args:
            session_id: Session identifier
            
        Returns:
            Coverage analysis dictionary
        """
        technique_ids = self.session_techniques.get(session_id, [])
        unique_techniques = list(set(technique_ids))
        
        coverage = self.attack.validate_technique_coverage(unique_techniques)
        coverage['session_id'] = session_id
        coverage['total_executions'] = len(technique_ids)
        coverage['unique_techniques'] = len(unique_techniques)
        
        return coverage
    
    def get_agent_coverage(self, agent_id: str) -> Dict[str, Any]:
        """
        Get ATT&CK coverage for a specific agent across all sessions
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Coverage analysis dictionary
        """
        technique_ids = self.agent_techniques.get(agent_id, [])
        unique_techniques = list(set(technique_ids))
        
        coverage = self.attack.validate_technique_coverage(unique_techniques)
        coverage['agent_id'] = agent_id
        coverage['total_executions'] = len(technique_ids)
        coverage['unique_techniques'] = len(unique_techniques)
        
        return coverage
    
    def get_technique_statistics(self, technique_id: str) -> Dict[str, Any]:
        """
        Get statistics for a specific technique across all sessions
        
        Args:
            technique_id: ATT&CK technique ID
            
        Returns:
            Technique statistics dictionary
        """
        executions = [e for e in self.executions if e.technique_id == technique_id]
        
        if not executions:
            return {
                'technique_id': technique_id,
                'total_executions': 0
            }
        
        successes = sum(1 for e in executions if e.success)
        detections = sum(1 for e in executions if e.detection_triggered)
        avg_time = sum(e.execution_time_seconds for e in executions) / len(executions)
        
        return {
            'technique_id': technique_id,
            'technique_name': executions[0].technique_name,
            'total_executions': len(executions),
            'success_count': successes,
            'success_rate': successes / len(executions) if executions else 0,
            'detection_count': detections,
            'detection_rate': detections / len(executions) if executions else 0,
            'average_execution_time': avg_time,
            'unique_agents': len(set(e.agent_id for e in executions)),
            'unique_sessions': len(set(e.session_id for e in executions)),
            'first_used': min(e.timestamp for e in executions).isoformat(),
            'last_used': max(e.timestamp for e in executions).isoformat()
        }
    
    def get_session_timeline(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get chronological timeline of techniques used in a session
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of technique executions in chronological order
        """
        session_executions = [
            e for e in self.executions 
            if e.session_id == session_id
        ]
        
        # Sort by timestamp
        session_executions.sort(key=lambda e: e.timestamp)
        
        return [e.to_dict() for e in session_executions]
    
    def get_all_statistics(self) -> Dict[str, Any]:
        """
        Get overall tracking statistics
        
        Returns:
            Dictionary with comprehensive statistics
        """
        if not self.executions:
            return {
                'total_executions': 0,
                'unique_techniques': 0,
                'unique_agents': 0,
                'unique_sessions': 0
            }
        
        unique_techniques = set(e.technique_id for e in self.executions)
        unique_agents = set(e.agent_id for e in self.executions)
        unique_sessions = set(e.session_id for e in self.executions)
        
        total_successes = sum(1 for e in self.executions if e.success)
        total_detections = sum(1 for e in self.executions if e.detection_triggered)
        
        return {
            'total_executions': len(self.executions),
            'unique_techniques': len(unique_techniques),
            'unique_agents': len(unique_agents),
            'unique_sessions': len(unique_sessions),
            'overall_success_rate': total_successes / len(self.executions) if self.executions else 0,
            'overall_detection_rate': total_detections / len(self.executions) if self.executions else 0,
            'average_execution_time': sum(e.execution_time_seconds for e in self.executions) / len(self.executions) if self.executions else 0,
            'first_execution': min(e.timestamp for e in self.executions).isoformat() if self.executions else None,
            'last_execution': max(e.timestamp for e in self.executions).isoformat() if self.executions else None
        }
    
    def _load_executions(self) -> None:
        """Load executions from persistent storage"""
        try:
            if Path(self.storage_path).exists():
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    
                # Reconstruct execution objects
                for exec_data in data.get('executions', []):
                    exec_data['timestamp'] = datetime.fromisoformat(exec_data['timestamp'])
                    execution = TechniqueExecution(**exec_data)
                    self.executions.append(execution)
                
                # Rebuild indices
                for execution in self.executions:
                    # Session index
                    if execution.session_id not in self.session_techniques:
                        self.session_techniques[execution.session_id] = []
                    self.session_techniques[execution.session_id].append(execution.technique_id)
                    
                    # Agent index
                    if execution.agent_id not in self.agent_techniques:
                        self.agent_techniques[execution.agent_id] = []
                    self.agent_techniques[execution.agent_id].append(execution.technique_id)
                
                self.logger.info(f"Loaded {len(self.executions)} technique executions from storage")
        
        except Exception as e:
            self.logger.error(f"Error loading executions: {e}")
    
    def _save_executions(self) -> None:
        """Save executions to persistent storage"""
        try:
            Path(self.storage_path).parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                'executions': [e.to_dict() for e in self.executions],
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
        
        except Exception as e:
            self.logger.error(f"Error saving executions: {e}")


class VoiceTechniqueTracker(TechniqueTracker):
    """
    Specialized tracker for voice-based social engineering techniques
    Extends base tracker with voice operation specific fields
    """
    
    def record_voice_technique(self,
                              technique_id: str,
                              agent_id: str,
                              session_id: str,
                              call_id: str,
                              call_duration: float,
                              success: bool,
                              metadata: Dict) -> None:
        """
        Record voice technique execution with call-specific data
        
        Args:
            technique_id: ATT&CK technique ID
            agent_id: Agent identifier (typically puppet_master)
            session_id: Training session identifier
            call_id: Unique call identifier
            call_duration: Total call duration in seconds
            success: Whether the voice operation was successful
            metadata: Voice operation metadata including:
                - response_type: Target response (cooperative, suspicious, hostile)
                - credential_obtained: Whether credentials were harvested
                - information: Dictionary of gathered information
                - persona: Voice persona used
                - triggers: Psychological triggers employed
                - recording_path: Path to call recording
                - transcript_path: Path to call transcript
        """
        
        technique = self.attack.get_technique(technique_id)
        if not technique:
            self.logger.warning(f"Unknown technique ID: {technique_id}")
            return
        
        # Determine if detected based on suspicion
        detection_triggered = metadata.get('target_suspicious', False) or metadata.get('response_type') == 'hostile'
        
        # Create voice-specific execution record
        voice_execution = VoiceTechniqueExecution(
            technique_id=technique_id,
            technique_name=technique['name'],
            tactic=technique['tactics'][0] if technique['tactics'] else 'unknown',
            timestamp=datetime.now(),
            agent_id=agent_id,
            session_id=session_id,
            success=success,
            detection_triggered=detection_triggered,
            execution_time_seconds=call_duration,
            call_id=call_id,
            call_duration_seconds=call_duration,
            target_response_type=metadata.get('response_type', 'unknown'),
            credential_obtained=metadata.get('credential_obtained', False),
            information_gathered=metadata.get('information', {}),
            persona_used=metadata.get('persona', 'default'),
            psychological_triggers_used=metadata.get('triggers', []),
            voice_recording_path=metadata.get('recording_path'),
            transcript_path=metadata.get('transcript_path'),
            metadata=metadata
        )
        
        # Store execution
        self.executions.append(voice_execution)
        
        # Update tracking indices
        if session_id not in self.session_techniques:
            self.session_techniques[session_id] = []
        self.session_techniques[session_id].append(technique_id)
        
        if agent_id not in self.agent_techniques:
            self.agent_techniques[agent_id] = []
        self.agent_techniques[agent_id].append(technique_id)
        
        # Audit log with voice-specific context
        if self.audit_logger:
            self.audit_logger.audit(
                event_type="VOICE_TECHNIQUE_EXECUTED",
                action=f"voice_technique_{technique_id}_executed",
                details={
                    'technique_id': technique_id,
                    'technique_name': technique['name'],
                    'call_id': call_id,
                    'call_duration': call_duration,
                    'persona': metadata.get('persona'),
                    'success': success,
                    'credential_obtained': metadata.get('credential_obtained', False),
                    'information_gathered': len(metadata.get('information', {})),
                    'psychological_triggers': metadata.get('triggers', []),
                    'recording_stored': voice_execution.voice_recording_path is not None,
                    'target_response': metadata.get('response_type')
                },
                security_level="HIGH"
            )
        
        # Log voice execution
        self.logger.info(
            f"Voice technique executed: {technique_id} ({technique['name']}) "
            f"by {agent_id} in call {call_id} - "
            f"{'SUCCESS' if success else 'FAILED'}"
            f"{' [CREDENTIAL OBTAINED]' if metadata.get('credential_obtained') else ''}"
            f"{' [DETECTED]' if detection_triggered else ''}"
        )
        
        # Persist to storage
        self._save_executions()
    
    def get_voice_statistics(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get voice-specific statistics
        
        Args:
            agent_id: Optional agent ID to filter by
            
        Returns:
            Voice operation statistics
        """
        # Filter voice executions
        voice_executions = [
            e for e in self.executions
            if isinstance(e, VoiceTechniqueExecution)
            and (agent_id is None or e.agent_id == agent_id)
        ]
        
        if not voice_executions:
            return {
                'total_calls': 0,
                'total_techniques': 0
            }
        
        # Calculate statistics
        total_calls = len(set(e.call_id for e in voice_executions))
        credentials_obtained = sum(1 for e in voice_executions if e.credential_obtained)
        
        # Response type breakdown
        response_types = {}
        for e in voice_executions:
            response_types[e.target_response_type] = response_types.get(e.target_response_type, 0) + 1
        
        # Persona usage
        persona_usage = {}
        for e in voice_executions:
            persona_usage[e.persona_used] = persona_usage.get(e.persona_used, 0) + 1
        
        # Psychological triggers
        all_triggers = []
        for e in voice_executions:
            all_triggers.extend(e.psychological_triggers_used)
        
        trigger_frequency = {}
        for trigger in all_triggers:
            trigger_frequency[trigger] = trigger_frequency.get(trigger, 0) + 1
        
        return {
            'total_calls': total_calls,
            'total_techniques': len(voice_executions),
            'unique_techniques': len(set(e.technique_id for e in voice_executions)),
            'credentials_obtained': credentials_obtained,
            'credential_harvest_rate': credentials_obtained / total_calls if total_calls > 0 else 0,
            'average_call_duration': sum(e.call_duration_seconds for e in voice_executions) / len(voice_executions) if voice_executions else 0,
            'response_type_breakdown': response_types,
            'persona_usage': persona_usage,
            'psychological_triggers': trigger_frequency,
            'success_rate': sum(1 for e in voice_executions if e.success) / len(voice_executions) if voice_executions else 0,
            'detection_rate': sum(1 for e in voice_executions if e.detection_triggered) / len(voice_executions) if voice_executions else 0
        }
    
    def export_session_report(self, session_id: str) -> Dict[str, Any]:
        """
        Export comprehensive session report
        
        Args:
            session_id: Session identifier
            
        Returns:
            Complete session report with timeline and statistics
        """
        # Get session executions
        session_executions = [e for e in self.executions if e.session_id == session_id]
        
        if not session_executions:
            return {
                'session_id': session_id,
                'error': 'No executions found for session'
            }
        
        # Build timeline
        timeline = sorted(session_executions, key=lambda e: e.timestamp)
        
        # Calculate statistics
        coverage = self.get_session_coverage(session_id)
        
        # Voice-specific stats if applicable
        voice_stats = None
        if any(isinstance(e, VoiceTechniqueExecution) for e in session_executions):
            voice_stats = self.get_voice_statistics()
        
        return {
            'session_id': session_id,
            'start_time': min(e.timestamp for e in session_executions).isoformat(),
            'end_time': max(e.timestamp for e in session_executions).isoformat(),
            'duration_minutes': (max(e.timestamp for e in session_executions) - min(e.timestamp for e in session_executions)).total_seconds() / 60,
            'coverage': coverage,
            'timeline': [e.to_dict() for e in timeline],
            'voice_statistics': voice_stats,
            'agents_involved': list(set(e.agent_id for e in session_executions)),
            'summary': {
                'total_techniques': len(session_executions),
                'unique_techniques': len(set(e.technique_id for e in session_executions)),
                'success_rate': sum(1 for e in session_executions if e.success) / len(session_executions),
                'detection_rate': sum(1 for e in session_executions if e.detection_triggered) / len(session_executions)
            }
        }