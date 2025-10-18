"""
ATS MAFIA Framework Speech Recognition

This module provides speech recognition capabilities for the ATS MAFIA framework.
Includes real-time speech recognition, language detection, and confidence scoring.
"""

import os
import asyncio
import logging
import time
import json
from typing import Dict, Any, Optional, List, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone
import numpy as np

from .core import AudioSegment, AudioFormat
from ..config.settings import FrameworkConfig
from ..core.logging import AuditLogger, AuditEventType, SecurityLevel


class RecognitionEngine(Enum):
    """Types of recognition engines."""
    SPEECH_RECOGNITION = "speech_recognition"
    GOOGLE = "google"
    AZURE = "azure"
    AWS = "aws"
    WHISPER = "whisper"
    CUSTOM = "custom"


class RecognitionState(Enum):
    """States of speech recognition."""
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    COMPLETE = "complete"
    ERROR = "error"


@dataclass
class RecognitionResult:
    """Result of speech recognition."""
    text: str
    confidence: float  # 0.0 to 1.0
    alternatives: List[Dict[str, Any]]
    language: str
    duration: float
    processing_time: float
    engine: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'text': self.text,
            'confidence': self.confidence,
            'alternatives': self.alternatives,
            'language': self.language,
            'duration': self.duration,
            'processing_time': self.processing_time,
            'engine': self.engine,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RecognitionResult':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class RecognitionConfig:
    """Configuration for speech recognition."""
    engine: RecognitionEngine
    language: str = "en-US"
    enable_alternatives: bool = True
    max_alternatives: int = 3
    enable_profanity_filter: bool = True
    enable_automatic_punctuation: bool = True
    confidence_threshold: float = 0.5
    max_duration: float = 30.0
    silence_threshold: float = 0.5
    boost_words: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'engine': self.engine.value,
            'language': self.language,
            'enable_alternatives': self.enable_alternatives,
            'max_alternatives': self.max_alternatives,
            'enable_profanity_filter': self.enable_profanity_filter,
            'enable_automatic_punctuation': self.enable_automatic_punctuation,
            'confidence_threshold': self.confidence_threshold,
            'max_duration': self.max_duration,
            'silence_threshold': self.silence_threshold,
            'boost_words': self.boost_words
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RecognitionConfig':
        """Create from dictionary."""
        return cls(
            engine=RecognitionEngine(data['engine']),
            language=data.get('language', 'en-US'),
            enable_alternatives=data.get('enable_alternatives', True),
            max_alternatives=data.get('max_alternatives', 3),
            enable_profanity_filter=data.get('enable_profanity_filter', True),
            enable_automatic_punctuation=data.get('enable_automatic_punctuation', True),
            confidence_threshold=data.get('confidence_threshold', 0.5),
            max_duration=data.get('max_duration', 30.0),
            silence_threshold=data.get('silence_threshold', 0.5),
            boost_words=data.get('boost_words', [])
        )


