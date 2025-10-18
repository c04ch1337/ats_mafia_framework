"""
ATS MAFIA Framework Voice System Integration

This module provides integration between all voice system components and the core framework.
Includes voice system manager, initialization, and coordination.
"""

import os
import asyncio
import logging
import time
import uuid
import json
from typing import Dict, Any, Optional, List, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone

from .core import VoiceEngine, VoicePersonaConfig, AudioSegment, AudioFormat
from .engines import VoiceSynthesizer, SpeechRecognizer, VoiceAnalysisEngineImpl
from .analysis import VoiceAnalysisManager
from .conversation import ConversationManager, DialogueStrategy, ScenarioType, ConversationObjective
from .phone import PhoneCallManager
from .synthesis import VoiceSynthesizer as TextToSpeechSynthesizer
from .recognition import SpeechRecognizer as SpeechRecognitionEngine
from .adaptation import AdaptationEngine, AdaptationEvent, AdaptationTrigger
from .ethics import EthicsSafeguards, InteractionType, ScopeType
from ..config.settings import FrameworkConfig
from ..core.logging import AuditLogger, AuditEventType, SecurityLevel


class VoiceSystemState(Enum):
    """States of the voice system."""
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    ACTIVE = "active"
    ERROR = "error"
    SHUTDOWN = "shutdown"


@dataclass
class VoiceSystemConfig:
    """Configuration for the voice system."""
    enabled: bool = True
    auto_initialize: bool = True
    low_latency_mode: bool = True
    max_latency_ms: int = 300
    enable_adaptation: bool = True
    enable_analysis: bool = True
    enable_ethics: bool = True
    enable_conversation_management: bool = True
    enable_phone_integration: bool = True
    default_persona: str = "neutral"
    recording_enabled: bool = True
    audit_logging: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'enabled': self.enabled,
            'auto_initialize': self.auto_initialize,
            'low_latency_mode': self.low_latency_mode,
            'max_latency_ms': self.max_latency_ms,
            'enable_adaptation': self.enable_adaptation,
            'enable_analysis': self.enable_analysis,
            'enable_ethics': self.enable_ethics,
            'enable_conversation_management': self.enable_conversation_management,
            'enable_phone_integration': self.enable_phone_integration,
            'default_persona': self.default_persona,
            'recording_enabled': self.recording_enabled,
            'audit_logging': self.audit_logging
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VoiceSystemConfig':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class VoiceSystemMetrics:
    """Metrics for the voice system."""
    total_interactions: int = 0
    successful_interactions: int = 0
    failed_interactions: int = 0
    average_latency_ms: float = 0.0
    total_synthesis_time: float = 0.0
    total_recognition_time: float = 0.0
    total_analysis_time: float = 0.0
    active_conversations: int = 0
    active_calls: int = 0
    adaptations_applied: int = 0
    ethics_violations: int = 0
    system_uptime: float = 0.0
    last_activity: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'total_interactions': self.total_interactions,
            'successful_interactions': self.successful_interactions,
            'failed_interactions': self.failed_interactions,
            'success_rate': self.successful_interactions / max(self.total_interactions, 1),
            'average_latency_ms': self.average_latency_ms,
            'total_synthesis_time': self.total_synthesis_time,
            'total_recognition_time': self.total_recognition_time,
            'total_analysis_time': self.total_analysis_time,
            'active_conversations': self.active_conversations,
            'active_calls': self.active_calls,
            'adaptations_applied': self.adaptations_applied,
            'ethics_violations': self.ethics_violations,
            'system_uptime': self.system_uptime,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None
        }


