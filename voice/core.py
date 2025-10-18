
"""
ATS MAFIA Framework Voice Core System

This module provides the core voice processing engine and voice system architecture
for the ATS MAFIA framework. It handles real-time voice processing, TTS/STT integration,
and voice persona management.
"""

import os
import asyncio
import threading
import time
import uuid
import json
import logging
from typing import Dict, Any, Optional, List, Callable, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from abc import ABC, abstractmethod
import numpy as np
from datetime import datetime, timezone

from ..config.settings import FrameworkConfig
from ..core.logging import AuditLogger, AuditEventType, SecurityLevel


class VoiceState(Enum):
    """Voice system states."""
    IDLE = "idle"
    INITIALIZING = "initializing"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    LISTENING = "listening"
    ERROR = "error"
    SHUTDOWN = "shutdown"


class AudioFormat(Enum):
    """Supported audio formats."""
    WAV = "wav"
    MP3 = "mp3"
    FLAC = "flac"
    OGG = "ogg"
    PCM = "pcm"


class VoicePersona(Enum):
    """Predefined voice personas."""
    NEUTRAL = "neutral"
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    AUTHORITATIVE = "authoritative"
    CONCERNED = "concerned"
    URGENT = "urgent"
    CALM = "calm"
    EXCITED = "excited"
    SUSPICIOUS = "suspicious"
    HELPFUL = "helpful"


@dataclass
class VoicePersonaConfig:
    """Configuration for a voice persona."""
    name: str
    description: str
    pitch: float = 1.0  # 0.5 to 2.0
    rate: float = 1.0   # 0.5 to 2.0
    volume: float = 0.9  # 0.0 to 1.0
    tone: str = "neutral"  # neutral, warm, cold, etc.
    accent: str = "neutral"  # neutral, american, british, etc.
    emotion_modulation: float = 0.5  # 0.0 to 1.0
    breathing_style: str = "natural"  # natural, minimal, heavy
    speech_patterns: Dict[str, Any] = field(default_factory=dict)
    psychological_profile: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'description': self.description,
            'pitch': self.pitch,
            'rate': self.rate,
            'volume': self.volume,
            'tone': self.tone,
            'accent': self.accent,
            'emotion_modulation': self.emotion_modulation,
            'breathing_style': self.breathing_style,
            'speech_patterns': self.speech_patterns,
            'psychological_profile': self.psychological_profile
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VoicePersonaConfig':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class AudioSegment:
    """Audio segment data."""
    data: np.ndarray
    sample_rate: int
    channels: int
    format: AudioFormat
    duration: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'data': self.data.tolist(),
            'sample_rate': self.sample_rate,
            'channels': self.channels,
            'format': self.format.value,
            'duration': self.duration,
            'metadata': self.metadata
        }


@dataclass
class VoiceCommand:
    """Voice command for processing."""
    command_id: str
    command_type: str  # speak, listen, analyze, etc.
    parameters: Dict[str, Any]
    persona: Optional[VoicePersonaConfig] = None
    priority: int = 0  # 0 = normal, 1 = high, 2 = urgent
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    callback: Optional[Callable] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'command_id': self.command_id,
            'command_type': self.command_type,
            'parameters': self.parameters,
            'persona': self.persona.to_dict() if self.persona else None,
            'priority': self.priority,
            'timestamp': self.timestamp.isoformat(),
            'callback': str(self.callback) if self.callback else None
        }


class VoiceProcessor(ABC):
    """Abstract base class for voice processors."""
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the voice processor."""
        pass
    
    @abstractmethod
    async def process(self, audio_data: AudioSegment) -> AudioSegment:
        """Process audio data."""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup resources."""
        pass


class TTSEngine(ABC):
    """Abstract base class for Text-to-Speech engines."""
    
    @abstractmethod
    async def synthesize(self, 
                        text: str,
                        persona: VoicePersonaConfig,
                        format: AudioFormat = AudioFormat.WAV) -> AudioSegment:
        """Synthesize speech from text."""
        pass
    
    @abstractmethod
    async def get_available_voices(self) -> List[str]:
        """Get list of available voices."""
        pass


class STTEngine(ABC):
    """Abstract base class for Speech-to-Text engines."""
    
    @abstractmethod
    async def transcribe(self, 
                        audio_data: AudioSegment,
                        language: str = "en-US") -> Dict[str, Any]:
        """Transcribe speech to text."""
        pass
    
    @abstractmethod
    async def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        pass


