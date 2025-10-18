"""
ATS MAFIA Framework Phone Integration System

This module provides VoIP/SIP phone integration for the ATS MAFIA framework.
Includes call management, audio routing, and call recording capabilities.
"""

import os
import asyncio
import logging
import time
import uuid
import json
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone

from ..config.settings import FrameworkConfig
from ..core.logging import AuditLogger, AuditEventType, SecurityLevel
from .core import AudioSegment, AudioFormat


class CallState(Enum):
    """States of a phone call."""
    INITIALIZING = "initializing"
    DIALING = "dialing"
    RINGING = "ringing"
    CONNECTED = "connected"
    ON_HOLD = "on_hold"
    DISCONNECTED = "disconnected"
    FAILED = "failed"


class CallType(Enum):
    """Types of phone calls."""
    GENERAL = "general"
    IT_SUPPORT = "it_support"
    BANK_VERIFICATION = "bank_verification"
    SURVEY = "survey"
    VISHING_SIMULATION = "vishing_simulation"
    TRAINING = "training"


class ScenarioType(Enum):
    """Types of scenarios for calls."""
    TRAINING = "training"
    TESTING = "testing"
    DEMONSTRATION = "demonstration"
    LIVE = "live"


class AudioDirection(Enum):
    """Audio direction in calls."""
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    BIDIRECTIONAL = "bidirectional"


@dataclass
class CallParticipant:
    """Participant in a phone call."""
    participant_id: str
    name: str
    phone_number: str
    role: str  # caller, receiver, observer
    joined_at: datetime
    left_at: Optional[datetime] = None
    audio_enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'participant_id': self.participant_id,
            'name': self.name,
            'phone_number': self.phone_number,
            'role': self.role,
            'joined_at': self.joined_at.isoformat(),
            'left_at': self.left_at.isoformat() if self.left_at else None,
            'audio_enabled': self.audio_enabled,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CallParticipant':
        """Create from dictionary."""
        return cls(
            participant_id=data['participant_id'],
            name=data['name'],
            phone_number=data['phone_number'],
            role=data['role'],
            joined_at=datetime.fromisoformat(data['joined_at']),
            left_at=datetime.fromisoformat(data['left_at']) if data.get('left_at') else None,
            audio_enabled=data.get('audio_enabled', True),
            metadata=data.get('metadata', {})
        )


@dataclass
class PhoneCall:
    """A phone call."""
    call_id: str
    caller: CallParticipant
    receiver: CallParticipant
    call_type: CallType
    scenario_type: ScenarioType
    state: CallState
    start_time: datetime
    end_time: Optional[datetime] = None
    recording_enabled: bool = False
    recording_file: Optional[str] = None
    audio_direction: AudioDirection = AudioDirection.BIDIRECTIONAL
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'call_id': self.call_id,
            'caller': self.caller.to_dict(),
            'receiver': self.receiver.to_dict(),
            'call_type': self.call_type.value,
            'scenario_type': self.scenario_type.value,
            'state': self.state.value,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'recording_enabled': self.recording_enabled,
            'recording_file': self.recording_file,
            'audio_direction': self.audio_direction.value,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PhoneCall':
        """Create from dictionary."""
        return cls(
            call_id=data['call_id'],
            caller=CallParticipant.from_dict(data['caller']),
            receiver=CallParticipant.from_dict(data['receiver']),
            call_type=CallType(data['call_type']),
            scenario_type=ScenarioType(data['scenario_type']),
            state=CallState(data['state']),
            start_time=datetime.fromisoformat(data['start_time']),
            end_time=datetime.fromisoformat(data['end_time']) if data.get('end_time') else None,
            recording_enabled=data.get('recording_enabled', False),
            recording_file=data.get('recording_file'),
            audio_direction=AudioDirection(data.get('audio_direction', 'bidirectional')),
            metadata=data.get('metadata', {})
        )
    
    def get_duration(self) -> float:
        """Get call duration in seconds."""
        end_time = self.end_time or datetime.now(timezone.utc)
        return (end_time - self.start_time).total_seconds()


class VoIPProvider(Enum):
    """VoIP providers."""
    TWILIO = "twilio"
    PLIVO = "plivo"
    NEXMO = "nexmo"
    SIP = "sip"
    MOCK = "mock"


