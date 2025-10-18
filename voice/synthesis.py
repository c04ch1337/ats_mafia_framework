"""
ATS MAFIA Framework Voice Synthesis

This module provides text-to-speech synthesis capabilities for the ATS MAFIA framework.
Includes voice synthesis, voice persona management, and real-time audio generation.
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

from .core import AudioSegment, AudioFormat, VoicePersonaConfig
from ..config.settings import FrameworkConfig


class SynthesisEngine(Enum):
    """Types of synthesis engines."""
    PYTTSX3 = "pyttsx3"
    OPENAI = "openai"
    GOOGLE = "google"
    AZURE = "azure"
    AWS = "aws"
    CUSTOM = "custom"


class VoiceGender(Enum):
    """Voice gender options."""
    MALE = "male"
    FEMALE = "female"
    NEUTRAL = "neutral"


class VoiceAge(Enum):
    """Voice age options."""
    CHILD = "child"
    YOUNG = "young"
    ADULT = "adult"
    ELDERLY = "elderly"


@dataclass
class VoiceProfile:
    """Voice profile for synthesis."""
    profile_id: str
    name: str
    description: str
    gender: VoiceGender
    age: VoiceAge
    language: str
    accent: str
    engine: SynthesisEngine
    engine_voice_id: str
    default_settings: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'profile_id': self.profile_id,
            'name': self.name,
            'description': self.description,
            'gender': self.gender.value,
            'age': self.age.value,
            'language': self.language,
            'accent': self.accent,
            'engine': self.engine.value,
            'engine_voice_id': self.engine_voice_id,
            'default_settings': self.default_settings,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VoiceProfile':
        """Create from dictionary."""
        return cls(
            profile_id=data['profile_id'],
            name=data['name'],
            description=data['description'],
            gender=VoiceGender(data['gender']),
            age=VoiceAge(data['age']),
            language=data['language'],
            accent=data['accent'],
            engine=SynthesisEngine(data['engine']),
            engine_voice_id=data['engine_voice_id'],
            default_settings=data.get('default_settings', {}),
            metadata=data.get('metadata', {})
        )


class VoiceSynthesizer:
    """Voice synthesizer for text-to-speech conversion."""
    
    def __init__(self, config: FrameworkConfig):
        """
        Initialize the voice synthesizer.
        
        Args:
            config: Framework configuration
        """
        self.config = config
        self.logger = logging.getLogger("voice_synthesizer")
        
        # Configuration
        self.default_engine = SynthesisEngine(config.get('voice.synthesis.default_engine', 'pyttsx3'))
        self.default_language = config.get('voice.synthesis.default_language', 'en-US')
        self.default_format = AudioFormat(config.get('voice.synthesis.default_format', 'wav'))
        self.default_sample_rate = config.get('voice.synthesis.default_sample_rate', 22050)
        
        # Voice profiles
        self.voice_profiles: Dict[str, VoiceProfile] = {}
        
        # Synthesis engines
        self.engines: Dict[SynthesisEngine, Any] = {}
        
        # Load default voice profiles
        self._load_default_voice_profiles()
        
        # Initialize engines
        asyncio.create_task(self._initialize_engines())
    
    def _load_default_voice_profiles(self) -> None:
        """Load default voice profiles."""
        # English male adult
        self.voice_profiles['en_male_adult'] = VoiceProfile(
            profile_id='en_male_adult',
            name='English Male Adult',
            description='Standard adult male voice with American accent',
            gender=VoiceGender.MALE,
            age=VoiceAge.ADULT,
            language='en-US',
            accent='american',
            engine=SynthesisEngine.PYTTSX3,
            engine_voice_id='default_male',
            default_settings={
                'rate': 200,
                'volume': 0.9,
                'pitch': 1.0
            }
        )
        
        # English female adult
        self.voice_profiles['en_female_adult'] = VoiceProfile(
            profile_id='en_female_adult',
            name='English Female Adult',
            description='Standard adult female voice with American accent',
            gender=VoiceGender.FEMALE,
            age=VoiceAge.ADULT,
            language='en-US',
            accent='american',
            engine=SynthesisEngine.PYTTSX3,
            engine_voice_id='default_female',
            default_settings={
                'rate': 200,
                'volume': 0.9,
                'pitch': 1.0
            }
        )
        
        # British male adult
        self.voice_profiles['en_male_british'] = VoiceProfile(
            profile_id='en_male_british',
            name='British Male Adult',
            description='Adult male voice with British accent',
            gender=VoiceGender.MALE,
            age=VoiceAge.ADULT,
            language='en-GB',
            accent='british',
            engine=SynthesisEngine.PYTTSX3,
            engine_voice_id='british_male',
            default_settings={
                'rate': 190,
                'volume': 0.9,
                'pitch': 0.95
            }
        )
    
    async def _initialize_engines(self) -> None:
        """Initialize synthesis engines."""
        try:
            # Initialize PyTTSX3 engine
            await self._initialize_pyttsx3_engine()
            
            # Initialize other engines as needed
            # await self._initialize_openai_engine()
            # await self._initialize_google_engine()
            
            self.logger.info("Voice synthesis engines initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing synthesis engines: {e}")
    
    async def _initialize_pyttsx3_engine(self) -> None:
        """Initialize PyTTSX3 engine."""
        try:
            import pyttsx3
            
            engine = pyttsx3.init()
            self.engines[SynthesisEngine.PYTTSX3] = engine
            
            # Get available voices
            voices = engine.getProperty('voices')
            self.logger.info(f"PyTTSX3 engine initialized with {len(voices)} voices")
            
        except ImportError:
            self.logger.warning("PyTTSX3 not available")
        except Exception as e:
            self.logger.error(f"Error initializing PyTTSX3 engine: {e}")
    
    async def synthesize(self,
                        text: str,
                        persona: Optional[VoicePersonaConfig] = None,
                        voice_profile: Optional[str] = None,
                        format: Optional[AudioFormat] = None,
                        settings: Optional[Dict[str, Any]] = None) -> Optional[AudioSegment]:
        """
        Synthesize speech from text.
        
        Args:
            text: Text to synthesize
            persona: Voice persona to use
            voice_profile: Voice profile to use
            format: Output audio format
            settings: Additional synthesis settings
            
        Returns:
            Audio segment with synthesized speech
        """
        try:
            if not text.strip():
                return None
            
            # Determine voice profile
            if voice_profile:
                profile = self.voice_profiles.get(voice_profile)
                if not profile:
                    self.logger.warning(f"Voice profile not found: {voice_profile}")
                    profile = self.voice_profiles.get('en_male_adult')
            else:
                profile = self.voice_profiles.get('en_male_adult')
            
            if not profile:
                raise RuntimeError("No voice profile available")
            
            # Merge settings
            synthesis_settings = profile.default_settings.copy()
            if persona:
                synthesis_settings.update(self._persona_to_settings(persona))
            if settings:
                synthesis_settings.update(settings)
            
            # Synthesize using appropriate engine
            if profile.engine == SynthesisEngine.PYTTSX3:
                audio_segment = await self._synthesize_with_pyttsx3(
                    text, profile, synthesis_settings, format or self.default_format
                )
            else:
                # For other engines, fall back to PyTTSX3
                audio_segment = await self._synthesize_with_pyttsx3(
                    text, profile, synthesis_settings, format or self.default_format
                )
            
            # Apply persona-based modifications if needed
            if persona:
                audio_segment = await self._apply_persona_modifications(
                    audio_segment, persona, synthesis_settings
                )
            
            return audio_segment
            
        except Exception as e:
            self.logger.error(f"Error synthesizing speech: {e}")
            return None
    
    async def _synthesize_with_pyttsx3(self,
                                      text: str,
                                      profile: VoiceProfile,
                                      settings: Dict[str, Any],
                                      format: AudioFormat) -> AudioSegment:
        """Synthesize speech using PyTTSX3."""
        try:
            engine = self.engines.get(SynthesisEngine.PYTTSX3)
            if not engine:
                raise RuntimeError("PyTTSX3 engine not initialized")
            
            # Configure engine
            engine.setProperty('rate', int(settings.get('rate', 200)))
            engine.setProperty('volume', settings.get('volume', 0.9))
            
            # Set voice if available
            voices = engine.getProperty('voices')
            if voices:
                # Try to find matching voice
                for voice in voices:
                    if (profile.gender.value.lower() in voice.name.lower() and
                        profile.accent.lower() in voice.name.lower()):
                        engine.setProperty('voice', voice.id)
                        break
                else:
                    # Fall back to first voice
                    engine.setProperty('voice', voices[0].id)
            
            # Save to temporary file
            temp_file = f"temp_tts_{int(time.time())}.wav"
            engine.save_to_file(text, temp_file)
            engine.runAndWait()
            
            # Read the file
            try:
                import wave
                
                with wave.open(temp_file, 'rb') as wav_file:
                    frames = wav_file.readframes(-1)
                    sound_info = wav_file.getparams()
                    
                    # Convert to numpy array
                    audio_data = np.frombuffer(frames, dtype=np.int16)
                    
                    # Create audio segment
                    audio_segment = AudioSegment(
                        data=audio_data,
                        sample_rate=sound_info.framerate,
                        channels=sound_info.nchannels,
                        format=AudioFormat.WAV,
                        duration=sound_info.nframes / sound_info.framerate
                    )
                
                # Clean up temp file
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                
                return audio_segment
                
            except Exception as e:
                self.logger.error(f"Error reading synthesized audio: {e}")
                # Create empty audio segment as fallback
                return AudioSegment(
                    data=np.array([], dtype=np.int16),
                    sample_rate=self.default_sample_rate,
                    channels=1,
                    format=AudioFormat.WAV,
                    duration=0.0
                )
            
        except Exception as e:
            self.logger.error(f"Error synthesizing with PyTTSX3: {e}")
            # Create empty audio segment as fallback
            return AudioSegment(
                data=np.array([], dtype=np.int16),
                sample_rate=self.default_sample_rate,
                channels=1,
                format=AudioFormat.WAV,
                duration=0.0
            )
    
    def _persona_to_settings(self, persona: VoicePersonaConfig) -> Dict[str, Any]:
        """Convert persona to synthesis settings."""
        settings = {}
        
        # Map persona properties to synthesis settings
        settings['rate'] = int(200 * persona.rate)
        settings['volume'] = persona.volume
        
        # Pitch is handled differently by different engines
        # For PyTTSX3, we'll use the voice selection and rate changes
        
        return settings
    
    async def _apply_persona_modifications(self,
                                         audio_segment: AudioSegment,
                                         persona: VoicePersonaConfig,
                                         settings: Dict[str, Any]) -> AudioSegment:
        """Apply persona-based modifications to audio."""
        try:
            # Convert to numpy array
            audio_array = audio_segment.data.astype(np.float32) / np.max(np.abs(audio_segment.data))
            
            # Apply pitch modification if needed
            if persona.pitch != 1.0:
                audio_array = await self._modify_pitch(audio_array, audio_segment.sample_rate, persona.pitch)
            
            # Apply emotional modulation
            if persona.emotion_modulation > 0.5:
                audio_array = await self._apply_emotional_modulation(
                    audio_array, audio_segment.sample_rate, persona.emotion_modulation
                )
            
            # Convert back to int16
            audio_array = (audio_array * 32767).astype(np.int16)
            
            return AudioSegment(
                data=audio_array,
                sample_rate=audio_segment.sample_rate,
                channels=audio_segment.channels,
                format=audio_segment.format,
                duration=audio_segment.duration
            )
            
        except Exception as e:
            self.logger.error(f"Error applying persona modifications: {e}")
            return audio_segment
    
    async def _modify_pitch(self,
                          audio_array: np.ndarray,
                          sample_rate: int,
                          pitch_factor: float) -> np.ndarray:
        """Modify pitch of audio."""
        try:
            # In a real implementation, this would use a pitch shifting algorithm
            # For now, we'll simulate pitch modification
            
            if pitch_factor == 1.0:
                return audio_array
            
            # Simple resampling approach (not ideal for production)
            if pitch_factor > 1.0:
                # Higher pitch - compress time
                new_length = int(len(audio_array) / pitch_factor)
                audio_array = audio_array[:new_length]
            else:
                # Lower pitch - stretch time
                new_length = int(len(audio_array) / pitch_factor)
                # Pad with zeros
                padding = new_length - len(audio_array)
                if padding > 0:
                    audio_array = np.pad(audio_array, (0, padding), mode='constant')
            
            return audio_array
            
        except Exception as e:
            self.logger.error(f"Error modifying pitch: {e}")
            return audio_array
    
    async def _apply_emotional_modulation(self,
                                        audio_array: np.ndarray,
                                        sample_rate: int,
                                        modulation_intensity: float) -> np.ndarray:
        """Apply emotional modulation to audio."""
        try:
            # In a real implementation, this would apply sophisticated emotional modulation
            # For now, we'll apply simple amplitude modulation
            
            if modulation_intensity <= 0.5:
                return audio_array
            
            # Generate modulation envelope
            duration = len(audio_array) / sample_rate
            t = np.linspace(0, duration, len(audio_array))
            
            # Create emotional modulation (slight vibrato)
            modulation_rate = 5.0  # Hz
            modulation_depth = 0.1 * (modulation_intensity - 0.5)
            
            envelope = 1.0 + modulation_depth * np.sin(2 * np.pi * modulation_rate * t)
            
            # Apply modulation
            modulated_audio = audio_array * envelope
            
            return modulated_audio
            
        except Exception as e:
            self.logger.error(f"Error applying emotional modulation: {e}")
            return audio_array
    
    def add_voice_profile(self, profile: VoiceProfile) -> None:
        """
        Add a voice profile.
        
        Args:
            profile: Voice profile to add
        """
        self.voice_profiles[profile.profile_id] = profile
        self.logger.info(f"Voice profile added: {profile.profile_id}")
    
    def remove_voice_profile(self, profile_id: str) -> bool:
        """
        Remove a voice profile.
        
        Args:
            profile_id: ID of the profile to remove
            
        Returns:
            True if successful, False if not found
        """
        if profile_id in self.voice_profiles:
            del self.voice_profiles[profile_id]
            self.logger.info(f"Voice profile removed: {profile_id}")
            return True
        return False
    
    def get_voice_profile(self, profile_id: str) -> Optional[VoiceProfile]:
        """
        Get a voice profile by ID.
        
        Args:
            profile_id: ID of the profile
            
        Returns:
            Voice profile or None if not found
        """
        return self.voice_profiles.get(profile_id)
    
    def list_voice_profiles(self) -> List[VoiceProfile]:
        """
        List all voice profiles.
        
        Returns:
            List of voice profiles
        """
        return list(self.voice_profiles.values())
    
    def get_available_voices(self) -> List[str]:
        """
        Get list of available voices from engines.
        
        Returns:
            List of voice names
        """
        voices = []
        
        for engine_type, engine in self.engines.items():
            if engine_type == SynthesisEngine.PYTTSX3:
                try:
                    pyttsx3_voices = engine.getProperty('voices')
                    for voice in pyttsx3_voices:
                        voices.append(f"{engine_type.value}:{voice.id}:{voice.name}")
                except Exception as e:
                    self.logger.error(f"Error getting voices from {engine_type}: {e}")
        
        return voices
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        # Stop all engines
        for engine in self.engines.values():
            try:
                if hasattr(engine, 'stop'):
                    engine.stop()
            except Exception as e:
                self.logger.error(f"Error stopping engine: {e}")
        
        self.engines.clear()
        self.logger.info("Voice synthesizer cleanup complete")


# Global voice synthesizer instance
_global_voice_synthesizer: Optional[VoiceSynthesizer] = None


def get_voice_synthesizer() -> Optional[VoiceSynthesizer]:
    """
    Get the global voice synthesizer instance.
    
    Returns:
        Global VoiceSynthesizer instance or None if not initialized
    """
    return _global_voice_synthesizer


def initialize_voice_synthesizer(config: FrameworkConfig) -> VoiceSynthesizer:
    """
    Initialize the global voice synthesizer.
    
    Args:
        config: Framework configuration
        
    Returns:
        Initialized VoiceSynthesizer instance
    """
    global _global_voice_synthesizer
    _global_voice_synthesizer = VoiceSynthesizer(config)
    return _global_voice_synthesizer


def shutdown_voice_synthesizer() -> None:
    """Shutdown the global voice synthesizer."""
    global _global_voice_synthesizer
    if _global_voice_synthesizer:
        asyncio.create_task(_global_voice_synthesizer.cleanup())
        _global_voice_synthesizer = None