class SpeechRecognizer:
    """Speech recognizer for converting audio to text."""
    
    def __init__(self, config: FrameworkConfig):
        """
        Initialize the speech recognizer.
        
        Args:
            config: Framework configuration
        """
        self.config = config
        self.logger = logging.getLogger("speech_recognizer")
        
        # Recognition configuration
        self.recognition_config = RecognitionConfig(
            engine=RecognitionEngine(config.get('voice.recognition.engine', 'speech_recognition')),
            language=config.get('voice.recognition.language', 'en-US'),
            enable_alternatives=config.get('voice.recognition.enable_alternatives', True),
            max_alternatives=config.get('voice.recognition.max_alternatives', 3),
            enable_profanity_filter=config.get('voice.recognition.enable_profanity_filter', True),
            enable_automatic_punctuation=config.get('voice.recognition.enable_automatic_punctuation', True),
            confidence_threshold=config.get('voice.recognition.confidence_threshold', 0.5),
            max_duration=config.get('voice.recognition.max_duration', 30.0),
            silence_threshold=config.get('voice.recognition.silence_threshold', 0.5),
            boost_words=config.get('voice.recognition.boost_words', [])
        )
        
        # Recognition state
        self.state = RecognitionState.IDLE
        self.current_recognition: Optional[RecognitionResult] = None
        
        # Recognition engines
        self.engines: Dict[RecognitionEngine, Any] = {}
        
        # Statistics
        self.stats = {
            'total_recognitions': 0,
            'successful_recognitions': 0,
            'failed_recognitions': 0,
            'average_confidence': 0.0,
            'average_processing_time': 0.0,
            'total_duration': 0.0
        }
        
        # Initialize engines
        asyncio.create_task(self._initialize_engines())
    
    async def _initialize_engines(self) -> None:
        """Initialize recognition engines."""
        try:
            # Initialize SpeechRecognition engine
            await self._initialize_speech_recognition_engine()
            
            # Initialize other engines as needed
            # await self._initialize_google_engine()
            # await self._initialize_azure_engine()
            
            self.logger.info("Speech recognition engines initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing recognition engines: {e}")
    
    async def _initialize_speech_recognition_engine(self) -> None:
        """Initialize SpeechRecognition engine."""
        try:
            import speech_recognition as sr
            
            recognizer = sr.Recognizer()
            self.engines[RecognitionEngine.SPEECH_RECOGNITION] = recognizer
            
            # Configure recognizer
            recognizer.energy_threshold = 300
            recognizer.dynamic_energy_threshold = True
            recognizer.pause_threshold = self.recognition_config.silence_threshold
            
            self.logger.info("SpeechRecognition engine initialized")
            
        except ImportError:
            self.logger.warning("SpeechRecognition library not available")
        except Exception as e:
            self.logger.error(f"Error initializing SpeechRecognition engine: {e}")
    
    async def recognize(self,
                       audio: AudioSegment,
                       language: Optional[str] = None,
                       config: Optional[RecognitionConfig] = None) -> Optional[RecognitionResult]:
        """
        Recognize speech from audio.
        
        Args:
            audio: Audio segment to recognize
            language: Language code (overrides config)
            config: Recognition configuration (overrides default)
            
        Returns:
            Recognition result or None if error
        """
        try:
            if not audio:
                return None
            
            start_time = time.time()
            self.state = RecognitionState.PROCESSING
            
            # Use provided config or default
            recognition_config = config or self.recognition_config
            recognition_language = language or recognition_config.language
            
            # Select engine
            engine = recognition_config.engine
            if engine not in self.engines:
                self.logger.warning(f"Recognition engine {engine.value} not available, falling back to speech_recognition")
                engine = RecognitionEngine.SPEECH_RECOGNITION
            
            # Perform recognition
            if engine == RecognitionEngine.SPEECH_RECOGNITION:
                result = await self._recognize_with_speech_recognition(audio, recognition_config, recognition_language)
            else:
                # Fallback to speech_recognition
                result = await self._recognize_with_speech_recognition(audio, recognition_config, recognition_language)
            
            # Update statistics
            processing_time = time.time() - start_time
            self.stats['total_recognitions'] += 1
            self.stats['total_duration'] += audio.duration
            
            if result:
                self.stats['successful_recognitions'] += 1
                self.stats['average_processing_time'] = (
                    (self.stats['average_processing_time'] * (self.stats['successful_recognitions'] - 1) + processing_time) /
                    self.stats['successful_recognitions']
                )
                self.stats['average_confidence'] = (
                    (self.stats['average_confidence'] * (self.stats['successful_recognitions'] - 1) + result.confidence) /
                    self.stats['successful_recognitions']
                )
            else:
                self.stats['failed_recognitions'] += 1
            
            self.state = RecognitionState.COMPLETE
            self.current_recognition = result
            
            return result
            
        except Exception as e:
            self.state = RecognitionState.ERROR
            self.stats['failed_recognitions'] += 1
            self.logger.error(f"Error recognizing speech: {e}")
            return None
    
    async def _recognize_with_speech_recognition(self,
                                                audio: AudioSegment,
                                                config: RecognitionConfig,
                                                language: str) -> Optional[RecognitionResult]:
        """Recognize speech using SpeechRecognition library."""
        try:
            import speech_recognition as sr
            
            recognizer = self.engines[RecognitionEngine.SPEECH_RECOGNITION]
            
            # Convert audio to format expected by SpeechRecognition
            audio_data = self._convert_audio_for_sr(audio)
            
            if audio_data is None:
                return None
            
            # Perform recognition
            try:
                # Try Google Speech Recognition first
                text = recognizer.recognize_google(
                    audio_data,
                    language=language,
                    show_all=config.enable_alternatives
                )
                
                if isinstance(text, dict):
                    # Multiple alternatives
                    alternatives = []
                    for i, alt in enumerate(text.get('alternative', [])):
                        alternatives.append({
                            'text': alt.get('transcript', ''),
                            'confidence': alt.get('confidence', 0.0)
                        })
                    
                    # Use highest confidence as primary result
                    primary = alternatives[0] if alternatives else {'text': '', 'confidence': 0.0}
                    recognized_text = primary['text']
                    confidence = primary['confidence']
                else:
                    # Single result
                    recognized_text = text
                    alternatives = [{'text': text, 'confidence': 1.0}]
                    confidence = 1.0  # Google doesn't provide confidence for single results
                
                # Apply confidence threshold
                if confidence < config.confidence_threshold:
                    self.logger.warning(f"Recognition confidence {confidence} below threshold {config.confidence_threshold}")
                    return None
                
                # Apply automatic punctuation
                if config.enable_automatic_punctuation:
                    recognized_text = self._add_automatic_punctuation(recognized_text)
                
                # Apply profanity filter
                if config.enable_profanity_filter:
                    recognized_text = self._filter_profanity(recognized_text)
                
                return RecognitionResult(
                    text=recognized_text,
                    confidence=confidence,
                    alternatives=alternatives[:config.max_alternatives],
                    language=language,
                    duration=audio.duration,
                    processing_time=0.0,  # Will be set by caller
                    engine='speech_recognition',
                    metadata={'method': 'google'}
                )
                
            except sr.UnknownValueError:
                self.logger.warning("SpeechRecognition could not understand audio")
                return None
            except sr.RequestError as e:
                self.logger.error(f"SpeechRecognition service error: {e}")
                return None
            
        except Exception as e:
            self.logger.error(f"Error recognizing with SpeechRecognition: {e}")
            return None
    
    def _convert_audio_for_sr(self, audio: AudioSegment) -> Optional[Any]:
        """Convert audio segment to format expected by SpeechRecognition."""
        try:
            import speech_recognition as sr
            
            # Convert to 16-bit PCM
            if audio.data.dtype != np.int16:
                audio_data = (audio.data * 32767).astype(np.int16)
            else:
                audio_data = audio.data
            
            # Create AudioData object
            audio_data = sr.AudioData(
                audio_data.tobytes(),
                sample_rate=audio.sample_rate,
                sample_width=audio.data.dtype.itemsize
            )
            
            return audio_data
            
        except Exception as e:
            self.logger.error(f"Error converting audio for SpeechRecognition: {e}")
            return None
    
    def _add_automatic_punctuation(self, text: str) -> str:
        """Add automatic punctuation to text."""
        try:
            # Simple punctuation rules
            text = text.strip()
            
            # Add period at end if no punctuation
            if text and text[-1] not in '.!?':
                text += '.'
            
            # Capitalize first letter
            if text:
                text = text[0].upper() + text[1:]
            
            return text
            
        except Exception as e:
            self.logger.error(f"Error adding automatic punctuation: {e}")
            return text
    
    def _filter_profanity(self, text: str) -> str:
        """Filter profanity from text."""
        try:
            # Simple profanity filter - in a real implementation, use a comprehensive list
            profanity_list = ['damn', 'hell', 'shit', 'fuck', 'ass']
            words = text.split()
            
            filtered_words = []
            for word in words:
                # Remove punctuation for checking
                clean_word = word.lower().strip('.,!?')
                if clean_word in profanity_list:
                    # Replace with asterisks
                    filtered_words.append(word[0] + '*' * (len(word) - 1))
                else:
                    filtered_words.append(word)
            
            return ' '.join(filtered_words)
            
        except Exception as e:
            self.logger.error(f"Error filtering profanity: {e}")
            return text
    
    def get_state(self) -> RecognitionState:
        """Get current recognition state."""
        return self.state
    
    def get_current_recognition(self) -> Optional[RecognitionResult]:
        """Get current recognition result."""
        return self.current_recognition
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get recognition statistics."""
        stats = self.stats.copy()
        
        # Calculate success rate
        if stats['total_recognitions'] > 0:
            stats['success_rate'] = stats['successful_recognitions'] / stats['total_recognitions']
        else:
            stats['success_rate'] = 0.0
        
        return stats
    
    def reset_statistics(self) -> None:
        """Reset recognition statistics."""
        self.stats = {
            'total_recognitions': 0,
            'successful_recognitions': 0,
            'failed_recognitions': 0,
            'average_confidence': 0.0,
            'average_processing_time': 0.0,
            'total_duration': 0.0
        }
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        try:
            self.engines.clear()
            self.state = RecognitionState.IDLE
            self.current_recognition = None
            
            self.logger.info("Speech recognizer cleanup complete")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")


# Global speech recognizer instance
_global_speech_recognizer: Optional[SpeechRecognizer] = None


def get_speech_recognizer() -> Optional[SpeechRecognizer]:
    """
    Get the global speech recognizer instance.
    
    Returns:
        Global SpeechRecognizer instance or None if not initialized
    """
    return _global_speech_recognizer


def initialize_speech_recognizer(config: FrameworkConfig) -> SpeechRecognizer:
    """
    Initialize the global speech recognizer.
    
    Args:
        config: Framework configuration
        
    Returns:
        Initialized SpeechRecognizer instance
    """
    global _global_speech_recognizer
    _global_speech_recognizer = SpeechRecognizer(config)
    return _global_speech_recognizer


def shutdown_speech_recognizer() -> None:
    """Shutdown the global speech recognizer."""
    global _global_speech_recognizer
    if _global_speech_recognizer:
        asyncio.create_task(_global_speech_recognizer.cleanup())
        _global_speech_recognizer = None