class VoiceAnalysisEngine(ABC):
    """Abstract base class for voice analysis engines."""
    
    @abstractmethod
    async def analyze_emotion(self, audio_data: AudioSegment) -> Dict[str, Any]:
        """Analyze emotional content of voice."""
        pass
    
    @abstractmethod
    async def analyze_stress(self, audio_data: AudioSegment) -> Dict[str, Any]:
        """Analyze stress levels in voice."""
        pass
    
    @abstractmethod
    async def analyze_psychological_profile(self, 
                                          audio_data: AudioSegment,
                                          text_content: str) -> Dict[str, Any]:
        """Analyze psychological profile from voice and text."""
        pass


class VoiceEngine:
    """
    Core voice processing engine for the ATS MAFIA framework.
    
    Handles real-time voice processing, TTS/STT integration, and voice persona management.
    """
    
    def __init__(self, 
                 config: FrameworkConfig,
                 audit_logger: Optional[AuditLogger] = None):
        """
        Initialize the voice engine.
        
        Args:
            config: Framework configuration
            audit_logger: Audit logger instance
        """
        self.config = config
        self.audit_logger = audit_logger
        self.logger = logging.getLogger("voice_engine")
        
        # Engine state
        self.state = VoiceState.IDLE
        self._shutdown_event = threading.Event()
        self.initialized = False
        
        # Core components
        self.tts_engine: Optional[TTSEngine] = None
        self.stt_engine: Optional[STTEngine] = None
        self.analysis_engine: Optional[VoiceAnalysisEngine] = None
        
        # Voice processing pipeline
        self.processors: List[VoiceProcessor] = []
        
        # Voice personas
        self.personas: Dict[str, VoicePersonaConfig] = {}
        self.active_persona: Optional[VoicePersonaConfig] = None
        
        # Command queue and processing
        self.command_queue: List[VoiceCommand] = []
        self.processing_thread: Optional[threading.Thread] = None
        self.queue_lock = threading.RLock()
        
        # Performance monitoring
        self.metrics = {
            'commands_processed': 0,
            'average_processing_time': 0.0,
            'error_count': 0,
            'last_activity': None
        }
        
        # Load default personas
        self._load_default_personas()
        
        # Initialize components will be called separately
        self.initialized = False
    
    def _load_default_personas(self) -> None:
        """Load default voice personas."""
        default_personas = {
            VoicePersona.NEUTRAL.value: VoicePersonaConfig(
                name="Neutral",
                description="Balanced, neutral voice tone",
                pitch=1.0,
                rate=1.0,
                volume=0.9,
                tone="neutral",
                accent="neutral",
                emotion_modulation=0.3,
                psychological_profile={
                    'trust_level': 0.5,
                    'confidence_level': 0.5,
                    'authority_level': 0.5,
                    'friendliness_level': 0.5
                }
            ),
            VoicePersona.PROFESSIONAL.value: VoicePersonaConfig(
                name="Professional",
                description="Business professional voice",
                pitch=1.1,
                rate=0.9,
                volume=0.8,
                tone="confident",
                accent="neutral",
                emotion_modulation=0.2,
                psychological_profile={
                    'trust_level': 0.8,
                    'confidence_level': 0.9,
                    'authority_level': 0.7,
                    'friendliness_level': 0.4
                }
            ),
            VoicePersona.AUTHORITATIVE.value: VoicePersonaConfig(
                name="Authoritative",
                description="Commanding, authoritative voice",
                pitch=0.9,
                rate=0.8,
                volume=0.9,
                tone="commanding",
                accent="neutral",
                emotion_modulation=0.1,
                psychological_profile={
                    'trust_level': 0.6,
                    'confidence_level': 0.9,
                    'authority_level': 0.9,
                    'friendliness_level': 0.2
                }
            ),
            VoicePersona.CONCERNED.value: VoicePersonaConfig(
                name="Concerned",
                description="Concerned, empathetic voice",
                pitch=1.1,
                rate=0.9,
                volume=0.7,
                tone="empathetic",
                accent="neutral",
                emotion_modulation=0.7,
                psychological_profile={
                    'trust_level': 0.7,
                    'confidence_level': 0.4,
                    'authority_level': 0.3,
                    'friendliness_level': 0.8
                }
            ),
            VoicePersona.URGENT.value: VoicePersonaConfig(
                name="Urgent",
                description="Urgent, high-energy voice",
                pitch=1.2,
                rate=1.3,
                volume=0.9,
                tone="alert",
                accent="neutral",
                emotion_modulation=0.8,
                psychological_profile={
                    'trust_level': 0.5,
                    'confidence_level': 0.7,
                    'authority_level': 0.6,
                    'friendliness_level': 0.3
                }
            ),
            VoicePersona.SUSPICIOUS.value: VoicePersonaConfig(
                name="Suspicious",
                description="Suspicious, cautious voice",
                pitch=0.95,
                rate=0.85,
                volume=0.7,
                tone="cautious",
                accent="neutral",
                emotion_modulation=0.4,
                psychological_profile={
                    'trust_level': 0.2,
                    'confidence_level': 0.3,
                    'authority_level': 0.4,
                    'friendliness_level': 0.3
                }
            )
        }
        
        self.personas.update(default_personas)
        self.active_persona = default_personas[VoicePersona.NEUTRAL.value]
    
    async def initialize(self) -> bool:
        """Initialize the voice engine and all components."""
        try:
            self.state = VoiceState.INITIALIZING
            
            # Initialize TTS engine
            await self._initialize_tts_engine()
            
            # Initialize STT engine
            await self._initialize_stt_engine()
            
            # Initialize analysis engine
            await self._initialize_analysis_engine()
            
            # Start processing thread
            self.processing_thread = threading.Thread(
                target=self._processing_loop,
                daemon=True
            )
            self.processing_thread.start()
            
            self.state = VoiceState.IDLE
            self.initialized = True
            
            if self.audit_logger:
                self.audit_logger.audit(
                    event_type=AuditEventType.SYSTEM_EVENT,
                    action="voice_engine_initialized",
                    details={
                        'tts_engine': type(self.tts_engine).__name__ if self.tts_engine else None,
                        'stt_engine': type(self.stt_engine).__name__ if self.stt_engine else None,
                        'analysis_engine': type(self.analysis_engine).__name__ if self.analysis_engine else None
                    },
                    security_level=SecurityLevel.LOW
                )
            
            self.logger.info("Voice engine initialized successfully")
            return True
            
        except Exception as e:
            self.state = VoiceState.ERROR
            self.logger.error(f"Failed to initialize voice engine: {e}")
            
            if self.audit_logger:
                self.audit_logger.audit(
                    event_type=AuditEventType.SYSTEM_EVENT,
                    action="voice_engine_initialization_failed",
                    details={'error': str(e)},
                    security_level=SecurityLevel.MEDIUM
                )
            
            return False
    
    async def _initialize_tts_engine(self) -> None:
        """Initialize the Text-to-Speech engine."""
        # This will be implemented with actual TTS integration
        # For now, we'll use a mock implementation
        from .engines import PyTTSEngine
        self.tts_engine = PyTTSEngine(self.config)
        await self.tts_engine.initialize()
    
    async def _initialize_stt_engine(self) -> None:
        """Initialize the Speech-to-Text engine."""
        # This will be implemented with actual STT integration
        # For now, we'll use a mock implementation
        from .engines import SpeechRecognitionEngine
        self.stt_engine = SpeechRecognitionEngine(self.config)
        await self.stt_engine.initialize()
    
    async def _initialize_analysis_engine(self) -> None:
        """Initialize the voice analysis engine."""
        # This will be implemented with actual analysis integration
        from .engines import VoiceAnalysisEngineImpl
        self.analysis_engine = VoiceAnalysisEngineImpl(self.config)
        await self.analysis_engine.initialize()
    
    def _processing_loop(self) -> None:
        """Main processing loop for voice commands."""
        while not self._shutdown_event.is_set():
            try:
                command = self._get_next_command()
                if command:
                    asyncio.create_task(self._process_command(command))
                else:
                    time.sleep(0.1)  # Small delay to prevent busy waiting
            except Exception as e:
                self.logger.error(f"Error in processing loop: {e}")
                self.metrics['error_count'] += 1
    
    def _get_next_command(self) -> Optional[VoiceCommand]:
        """Get the next command from the queue."""
        with self.queue_lock:
            if not self.command_queue:
                return None
            
            # Sort by priority (higher priority first)
            self.command_queue.sort(key=lambda x: x.priority, reverse=True)
            return self.command_queue.pop(0)
    
    async def _process_command(self, command: VoiceCommand) -> None:
        """Process a voice command."""
        start_time = time.time()
        
        try:
            self.state = VoiceState.PROCESSING
            self.metrics['last_activity'] = datetime.now(timezone.utc)
            
            result = None
            
            if command.command_type == "speak":
                result = await self._handle_speak_command(command)
            elif command.command_type == "listen":
                result = await self._handle_listen_command(command)
            elif command.command_type == "analyze":
                result = await self._handle_analyze_command(command)
            elif command.command_type == "set_persona":
                result = await self._handle_set_persona_command(command)
            else:
                self.logger.warning(f"Unknown command type: {command.command_type}")
            
            # Update metrics
            processing_time = time.time() - start_time
            self.metrics['commands_processed'] += 1
            self.metrics['average_processing_time'] = (
                (self.metrics['average_processing_time'] * (self.metrics['commands_processed'] - 1) + processing_time) /
                self.metrics['commands_processed']
            )
            
            # Call callback if provided
            if command.callback:
                try:
                    if asyncio.iscoroutinefunction(command.callback):
                        await command.callback(result)
                    else:
                        command.callback(result)
                except Exception as e:
                    self.logger.error(f"Error in command callback: {e}")
            
            if self.audit_logger:
                self.audit_logger.audit(
                    event_type=AuditEventType.SYSTEM_EVENT,
                    action="voice_command_processed",
                    details={
                        'command_id': command.command_id,
                        'command_type': command.command_type,
                        'processing_time': processing_time,
                        'success': True
                    },
                    security_level=SecurityLevel.LOW
                )
            
        except Exception as e:
            self.metrics['error_count'] += 1
            self.logger.error(f"Error processing command {command.command_id}: {e}")
            
            if self.audit_logger:
                self.audit_logger.audit(
                    event_type=AuditEventType.SYSTEM_EVENT,
                    action="voice_command_failed",
                    details={
                        'command_id': command.command_id,
                        'command_type': command.command_type,
                        'error': str(e)
                    },
                    security_level=SecurityLevel.MEDIUM
                )
            
            if command.callback:
                try:
                    if asyncio.iscoroutinefunction(command.callback):
                        await command.callback({'error': str(e)})
                    else:
                        command.callback({'error': str(e)})
                except Exception as e:
                    self.logger.error(f"Error in command error callback: {e}")
        
        finally:
            self.state = VoiceState.IDLE
    
    async def _handle_speak_command(self, command: VoiceCommand) -> Dict[str, Any]:
        """Handle a speak command."""
        if not self.tts_engine:
            raise RuntimeError("TTS engine not initialized")
        
        text = command.parameters.get('text', '')
        persona = command.persona or self.active_persona
        
        if not text:
            raise ValueError("Text parameter is required for speak command")
        
        self.state = VoiceState.SPEAKING
        
        # Synthesize speech
        audio_segment = await self.tts_engine.synthesize(
            text=text,
            persona=persona,
            format=AudioFormat(command.parameters.get('format', 'wav'))
        )
        
        # Apply processors
        for processor in self.processors:
            audio_segment = await processor.process(audio_segment)
        
        return {
            'command_id': command.command_id,
            'audio_segment': audio_segment,
            'duration': audio_segment.duration,
            'persona_used': persona.name
        }
    
    async def _handle_listen_command(self, command: VoiceCommand) -> Dict[str, Any]:
        """Handle a listen command."""
        if not self.stt_engine:
            raise RuntimeError("STT engine not initialized")
        
        audio_data = command.parameters.get('audio_data')
        language = command.parameters.get('language', 'en-US')
        
        if not audio_data:
            raise ValueError("Audio data parameter is required for listen command")
        
        self.state = VoiceState.LISTENING
        
        # Convert to AudioSegment if needed
        if isinstance(audio_data, dict):
            audio_segment = AudioSegment(
                data=np.array(audio_data['data']),
                sample_rate=audio_data['sample_rate'],
                channels=audio_data['channels'],
                format=AudioFormat(audio_data['format']),
                duration=audio_data['duration'],
                metadata=audio_data.get('metadata', {})
            )
        else:
            audio_segment = audio_data
        
        # Transcribe speech
        transcription_result = await self.stt_engine.transcribe(
            audio_data=audio_segment,
            language=language
        )
        
        return {
            'command_id': command.command_id,
            'transcription': transcription_result.get('text', ''),
            'confidence': transcription_result.get('confidence', 0.0),
            'language': language,
            'alternatives': transcription_result.get('alternatives', [])
        }
    
    async def _handle_analyze_command(self, command: VoiceCommand) -> Dict[str, Any]:
        """Handle an analyze command."""
        if not self.analysis_engine:
            raise RuntimeError("Analysis engine not initialized")
        
        audio_data = command.parameters.get('audio_data')
        text_content = command.parameters.get('text_content', '')
        analysis_types = command.parameters.get('analysis_types', ['emotion', 'stress'])
        
        if not audio_data:
            raise ValueError("Audio data parameter is required for analyze command")
        
        # Convert to AudioSegment if needed
        if isinstance(audio_data, dict):
            audio_segment = AudioSegment(
                data=np.array(audio_data['data']),
                sample_rate=audio_data['sample_rate'],
                channels=audio_data['channels'],
                format=AudioFormat(audio_data['format']),
                duration=audio_data['duration'],
                metadata=audio_data.get('metadata', {})
            )
        else:
            audio_segment = audio_data
        
        results = {}
        # Perform requested analyses
        if 'emotion' in analysis_types:
            results['emotion'] = await self.analysis_engine.analyze_emotion(audio_segment)
        
        if 'stress' in analysis_types:
            results['stress'] = await self.analysis_engine.analyze_stress(audio_segment)
        
        if 'psychological' in analysis_types:
            results['psychological'] = await self.analysis_engine.analyze_psychological_profile(
                audio_segment, text_content
            )
        
        return {
            'command_id': command.command_id,
            'analysis_results': results,
            'analysis_types': analysis_types
        }
    
    async def _handle_set_persona_command(self, command: VoiceCommand) -> Dict[str, Any]:
        """Handle a set persona command."""
        persona_name = command.parameters.get('persona_name')
        
        if persona_name and persona_name in self.personas:
            self.active_persona = self.personas[persona_name]
            return {
                'command_id': command.command_id,
                'persona_set': persona_name,
                'persona_config': self.active_persona.to_dict()
            }
        else:
            raise ValueError(f"Persona '{persona_name}' not found")
    
    def add_command(self, 
                   command_type: str,
                   parameters: Dict[str, Any],
                   persona: Optional[VoicePersonaConfig] = None,
                   priority: int = 0,
                   callback: Optional[Callable] = None) -> str:
        """
        Add a command to the processing queue.
        
        Args:
            command_type: Type of command (speak, listen, analyze, etc.)
            parameters: Command parameters
            persona: Voice persona to use
            priority: Command priority (0=normal, 1=high, 2=urgent)
            callback: Callback function for results
            
        Returns:
            Command ID
        """
        command = VoiceCommand(
            command_id=str(uuid.uuid4()),
            command_type=command_type,
            parameters=parameters,
            persona=persona,
            priority=priority,
            callback=callback
        )
        
        with self.queue_lock:
            self.command_queue.append(command)
        
        self.logger.debug(f"Added command {command.command_id} of type {command_type}")
        return command.command_id
    
    def set_persona(self, persona_name: str) -> bool:
        """
        Set the active voice persona.
        
        Args:
            persona_name: Name of the persona to set
            
        Returns:
            True if persona was set, False if not found
        """
        if persona_name in self.personas:
            self.active_persona = self.personas[persona_name]
            
            if self.audit_logger:
                self.audit_logger.audit(
                    event_type=AuditEventType.SYSTEM_EVENT,
                    action="voice_persona_changed",
                    details={'persona_name': persona_name},
                    security_level=SecurityLevel.LOW
                )
            
            self.logger.info(f"Voice persona changed to: {persona_name}")
            return True
        else:
            self.logger.warning(f"Persona not found: {persona_name}")
            return False
    
    def add_persona(self, persona: VoicePersonaConfig) -> None:
        """
        Add a new voice persona.
        
        Args:
            persona: Persona configuration to add
        """
        self.personas[persona.name] = persona
        
        if self.audit_logger:
            self.audit_logger.audit(
                event_type=AuditEventType.SYSTEM_EVENT,
                action="voice_persona_added",
                details={'persona_name': persona.name},
                security_level=SecurityLevel.LOW
            )
        
        self.logger.info(f"Added voice persona: {persona.name}")
    
    def get_available_personas(self) -> List[str]:
        """
        Get list of available persona names.
        
        Returns:
            List of persona names
        """
        return list(self.personas.keys())
    
    def get_active_persona(self) -> Optional[VoicePersonaConfig]:
        """
        Get the currently active persona.
        
        Returns:
            Active persona configuration or None
        """
        return self.active_persona
    
    def add_processor(self, processor: VoiceProcessor) -> None:
        """
        Add a voice processor to the pipeline.
        
        Args:
            processor: Voice processor to add
        """
        self.processors.append(processor)
        self.logger.info(f"Added voice processor: {type(processor).__name__}")
    
    def remove_processor(self, processor: VoiceProcessor) -> bool:
        """
        Remove a voice processor from the pipeline.
        
        Args:
            processor: Voice processor to remove
            
        Returns:
            True if processor was removed, False if not found
        """
        if processor in self.processors:
            self.processors.remove(processor)
            self.logger.info(f"Removed voice processor: {type(processor).__name__}")
            return True
        return False
    
    def get_state(self) -> VoiceState:
        """
        Get the current voice engine state.
        
        Returns:
            Current voice state
        """
        return self.state
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get voice engine metrics.
        
        Returns:
            Dictionary containing metrics
        """
        return {
            **self.metrics,
            'state': self.state.value,
            'queue_size': len(self.command_queue),
            'active_persona': self.active_persona.name if self.active_persona else None,
            'available_personas': len(self.personas),
            'processors_count': len(self.processors)
        }
    
    async def shutdown(self) -> None:
        """Shutdown the voice engine and clean up resources."""
        try:
            self.state = VoiceState.SHUTDOWN
            
            # Signal shutdown
            self._shutdown_event.set()
            
            # Wait for processing thread to finish
            if self.processing_thread and self.processing_thread.is_alive():
                self.processing_thread.join(timeout=5.0)
            
            # Cleanup processors
            for processor in self.processors:
                try:
                    await processor.cleanup()
                except Exception as e:
                    self.logger.error(f"Error cleaning up processor {type(processor).__name__}: {e}")
            
            # Cleanup engines
            if self.tts_engine:
                try:
                    await self.tts_engine.cleanup()
                except Exception as e:
                    self.logger.error(f"Error cleaning up TTS engine: {e}")
            
            if self.stt_engine:
                try:
                    await self.stt_engine.cleanup()
                except Exception as e:
                    self.logger.error(f"Error cleaning up STT engine: {e}")
            
            if self.analysis_engine:
                try:
                    await self.analysis_engine.cleanup()
                except Exception as e:
                    self.logger.error(f"Error cleaning up analysis engine: {e}")
            
            if self.audit_logger:
                self.audit_logger.audit(
                    event_type=AuditEventType.SYSTEM_EVENT,
                    action="voice_engine_shutdown",
                    details={'metrics': self.get_metrics()},
                    security_level=SecurityLevel.LOW
                )
            
            self.logger.info("Voice engine shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during voice engine shutdown: {e}")


# Global voice engine instance
_global_voice_engine: Optional[VoiceEngine] = None


def get_voice_engine() -> Optional[VoiceEngine]:
    """
    Get the global voice engine instance.
    
    Returns:
        Global VoiceEngine instance or None if not initialized
    """
    return _global_voice_engine


def initialize_voice_engine(config: FrameworkConfig,
                           audit_logger: Optional[AuditLogger] = None) -> VoiceEngine:
    """
    Initialize the global voice engine.
    
    Args:
        config: Framework configuration
        audit_logger: Audit logger instance
        
    Returns:
        Initialized VoiceEngine instance
    """
    global _global_voice_engine
    _global_voice_engine = VoiceEngine(config, audit_logger)
    return _global_voice_engine


def shutdown_voice_engine() -> None:
    """Shutdown the global voice engine."""
    global _global_voice_engine
    if _global_voice_engine:
        asyncio.create_task(_global_voice_engine.shutdown())
        _global_voice_engine = None
        