class MockVoIPProvider:
    """Mock VoIP provider for testing."""
    
    def __init__(self, config: FrameworkConfig):
        """
        Initialize the mock VoIP provider.
        
        Args:
            config: Framework configuration
        """
        self.config = config
        self.logger = logging.getLogger("mock_voip_provider")
        self.simulated_calls: Dict[str, PhoneCall] = {}
    
    async def make_call(self, 
                       from_number: str,
                       to_number: str,
                       call_id: str) -> bool:
        """
        Simulate making a call.
        
        Args:
            from_number: From phone number
            to_number: To phone number
            call_id: Call ID
            
        Returns:
            True if call initiated successfully, False otherwise
        """
        try:
            # Simulate call setup delay
            await asyncio.sleep(1.0)
            
            self.logger.info(f"Mock call initiated: {from_number} -> {to_number} (ID: {call_id})")
            return True
            
        except Exception as e:
            self.logger.error(f"Error making mock call: {e}")
            return False
    
    async def end_call(self, call_id: str) -> bool:
        """
        Simulate ending a call.
        
        Args:
            call_id: Call ID
            
        Returns:
            True if call ended successfully, False otherwise
        """
        try:
            # Simulate call teardown delay
            await asyncio.sleep(0.5)
            
            self.logger.info(f"Mock call ended: {call_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error ending mock call: {e}")
            return False
    
    async def send_audio(self, 
                        call_id: str,
                        audio_data: AudioSegment) -> bool:
        """
        Simulate sending audio.
        
        Args:
            call_id: Call ID
            audio_data: Audio data to send
            
        Returns:
            True if audio sent successfully, False otherwise
        """
        try:
            # Simulate audio transmission delay
            await asyncio.sleep(audio_data.duration * 0.1)
            
            self.logger.debug(f"Mock audio sent: {call_id} ({audio_data.duration:.2f}s)")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending mock audio: {e}")
            return False
    
    async def receive_audio(self, call_id: str) -> Optional[AudioSegment]:
        """
        Simulate receiving audio.
        
        Args:
            call_id: Call ID
            
        Returns:
            Received audio segment or None
        """
        try:
            # Simulate audio reception delay
            await asyncio.sleep(0.1)
            
            # Generate mock audio (silence)
            sample_rate = 16000
            duration = 0.1  # 100ms of audio
            samples = int(sample_rate * duration)
            audio_data = np.zeros(samples, dtype=np.float32)
            
            return AudioSegment(
                data=audio_data,
                sample_rate=sample_rate,
                channels=1,
                format=AudioFormat.PCM,
                duration=duration
            )
            
        except Exception as e:
            self.logger.error(f"Error receiving mock audio: {e}")
            return None