class VoiceSystemManager:
    """
    Manager for the entire voice system in the ATS MAFIA framework.
    
    Coordinates all voice components and provides high-level interface.
    """
    
    def __init__(self, 
                 config: FrameworkConfig,
                 audit_logger: Optional[AuditLogger] = None):
        """
        Initialize the voice system manager.
        
        Args:
            config: Framework configuration
            audit_logger: Audit logger instance
        """
        self.config = config
        self.audit_logger = audit_logger
        self.logger = logging.getLogger("voice_system_manager")
        
        # System state
        self.state = VoiceSystemState.UNINITIALIZED
        self.start_time = datetime.now(timezone.utc)
        self.shutdown_event = asyncio.Event()
        
        # Voice system configuration
        self.voice_config = VoiceSystemConfig(
            enabled=config.get('voice.enabled', True),
            auto_initialize=config.get('voice.auto_initialize', True),
            low_latency_mode=config.get('voice.low_latency_mode', True),
            max_latency_ms=config.get('voice.max_latency_ms', 300),
            enable_adaptation=config.get('voice.adaptation.enabled', True),
            enable_analysis=config.get('voice.analysis.enabled', True),
            enable_ethics=config.get('voice.ethics.enabled', True),
            enable_conversation_management=config.get('voice.conversation.enabled', True),
            enable_phone_integration=config.get('voice.phone.enabled', False),
            default_persona=config.get('voice.default_persona', 'neutral'),
            recording_enabled=config.get('voice.recording.enabled', True),
            audit_logging=config.get('voice.audit_logging', True)
        )
        
        # Core components
        self.voice_engine: Optional[VoiceEngine] = None
        self.voice_synthesizer: Optional[TextToSpeechSynthesizer] = None
        self.speech_recognizer: Optional[SpeechRecognitionEngine] = None
        self.voice_analysis_manager: Optional[VoiceAnalysisManager] = None
        self.conversation_manager: Optional[ConversationManager] = None
        self.phone_call_manager: Optional[PhoneCallManager] = None
        self.adaptation_engine: Optional[AdaptationEngine] = None
        self.ethics_safeguards: Optional[EthicsSafeguards] = None
        
        # Metrics
        self.metrics = VoiceSystemMetrics()
        
        # Performance monitoring
        self.performance_monitor = VoicePerformanceMonitor(self.voice_config)
        
        # Auto-initialize if enabled
        if self.voice_config.auto_initialize:
            asyncio.create_task(self.initialize())
    
    async def initialize(self) -> bool:
        """
        Initialize the voice system and all components.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            if self.state != VoiceSystemState.UNINITIALIZED:
                self.logger.warning(f"Voice system already initialized or in state: {self.state.value}")
                return False
            
            self.state = VoiceSystemState.INITIALIZING
            
            # Initialize core voice engine
            self.voice_engine = VoiceEngine(self.config, self.audit_logger)
            await self.voice_engine.initialize()
            
            # Initialize voice synthesizer
            if self.voice_config.enabled:
                self.voice_synthesizer = TextToSpeechSynthesizer(self.config)
                await self.voice_synthesizer.initialize()
            
            # Initialize speech recognizer
            if self.voice_config.enabled:
                self.speech_recognizer = SpeechRecognitionEngine(self.config)
                await self.speech_recognizer.initialize()
            
            # Initialize voice analysis manager
            if self.voice_config.enable_analysis:
                self.voice_analysis_manager = VoiceAnalysisManager(self.config, self.audit_logger)
            
            # Initialize conversation manager
            if self.voice_config.enable_conversation_management:
                self.conversation_manager = ConversationManager(self.config, self.audit_logger)
            
            # Initialize phone call manager
            if self.voice_config.enable_phone_integration:
                self.phone_call_manager = PhoneCallManager(self.config, self.audit_logger)
                await self.phone_call_manager.initialize()
            
            # Initialize adaptation engine
            if self.voice_config.enable_adaptation:
                self.adaptation_engine = AdaptationEngine(self.config, self.audit_logger)
            
            # Initialize ethics safeguards
            if self.voice_config.enable_ethics:
                self.ethics_safeguards = EthicsSafeguards(self.config, self.audit_logger)
            
            self.state = VoiceSystemState.READY
            
            # Log to audit
            if self.audit_logger:
                self.audit_logger.audit(
                    event_type=AuditEventType.SYSTEM_EVENT,
                    action="voice_system_initialized",
                    details={
                        'components_enabled': {
                            'voice_synthesizer': self.voice_synthesizer is not None,
                            'speech_recognizer': self.speech_recognizer is not None,
                            'voice_analysis': self.voice_analysis_manager is not None,
                            'conversation_management': self.conversation_manager is not None,
                            'phone_integration': self.phone_call_manager is not None,
                            'adaptation_engine': self.adaptation_engine is not None,
                            'ethics_safeguards': self.ethics_safeguards is not None
                        },
                        'configuration': self.voice_config.to_dict()
                    },
                    security_level=SecurityLevel.MEDIUM
                )
            
            self.logger.info("Voice system initialized successfully")
            return True
            
        except Exception as e:
            self.state = VoiceSystemState.ERROR
            self.logger.error(f"Failed to initialize voice system: {e}")
            
            if self.audit_logger:
                self.audit_logger.audit(
                    event_type=AuditEventType.SYSTEM_EVENT,
                    action="voice_system_initialization_failed",
                    details={'error': str(e)},
                    security_level=SecurityLevel.HIGH
                )
            
            return False
    
    async def synthesize_speech(self,
                               text: str,
                               persona: Optional[str] = None,
                               format: Optional[AudioFormat] = None) -> Optional[AudioSegment]:
        """
        Synthesize speech from text.
        
        Args:
            text: Text to synthesize
            persona: Voice persona to use
            format: Output audio format
            
        Returns:
            Audio segment with synthesized speech
        """
        try:
            if not self.voice_synthesizer:
                self.logger.warning("Voice synthesizer not initialized")
                return None
            
            start_time = time.time()
            
            # Get persona configuration
            persona_name = persona or self.voice_config.default_persona
            persona_config = self.voice_engine.get_active_persona()
            if not persona_config or persona_config.name != persona_name:
                # Set persona if different
                self.voice_engine.set_persona(persona_name)
                persona_config = self.voice_engine.get_active_persona()
            
            # Synthesize speech
            audio_segment = await self.voice_synthesizer.synthesize(
                text=text,
                persona=persona_config,
                format=format or AudioFormat.WAV
            )
            
            # Update metrics
            processing_time = (time.time() - start_time) * 1000  # Convert to ms
            self.metrics.total_synthesis_time += processing_time
            self.metrics.total_interactions += 1
            self.metrics.successful_interactions += 1
            self.metrics.last_activity = datetime.now(timezone.utc)
            
            # Check latency
            if self.voice_config.low_latency_mode and processing_time > self.voice_config.max_latency_ms:
                self.logger.warning(f"High synthesis latency: {processing_time:.2f}ms")
            
            return audio_segment
            
        except Exception as e:
            self.metrics.total_interactions += 1
            self.metrics.failed_interactions += 1
            self.logger.error(f"Error synthesizing speech: {e}")
            return None
    
    async def recognize_speech(self,
                              audio: AudioSegment,
                              language: str = "en-US") -> Optional[str]:
        """
        Recognize speech from audio.
        
        Args:
            audio: Audio segment to recognize
            language: Language code
            
        Returns:
            Recognized text or None if error
        """
        try:
            if not self.speech_recognizer:
                self.logger.warning("Speech recognizer not initialized")
                return None
            
            start_time = time.time()
            
            # Recognize speech
            result = await self.speech_recognizer.recognize(audio, language)
            
            if result:
                # Update metrics
                processing_time = (time.time() - start_time) * 1000  # Convert to ms
                self.metrics.total_recognition_time += processing_time
                self.metrics.total_interactions += 1
                self.metrics.successful_interactions += 1
                self.metrics.last_activity = datetime.now(timezone.utc)
                
                # Check latency
                if self.voice_config.low_latency_mode and processing_time > self.voice_config.max_latency_ms:
                    self.logger.warning(f"High recognition latency: {processing_time:.2f}ms")
                
                return result.text
            
            return None
            
        except Exception as e:
            self.metrics.total_interactions += 1
            self.metrics.failed_interactions += 1
            self.logger.error(f"Error recognizing speech: {e}")
            return None
    
    async def analyze_voice(self,
                           audio: AudioSegment,
                           text: Optional[str] = None,
                           analysis_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Analyze voice for emotion, stress, and psychological profile.
        
        Args:
            audio: Audio segment to analyze
            text: Text content of speech
            analysis_types: Types of analysis to perform
            
        Returns:
            Analysis results
        """
        try:
            if not self.voice_analysis_manager:
                self.logger.warning("Voice analysis manager not initialized")
                return {}
            
            start_time = time.time()
            
            analysis_types = analysis_types or ['emotion', 'stress', 'psychological']
            results = {}
            
            # Perform emotion analysis
            if 'emotion' in analysis_types:
                emotion_result = await self.voice_analysis_manager.analyze_emotion(audio)
                results['emotion'] = emotion_result.to_dict()
            
            # Perform stress analysis
            if 'stress' in analysis_types:
                stress_result = await self.voice_analysis_manager.analyze_stress(audio)
                results['stress'] = stress_result.to_dict()
            
            # Perform psychological analysis
            if 'psychological' in analysis_types and text:
                profile_result = await self.voice_analysis_manager.analyze_psychological_profile(audio, text)
                results['psychological'] = profile_result.to_dict()
            
            # Perform deception analysis
            if 'deception' in analysis_types and text:
                deception_result = await self.voice_analysis_manager.analyze_deception(audio, text)
                results['deception'] = deception_result.to_dict()
            
            # Update metrics
            processing_time = (time.time() - start_time) * 1000  # Convert to ms
            self.metrics.total_analysis_time += processing_time
            self.metrics.last_activity = datetime.now(timezone.utc)
            
            # Trigger adaptation if enabled
            if self.adaptation_engine and text:
                await self._trigger_adaptation(results, text)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error analyzing voice: {e}")
            return {}
    
    async def start_conversation(self,
                               participant_id: str,
                               participant_info: Dict[str, Any],
                               scenario_type: ScenarioType,
                               strategy: DialogueStrategy,
                               objectives: List[ConversationObjective]) -> Optional[str]:
        """
        Start a new conversation.
        
        Args:
            participant_id: ID of the participant
            participant_info: Information about the participant
            scenario_type: Type of scenario
            strategy: Dialogue strategy to use
            objectives: List of conversation objectives
            
        Returns:
            Conversation ID or None if error
        """
        try:
            if not self.conversation_manager:
                self.logger.warning("Conversation manager not initialized")
                return None
            
            # Start ethics monitoring if enabled
            session_id = None
            if self.ethics_safeguards:
                session_id = str(uuid.uuid4())
                await self.ethics_safeguards.start_monitoring(
                    session_id=session_id,
                    interaction_id=str(uuid.uuid4()),
                    interaction_type=InteractionType.TRAINING,
                    scope_id=ScopeType.CONTROLLED.value,
                    scope_type=ScopeType.CONTROLLED,
                    participant_id=participant_id,
                    metadata={'scenario_type': scenario_type.value}
                )
            
            # Start conversation
            conversation_id = await self.conversation_manager.start_conversation(
                participant_id=participant_id,
                participant_info=participant_info,
                scenario_type=scenario_type,
                strategy=strategy,
                objectives=objectives
            )
            
            if conversation_id and session_id:
                # Store mapping for later reference
                if not hasattr(self, '_conversation_session_map'):
                    self._conversation_session_map = {}
                self._conversation_session_map[conversation_id] = session_id
            
            # Update metrics
            self.metrics.active_conversations += 1
            self.metrics.last_activity = datetime.now(timezone.utc)
            
            return conversation_id
            
        except Exception as e:
            self.logger.error(f"Error starting conversation: {e}")
            return None
    
    async def end_conversation(self, conversation_id: str) -> bool:
        """
        End a conversation.
        
        Args:
            conversation_id: ID of the conversation to end
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.conversation_manager:
                return False
            
            # End conversation
            success = await self.conversation_manager.end_conversation(conversation_id)
            
            # End ethics monitoring
            if self.ethics_safeguards and hasattr(self, '_conversation_session_map'):
                session_id = self._conversation_session_map.get(conversation_id)
                if session_id:
                    await self.ethics_safeguards.end_monitoring(session_id)
                    del self._conversation_session_map[conversation_id]
            
            # Update metrics
            if success:
                self.metrics.active_conversations = max(0, self.metrics.active_conversations - 1)
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error ending conversation: {e}")
            return False
    
    async def _trigger_adaptation(self, analysis_results: Dict[str, Any], text: str) -> None:
        """Trigger voice adaptation based on analysis results."""
        try:
            if not self.adaptation_engine:
                return
            
            # Check for emotion-based adaptation
            if 'emotion' in analysis_results:
                emotion_data = analysis_results['emotion']
                event = AdaptationEvent(
                    event_id=str(uuid.uuid4()),
                    trigger=AdaptationTrigger.EMOTION_CHANGE,
                    data={
                        'emotion': emotion_data.get('emotion_type'),
                        'intensity': emotion_data.get('intensity'),
                        'persona': self.voice_engine.get_active_persona()
                    }
                )
                await self.adaptation_engine.process_event(event)
            
            # Check for stress-based adaptation
            if 'stress' in analysis_results:
                stress_data = analysis_results['stress']
                event = AdaptationEvent(
                    event_id=str(uuid.uuid4()),
                    trigger=AdaptationTrigger.STRESS_LEVEL,
                    data={
                        'stress_level': stress_data.get('stress_value'),
                        'persona': self.voice_engine.get_active_persona()
                    }
                )
                await self.adaptation_engine.process_event(event)
            
            # Update metrics
            if self.adaptation_engine:
                stats = self.adaptation_engine.get_statistics()
                self.metrics.adaptations_applied = stats.get('total_adaptations', 0)
            
        except Exception as e:
            self.logger.error(f"Error triggering adaptation: {e}")
    
    def get_state(self) -> VoiceSystemState:
        """Get the current voice system state."""
        return self.state
    
    def get_metrics(self) -> VoiceSystemMetrics:
        """Get voice system metrics."""
        # Update system uptime
        if self.start_time:
            self.metrics.system_uptime = (datetime.now(timezone.utc) - self.start_time).total_seconds()
        
        # Calculate average latency
        total_time = self.metrics.total_synthesis_time + self.metrics.total_recognition_time + self.metrics.total_analysis_time
        total_operations = self.metrics.total_interactions
        if total_operations > 0:
            self.metrics.average_latency_ms = total_time / total_operations
        
        # Update active counts
        if self.conversation_manager:
            conv_stats = self.conversation_manager.get_statistics()
            self.metrics.active_conversations = conv_stats.get('active_conversations', 0)
        
        if self.phone_call_manager:
            phone_stats = self.phone_call_manager.get_statistics()
            self.metrics.active_calls = phone_stats.get('active_calls', 0)
        
        # Update ethics violations
        if self.ethics_safeguards:
            ethics_stats = self.ethics_safeguards.get_statistics()
            self.metrics.ethics_violations = ethics_stats.get('compliance_violations', 0)
        
        return self.metrics
    
    async def shutdown(self) -> None:
        """Shutdown the voice system and all components."""
        try:
            self.state = VoiceSystemState.SHUTDOWN
            self.shutdown_event.set()
            
            # Shutdown components
            if self.voice_engine:
                await self.voice_engine.shutdown()
            
            if self.voice_synthesizer:
                await self.voice_synthesizer.cleanup()
            
            if self.speech_recognizer:
                await self.speech_recognizer.cleanup()
            
            if self.voice_analysis_manager:
                await self.voice_analysis_manager.cleanup()
            
            if self.conversation_manager:
                await self.conversation_manager.cleanup()
            
            if self.phone_call_manager:
                await self.phone_call_manager.cleanup()
            
            if self.adaptation_engine:
                await self.adaptation_engine.cleanup()
            
            if self.ethics_safeguards:
                await self.ethics_safeguards.cleanup()
            
            # Log to audit
            if self.audit_logger:
                self.audit_logger.audit(
                    event_type=AuditEventType.SYSTEM_EVENT,
                    action="voice_system_shutdown",
                    details={
                        'final_metrics': self.get_metrics().to_dict(),
                        'uptime': self.metrics.system_uptime
                    },
                    security_level=SecurityLevel.MEDIUM
                )
            
            self.logger.info("Voice system shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during voice system shutdown: {e}")


class VoicePerformanceMonitor:
    """Monitor voice system performance."""
    
    def __init__(self, config: VoiceSystemConfig):
        """
        Initialize the performance monitor.
        
        Args:
            config: Voice system configuration
        """
        self.config = config
        self.logger = logging.getLogger("voice_performance_monitor")
        
        # Performance metrics
        self.latency_history: List[float] = []
        self.error_count = 0
        self.warning_count = 0
    
    def record_latency(self, latency_ms: float) -> None:
        """Record latency measurement."""
        self.latency_history.append(latency_ms)
        
        # Keep only last 100 measurements
        if len(self.latency_history) > 100:
            self.latency_history.pop(0)
        
        # Check for performance warnings
        if self.config.low_latency_mode and latency_ms > self.config.max_latency_ms:
            self.warning_count += 1
            self.logger.warning(f"High latency detected: {latency_ms:.2f}ms")
    
    def get_average_latency(self) -> float:
        """Get average latency."""
        if not self.latency_history:
            return 0.0
        return sum(self.latency_history) / len(self.latency_history)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        return {
            'average_latency_ms': self.get_average_latency(),
            'max_latency_ms': max(self.latency_history) if self.latency_history else 0.0,
            'min_latency_ms': min(self.latency_history) if self.latency_history else 0.0,
            'error_count': self.error_count,
            'warning_count': self.warning_count,
            'total_measurements': len(self.latency_history)
        }


# Global voice system manager instance
_global_voice_system_manager: Optional[VoiceSystemManager] = None


def get_voice_system_manager() -> Optional[VoiceSystemManager]:
    """
    Get the global voice system manager instance.
    
    Returns:
        Global VoiceSystemManager instance or None if not initialized
    """
    return _global_voice_system_manager


def initialize_voice_system_manager(config: FrameworkConfig,
                                   audit_logger: Optional[AuditLogger] = None) -> VoiceSystemManager:
    """
    Initialize the global voice system manager.
    
    Args:
        config: Framework configuration
        audit_logger: Audit logger instance
        
    Returns:
        Initialized VoiceSystemManager instance
    """
    global _global_voice_system_manager
    _global_voice_system_manager = VoiceSystemManager(config, audit_logger)
    return _global_voice_system_manager


def shutdown_voice_system_manager() -> None:
    """Shutdown the global voice system manager."""
    global _global_voice_system_manager
    if _global_voice_system_manager:
        asyncio.create_task(_global_voice_system_manager.shutdown())
        _global_voice_system_manager = None