class PhoneCallManager:
    """
    Manager for phone calls in the ATS MAFIA framework.
    
    Handles call lifecycle, audio routing, and recording.
    """
    
    def __init__(self, 
                 config: FrameworkConfig,
                 audit_logger: Optional[AuditLogger] = None):
        """
        Initialize the phone call manager.
        
        Args:
            config: Framework configuration
            audit_logger: Audit logger instance
        """
        self.config = config
        self.audit_logger = audit_logger
        self.logger = logging.getLogger("phone_call_manager")
        
        # VoIP provider
        self.voip_provider = MockVoIPProvider(config)
        
        # Active calls
        self.active_calls: Dict[str, PhoneCall] = {}
        
        # Configuration
        self.from_number = config.get('voice.from_number', '+1234567890')
        self.recording_path = config.get('voice.recording_path', 'recordings/')
        
        # Statistics
        self.statistics = {
            'total_calls': 0,
            'successful_calls': 0,
            'failed_calls': 0,
            'total_duration': 0.0,
            'recorded_calls': 0
        }
        
        # Ensure recording directory exists
        os.makedirs(self.recording_path, exist_ok=True)
    
    async def make_call(self, 
                       phone_number: str,
                       participant_name: str,
                       call_type: CallType = CallType.GENERAL,
                       scenario_type: ScenarioType = ScenarioType.TRAINING,
                       recording_enabled: bool = False) -> str:
        """
        Make a phone call.
        
        Args:
            phone_number: Phone number to call
            participant_name: Name of the participant
            call_type: Type of call
            scenario_type: Type of scenario
            recording_enabled: Whether to record the call
            
        Returns:
            Call ID
        """
        try:
            # Generate call ID
            call_id = str(uuid.uuid4())
            
            # Create participants
            caller = CallParticipant(
                participant_id=str(uuid.uuid4()),
                name="System",
                phone_number=self.from_number,
                role="caller",
                joined_at=datetime.now(timezone.utc)
            )
            
            receiver = CallParticipant(
                participant_id=str(uuid.uuid4()),
                name=participant_name,
                phone_number=phone_number,
                role="receiver",
                joined_at=datetime.now(timezone.utc)
            )
            
            # Create call
            call = PhoneCall(
                call_id=call_id,
                caller=caller,
                receiver=receiver,
                call_type=call_type,
                scenario_type=scenario_type,
                state=CallState.INITIALIZING,
                start_time=datetime.now(timezone.utc),
                recording_enabled=recording_enabled
            )
            
            # Store call
            self.active_calls[call_id] = call
            
            # Update statistics
            self.statistics['total_calls'] += 1
            
            # Initiate call
            call.state = CallState.DIALING
            
            success = await self.voip_provider.make_call(
                from_number=self.from_number,
                to_number=phone_number,
                call_id=call_id
            )
            
            if success:
                call.state = CallState.CONNECTED
                self.statistics['successful_calls'] += 1
                
                # Start recording if enabled
                if recording_enabled:
                    await self._start_recording(call)
                
                # Log to audit
                if self.audit_logger:
                    self.audit_logger.audit(
                        event_type=AuditEventType.SYSTEM_EVENT,
                        action="phone_call_initiated",
                        details={
                            'call_id': call_id,
                            'phone_number': phone_number,
                            'participant_name': participant_name,
                            'call_type': call_type.value,
                            'scenario_type': scenario_type.value,
                            'recording_enabled': recording_enabled
                        },
                        security_level=SecurityLevel.MEDIUM
                    )
                
                self.logger.info(f"Call initiated: {call_id} to {phone_number}")
            else:
                call.state = CallState.FAILED
                self.statistics['failed_calls'] += 1
                
                # Log to audit
                if self.audit_logger:
                    self.audit_logger.audit(
                        event_type=AuditEventType.SYSTEM_EVENT,
                        action="phone_call_failed",
                        details={
                            'call_id': call_id,
                            'phone_number': phone_number,
                            'participant_name': participant_name,
                            'call_type': call_type.value,
                            'scenario_type': scenario_type.value
                        },
                        security_level=SecurityLevel.MEDIUM
                    )
                
                self.logger.error(f"Call failed: {call_id} to {phone_number}")
            
            return call_id
            
        except Exception as e:
            self.logger.error(f"Error making call to {phone_number}: {e}")
            
            if self.audit_logger:
                self.audit_logger.audit(
                    event_type=AuditEventType.SYSTEM_EVENT,
                    action="phone_call_error",
                    details={
                        'phone_number': phone_number,
                        'participant_name': participant_name,
                        'error': str(e)
                    },
                    security_level=SecurityLevel.MEDIUM
                )
            
            raise
    
    async def end_call(self, call_id: str) -> bool:
        """
        End a phone call.
        
        Args:
            call_id: ID of the call to end
            
        Returns:
            True if call ended successfully, False otherwise
        """
        try:
            if call_id not in self.active_calls:
                self.logger.warning(f"Call not found: {call_id}")
                return False
            
            call = self.active_calls[call_id]
            
            # Update call state
            call.state = CallState.DISCONNECTED
            call.end_time = datetime.now(timezone.utc)
            
            # Update participant left time
            call.receiver.left_at = call.end_time
            
            # Calculate duration
            duration = call.get_duration()
            self.statistics['total_duration'] += duration
            
            # End call with provider
            success = await self.voip_provider.end_call(call_id)
            
            # Stop recording if enabled
            if call.recording_enabled:
                await self._stop_recording(call)
            
            # Remove from active calls
            del self.active_calls[call_id]
            
            # Log to audit
            if self.audit_logger:
                self.audit_logger.audit(
                    event_type=AuditEventType.SYSTEM_EVENT,
                    action="phone_call_ended",
                    details={
                        'call_id': call_id,
                        'duration': duration,
                        'recording_file': call.recording_file
                    },
                    security_level=SecurityLevel.MEDIUM
                )
            
            self.logger.info(f"Call ended: {call_id} ({duration:.2f}s)")
            return success
            
        except Exception as e:
            self.logger.error(f"Error ending call {call_id}: {e}")
            return False
    
    async def get_call_info(self, call_id: str) -> Optional[PhoneCall]:
        """
        Get information about a call.
        
        Args:
            call_id: ID of the call
            
        Returns:
            Call information or None if not found
        """
        return self.active_calls.get(call_id)
    
    def get_active_calls(self) -> List[PhoneCall]:
        """
        Get all active calls.
        
        Returns:
            List of active calls
        """
        return list(self.active_calls.values())
    
    async def send_audio(self, 
                         call_id: str,
                         audio_data: AudioSegment) -> bool:
        """
        Send audio to a call.
        
        Args:
            call_id: ID of the call
            audio_data: Audio data to send
            
        Returns:
            True if audio sent successfully, False otherwise
        """
        try:
            if call_id not in self.active_calls:
                self.logger.warning(f"Call not found: {call_id}")
                return False
            
            call = self.active_calls[call_id]
            
            if call.state != CallState.CONNECTED:
                self.logger.warning(f"Call not connected: {call_id}")
                return False
            
            # Send audio via provider
            success = await self.voip_provider.send_audio(call_id, audio_data)
            
            # Record if enabled
            if success and call.recording_enabled:
                await self._record_audio(call, audio_data, 'outbound')
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error sending audio to call {call_id}: {e}")
            return False
    
    async def receive_audio(self, call_id: str) -> Optional[AudioSegment]:
        """
        Receive audio from a call.
        
        Args:
            call_id: ID of the call
            
        Returns:
            Received audio segment or None
        """
        try:
            if call_id not in self.active_calls:
                self.logger.warning(f"Call not found: {call_id}")
                return None
            
            call = self.active_calls[call_id]
            
            if call.state != CallState.CONNECTED:
                self.logger.warning(f"Call not connected: {call_id}")
                return None
            
            # Receive audio via provider
            audio_data = await self.voip_provider.receive_audio(call_id)
            
            # Record if enabled
            if audio_data and call.recording_enabled:
                await self._record_audio(call, audio_data, 'inbound')
            
            return audio_data
            
        except Exception as e:
            self.logger.error(f"Error receiving audio from call {call_id}: {e}")
            return None
    
    async def _start_recording(self, call: PhoneCall) -> None:
        """Start recording a call."""
        try:
            # Generate recording filename
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            filename = f"call_{call.call_id}_{timestamp}.wav"
            filepath = os.path.join(self.recording_path, filename)
            
            # Store recording file path
            call.recording_file = filepath
            
            # Initialize recording
            call.metadata['recording_started'] = True
            call.metadata['recording_start_time'] = datetime.now(timezone.utc).isoformat()
            
            self.statistics['recorded_calls'] += 1
            self.logger.info(f"Started recording call {call.call_id}: {filepath}")
            
        except Exception as e:
            self.logger.error(f"Error starting recording for call {call.call_id}: {e}")
    
    async def _stop_recording(self, call: PhoneCall) -> None:
        """Stop recording a call."""
        try:
            if not call.recording_file:
                return
            
            # Update recording metadata
            call.metadata['recording_stopped'] = True
            call.metadata['recording_stop_time'] = datetime.now(timezone.utc).isoformat()
            
            self.logger.info(f"Stopped recording call {call.call_id}: {call.recording_file}")
            
        except Exception as e:
            self.logger.error(f"Error stopping recording for call {call.call_id}: {e}")
    
    async def _record_audio(self, 
                           call: PhoneCall,
                           audio_data: AudioSegment,
                           direction: str) -> None:
        """Record audio to call recording file."""
        try:
            if not call.recording_file:
                return
            
            # In a real implementation, this would append audio to the recording file
            # For now, we'll just log the recording
            self.logger.debug(f"Recorded {direction} audio for call {call.call_id}: {audio_data.duration:.2f}s")
            
        except Exception as e:
            self.logger.error(f"Error recording audio for call {call.call_id}: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get phone call statistics.
        
        Returns:
            Dictionary containing statistics
        """
        stats = self.statistics.copy()
        stats['active_calls'] = len(self.active_calls)
        
        # Calculate average call duration
        if stats['successful_calls'] > 0:
            stats['average_duration'] = stats['total_duration'] / stats['successful_calls']
        else:
            stats['average_duration'] = 0.0
        
        return stats
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        try:
            # End all active calls
            call_ids = list(self.active_calls.keys())
            for call_id in call_ids:
                await self.end_call(call_id)
            
            self.logger.info("Phone call manager cleanup complete")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")


# Global phone call manager instance
_global_phone_call_manager: Optional[PhoneCallManager] = None


def get_phone_call_manager() -> Optional[PhoneCallManager]:
    """
    Get the global phone call manager instance.
    
    Returns:
        Global PhoneCallManager instance or None if not initialized
    """
    return _global_phone_call_manager


def initialize_phone_call_manager(config: FrameworkConfig,
                               audit_logger: Optional[AuditLogger] = None) -> PhoneCallManager:
    """
    Initialize the global phone call manager.
    
    Args:
        config: Framework configuration
        audit_logger: Audit logger instance
        
    Returns:
        Initialized PhoneCallManager instance
    """
    global _global_phone_call_manager
    _global_phone_call_manager = PhoneCallManager(config, audit_logger)
    return _global_phone_call_manager


def shutdown_phone_call_manager() -> None:
    """Shutdown the global phone call manager."""
    global _global_phone_call_manager
    if _global_phone_call_manager:
        asyncio.create_task(_global_phone_call_manager.cleanup())
        _global_phone_call_manager = None