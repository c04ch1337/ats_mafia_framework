
"""
ATS MAFIA Framework Voice Analysis System

This module provides voice analysis capabilities for the ATS MAFIA framework.
Includes emotion analysis, stress detection, psychological profiling, and deception detection.
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
from .core import AudioSegment


class EmotionType(Enum):
    """Types of emotions."""
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    FEARFUL = "fearful"
    DISGUSTED = "disgusted"
    SURPRISED = "surprised"
    ANXIOUS = "anxious"
    CONFIDENT = "confident"
    UNCERTAIN = "uncertain"


class StressLevel(Enum):
    """Levels of stress."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class PsychologicalTrait:
    """Psychological trait."""
    trait_name: str
    value: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    description: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'trait_name': self.trait_name,
            'value': self.value,
            'confidence': self.confidence,
            'description': self.description
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PsychologicalTrait':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class Emotion:
    """Emotion analysis result."""
    emotion_type: EmotionType
    intensity: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'emotion_type': self.emotion_type.value,
            'intensity': self.intensity,
            'confidence': self.confidence,
            'timestamp': self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Emotion':
        """Create from dictionary."""
        return cls(
            emotion_type=EmotionType(data['emotion_type']),
            intensity=data['intensity'],
            confidence=data['confidence'],
            timestamp=datetime.fromisoformat(data['timestamp'])
        )


@dataclass
class StressResult:
    """Stress analysis result."""
    stress_level: StressLevel
    stress_value: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    indicators: List[str]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'stress_level': self.stress_level.value,
            'stress_value': self.stress_value,
            'confidence': self.confidence,
            'indicators': self.indicators,
            'timestamp': self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StressResult':
        """Create from dictionary."""
        return cls(
            stress_level=StressLevel(data['stress_level']),
            stress_value=data['stress_value'],
            confidence=data['confidence'],
            indicators=data['indicators'],
            timestamp=datetime.fromisoformat(data['timestamp'])
        )


@dataclass
class PsychologicalProfile:
    """Psychological profile result."""
    traits: List[PsychologicalTrait]
    personality_type: str
    confidence: float  # 0.0 to 1.0
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'traits': [trait.to_dict() for trait in self.traits],
            'personality_type': self.personality_type,
            'confidence': self.confidence,
            'timestamp': self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PsychologicalProfile':
        """Create from dictionary."""
        return cls(
            traits=[PsychologicalTrait.from_dict(trait) for trait in data['traits']],
            personality_type=data['personality_type'],
            confidence=data['confidence'],
            timestamp=datetime.fromisoformat(data['timestamp'])
        )


@dataclass
class DeceptionResult:
    """Deception analysis result."""
    deception_probability: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    indicators: List[str]
    voice_patterns: Dict[str, Any]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'deception_probability': self.deception_probability,
            'confidence': self.confidence,
            'indicators': self.indicators,
            'voice_patterns': self.voice_patterns,
            'timestamp': self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DeceptionResult':
        """Create from dictionary."""
        return cls(
            deception_probability=data['deception_probability'],
            confidence=data['confidence'],
            indicators=data['indicators'],
            voice_patterns=data['voice_patterns'],
            timestamp=datetime.fromisoformat(data['timestamp'])
        )


class VoiceFeatureExtractor:
    """Extracts features from voice audio."""
    
    def __init__(self, config: FrameworkConfig):
        """
        Initialize the voice feature extractor.
        
        Args:
            config: Framework configuration
        """
        self.config = config
        self.logger = logging.getLogger("voice_feature_extractor")
    
    async def extract_features(self, audio_segment: AudioSegment) -> Dict[str, Any]:
        """
        Extract features from audio segment.
        
        Args:
            audio_segment: Audio segment to analyze
            
        Returns:
            Dictionary of extracted features
        """
        try:
            features = {}
            
            # Basic audio features
            features['duration'] = audio_segment.duration
            features['sample_rate'] = audio_segment.sample_rate
            features['channels'] = audio_segment.channels
            
            # Extract pitch features
            features['pitch'] = self._extract_pitch_features(audio_segment)
            
            # Extract energy features
            features['energy'] = self._extract_energy_features(audio_segment)
            
            # Extract spectral features
            features['spectral'] = self._extract_spectral_features(audio_segment)
            
            # Extract temporal features
            features['temporal'] = self._extract_temporal_features(audio_segment)
            
            return features
            
        except Exception as e:
            self.logger.error(f"Error extracting features: {e}")
            return {}
    
    def _extract_pitch_features(self, audio_segment: AudioSegment) -> Dict[str, float]:
        """Extract pitch features from audio."""
        try:
            # Mock implementation - in a real system, this would use signal processing
            audio_data = audio_segment.data
            
            # Calculate basic pitch statistics
            if len(audio_data) > 0:
                # Mock pitch values
                pitch_mean = 200.0  # Hz
                pitch_std = 50.0    # Hz
                pitch_min = 100.0   # Hz
                pitch_max = 400.0   # Hz
                
                return {
                    'mean': pitch_mean,
                    'std': pitch_std,
                    'min': pitch_min,
                    'max': pitch_max
                }
            else:
                return {'mean': 0.0, 'std': 0.0, 'min': 0.0, 'max': 0.0}
                
        except Exception as e:
            self.logger.error(f"Error extracting pitch features: {e}")
            return {'mean': 0.0, 'std': 0.0, 'min': 0.0, 'max': 0.0}
    
    def _extract_energy_features(self, audio_segment: AudioSegment) -> Dict[str, float]:
        """Extract energy features from audio."""
        try:
            audio_data = audio_segment.data
            
            if len(audio_data) > 0:
                # Calculate energy statistics
                energy_mean = np.mean(audio_data ** 2)
                energy_std = np.std(audio_data ** 2)
                energy_max = np.max(audio_data ** 2)
                
                return {
                    'mean': float(energy_mean),
                    'std': float(energy_std),
                    'max': float(energy_max)
                }
            else:
                return {'mean': 0.0, 'std': 0.0, 'max': 0.0}
                
        except Exception as e:
            self.logger.error(f"Error extracting energy features: {e}")
            return {'mean': 0.0, 'std': 0.0, 'max': 0.0}
    
    def _extract_spectral_features(self, audio_segment: AudioSegment) -> Dict[str, float]:
        """Extract spectral features from audio."""
        try:
            audio_data = audio_segment.data
            
            if len(audio_data) > 0:
                # Mock spectral features
                spectral_centroid = 1000.0  # Hz
                spectral_bandwidth = 500.0   # Hz
                spectral_rolloff = 2000.0    # Hz
                
                return {
                    'centroid': spectral_centroid,
                    'bandwidth': spectral_bandwidth,
                    'rolloff': spectral_rolloff
                }
            else:
                return {'centroid': 0.0, 'bandwidth': 0.0, 'rolloff': 0.0}
                
        except Exception as e:
            self.logger.error(f"Error extracting spectral features: {e}")
            return {'centroid': 0.0, 'bandwidth': 0.0, 'rolloff': 0.0}
    
    def _extract_temporal_features(self, audio_segment: AudioSegment) -> Dict[str, float]:
        """Extract temporal features from audio."""
        try:
            audio_data = audio_segment.data
            
            if len(audio_data) > 0:
                # Mock temporal features
                zero_crossing_rate = 0.1
                tempo = 120.0  # BPM
                
                return {
                    'zero_crossing_rate': zero_crossing_rate,
                    'tempo': tempo
                }
            else:
                return {'zero_crossing_rate': 0.0, 'tempo': 0.0}
                
        except Exception as e:
            self.logger.error(f"Error extracting temporal features: {e}")
            return {'zero_crossing_rate': 0.0, 'tempo': 0.0}


class EmotionAnalyzer:
    """Analyzes emotions from voice features."""
    
    def __init__(self, config: FrameworkConfig):
        """
        Initialize the emotion analyzer.
        
        Args:
            config: Framework configuration
        """
        self.config = config
        self.logger = logging.getLogger("emotion_analyzer")
    
    async def analyze_emotion(self, features: Dict[str, Any]) -> Emotion:
        """
        Analyze emotion from voice features.
        
        Args:
            features: Voice features
            
        Returns:
            Emotion analysis result
        """
        try:
            # Mock emotion analysis - in a real system, this would use ML models
            pitch_mean = features.get('pitch', {}).get('mean', 200.0)
            energy_mean = features.get('energy', {}).get('mean', 0.1)
            
            # Simple rule-based emotion detection
            if pitch_mean > 250 and energy_mean > 0.2:
                emotion_type = EmotionType.ANGRY
                intensity = min(1.0, (pitch_mean - 200) / 100 + energy_mean)
            elif pitch_mean < 150 and energy_mean < 0.05:
                emotion_type = EmotionType.SAD
                intensity = min(1.0, (200 - pitch_mean) / 50 + (0.1 - energy_mean) * 10)
            elif pitch_mean > 220 and energy_mean > 0.15:
                emotion_type = EmotionType.HAPPY
                intensity = min(1.0, (pitch_mean - 200) / 100 + energy_mean)
            else:
                emotion_type = EmotionType.NEUTRAL
                intensity = 0.5
            
            confidence = 0.7  # Mock confidence
            
            return Emotion(
                emotion_type=emotion_type,
                intensity=intensity,
                confidence=confidence,
                timestamp=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing emotion: {e}")
            
            # Return neutral emotion as fallback
            return Emotion(
                emotion_type=EmotionType.NEUTRAL,
                intensity=0.5,
                confidence=0.0,
                timestamp=datetime.now(timezone.utc)
            )


class StressAnalyzer:
    """Analyzes stress levels from voice features."""
    
    def __init__(self, config: FrameworkConfig):
        """
        Initialize the stress analyzer.
        
        Args:
            config: Framework configuration
        """
        self.config = config
        self.logger = logging.getLogger("stress_analyzer")
    
    async def analyze_stress(self, features: Dict[str, Any]) -> StressResult:
        """
        Analyze stress from voice features.
        
        Args:
            features: Voice features
            
        Returns:
            Stress analysis result
        """
        try:
            # Mock stress analysis - in a real system, this would use ML models
            pitch_std = features.get('pitch', {}).get('std', 50.0)
            zero_crossing_rate = features.get('temporal', {}).get('zero_crossing_rate', 0.1)
            
            # Calculate stress value based on voice patterns
            stress_value = min(1.0, (pitch_std / 100) + zero_crossing_rate * 2)
            
            # Determine stress level
            if stress_value < 0.3:
                stress_level = StressLevel.LOW
            elif stress_value < 0.6:
                stress_level = StressLevel.MEDIUM
            elif stress_value < 0.8:
                stress_level = StressLevel.HIGH
            else:
                stress_level = StressLevel.CRITICAL
            
            # Generate indicators
            indicators = []
            if pitch_std > 60:
                indicators.append("High pitch variability")
            if zero_crossing_rate > 0.15:
                indicators.append("Rapid speech patterns")
            if stress_value > 0.7:
                indicators.append("Stressed vocal patterns")
            
            confidence = 0.75  # Mock confidence
            
            return StressResult(
                stress_level=stress_level,
                stress_value=stress_value,
                confidence=confidence,
                indicators=indicators,
                timestamp=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing stress: {e}")
            
            # Return low stress as fallback
            return StressResult(
                stress_level=StressLevel.LOW,
                stress_value=0.0,
                confidence=0.0,
                indicators=[],
                timestamp=datetime.now(timezone.utc)
            )


class PsychologicalProfiler:
    """Analyzes psychological profile from voice features and text."""
    
    def __init__(self, config: FrameworkConfig):
        """
        Initialize the psychological profiler.
        
        Args:
            config: Framework configuration
        """
        self.config = config
        self.logger = logging.getLogger("psychological_profiler")
    
    async def analyze_psychological_profile(self,
                                          features: Dict[str, Any],
                                          text_content: str) -> PsychologicalProfile:
        """
        Analyze psychological profile from voice features and text.
        
        Args:
            features: Voice features
            text_content: Text content of speech
            
        Returns:
            Psychological profile result
        """
        try:
            traits = []
            
            # Analyze confidence from voice features
            pitch_mean = features.get('pitch', {}).get('mean', 200.0)
            energy_mean = features.get('energy', {}).get('mean', 0.1)
            
            # Confidence trait
            if pitch_mean > 180 and energy_mean > 0.1:
                confidence_value = min(1.0, (pitch_mean - 150) / 100 + energy_mean * 5)
            else:
                confidence_value = max(0.0, 1.0 - ((200 - pitch_mean) / 100 + (0.1 - energy_mean) * 5))
            
            traits.append(PsychologicalTrait(
                trait_name="confidence",
                value=confidence_value,
                confidence=0.7,
                description="Level of confidence in communication"
            ))
            
            # Analyze openness from text content
            text_length = len(text_content)
            question_count = text_content.count('?')
            
            # Openness trait
            if text_length > 100 and question_count > 2:
                openness_value = min(1.0, (question_count / text_length * 100))
            else:
                openness_value = max(0.0, 1.0 - ((50 - text_length) / 50 + (2 - question_count) / 2))
            
            traits.append(PsychologicalTrait(
                trait_name="openness",
                value=openness_value,
                confidence=0.6,
                description="Willingness to share information and engage"
            ))
            
            # Determine personality type
            if confidence_value > 0.7 and openness_value > 0.7:
                personality_type = "Extroverted Leader"
            elif confidence_value > 0.7 and openness_value < 0.3:
                personality_type = "Confident Reserved"
            elif confidence_value < 0.3 and openness_value > 0.7:
                personality_type = "Open Collaborator"
            else:
                personality_type = "Balanced Communicator"
            
            overall_confidence = 0.65  # Mock overall confidence
            
            return PsychologicalProfile(
                traits=traits,
                personality_type=personality_type,
                confidence=overall_confidence,
                timestamp=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing psychological profile: {e}")
            
            # Return neutral profile as fallback
            return PsychologicalProfile(
                traits=[],
                personality_type="Unknown",
                confidence=0.0,
                timestamp=datetime.now(timezone.utc)
            )


class DeceptionAnalyzer:
    """Analyzes deception indicators from voice features and text."""
    
    def __init__(self, config: FrameworkConfig):
        """
        Initialize the deception analyzer.
        
        Args:
            config: Framework configuration
        """
        self.config = config
        self.logger = logging.getLogger("deception_analyzer")
    
    async def analyze_deception(self,
                              features: Dict[str, Any],
                              text_content: str) -> DeceptionResult:
        """
        Analyze deception from voice features and text.
        
        Args:
            features: Voice features
            text_content: Text content of speech
            
        Returns:
            Deception analysis result
        """
        try:
            # Mock deception analysis - in a real system, this would use ML models
            pitch_std = features.get('pitch', {}).get('std', 50.0)
            zero_crossing_rate = features.get('temporal', {}).get('zero_crossing_rate', 0.1)
            
            # Calculate deception probability
            deception_probability = min(1.0, (pitch_std / 150) + zero_crossing_rate * 3)
            
            # Generate indicators
            indicators = []
            voice_patterns = {}
            
            if pitch_std > 80:
                indicators.append("Unusual pitch variations")
                voice_patterns['pitch_instability'] = True
            
            if zero_crossing_rate > 0.2:
                indicators.append("Irregular speech patterns")
                voice_patterns['speech_irregularity'] = True
            
            # Text-based indicators
            if "um" in text_content.lower() or "uh" in text_content.lower():
                indicators.append("Hesitation patterns")
                voice_patterns['hesitation'] = True
            
            if len(text_content.split()) < 5:
                indicators.append("Short responses")
                voice_patterns['brief_responses'] = True
            
            confidence = 0.6  # Mock confidence
            
            return DeceptionResult(
                deception_probability=deception_probability,
                confidence=confidence,
                indicators=indicators,
                voice_patterns=voice_patterns,
                timestamp=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing deception: {e}")
            
            # Return low deception probability as fallback
            return DeceptionResult(
                deception_probability=0.0,
                confidence=0.0,
                indicators=[],
                voice_patterns={},
                timestamp=datetime.now(timezone.utc)
            )


class VoiceAnalysisManager:
    """
    Manager for voice analysis in the ATS MAFIA framework.
    
    Coordinates all voice analysis components.
    """
    
    def __init__(self,
                 config: FrameworkConfig,
                 audit_logger: Optional[AuditLogger] = None):
        """
        Initialize the voice analysis manager.
        
        Args:
            config: Framework configuration
            audit_logger: Audit logger instance
        """
        self.config = config
        self.audit_logger = audit_logger
        self.logger = logging.getLogger("voice_analysis_manager")
        
        # Analysis components
        self.feature_extractor = VoiceFeatureExtractor(config)
        self.emotion_analyzer = EmotionAnalyzer(config)
        self.stress_analyzer = StressAnalyzer(config)
        self.psychological_profiler = PsychologicalProfiler(config)
        self.deception_analyzer = DeceptionAnalyzer(config)
        
        # Statistics
        self.statistics = {
            'total_analyses': 0,
            'emotion_analyses': 0,
            'stress_analyses': 0,
            'psychological_analyses': 0,
            'deception_analyses': 0
        }
    
    async def analyze_emotion(self, audio_segment: AudioSegment) -> Emotion:
        """
        Analyze emotion from audio.
        
        Args:
            audio_segment: Audio segment to analyze
            
        Returns:
            Emotion analysis result
        """
        try:
            # Extract features
            features = await self.feature_extractor.extract_features(audio_segment)
            
            # Analyze emotion
            result = await self.emotion_analyzer.analyze_emotion(features)
            
            # Update statistics
            self.statistics['total_analyses'] += 1
            self.statistics['emotion_analyses'] += 1
            
            # Log to audit
            if self.audit_logger:
                self.audit_logger.audit(
                    event_type=AuditEventType.SYSTEM_EVENT,
                    action="voice_emotion_analyzed",
                    details={
                        'emotion_type': result.emotion_type.value,
                        'intensity': result.intensity,
                        'confidence': result.confidence
                    },
                    security_level=SecurityLevel.MEDIUM
                )
            
            self.logger.debug(f"Analyzed emotion: {result.emotion_type.value}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error analyzing emotion: {e}")
            raise
    
    async def analyze_stress(self, audio_segment: AudioSegment) -> StressResult:
        """
        Analyze stress from audio.
        
        Args:
            audio_segment: Audio segment to analyze
            
        Returns:
            Stress analysis result
        """
        try:
            # Extract features
            features = await self.feature_extractor.extract_features(audio_segment)
            
            # Analyze stress
            result = await self.stress_analyzer.analyze_stress(features)
            
            # Update statistics
            self.statistics['total_analyses'] += 1
            self.statistics['stress_analyses'] += 1
            
            # Log to audit
            if self.audit_logger:
                self.audit_logger.audit(
                    event_type=AuditEventType.SYSTEM_EVENT,
                    action="voice_stress_analyzed",
                    details={
                        'stress_level': result.stress_level.value,
                        'stress_value': result.stress_value,
                        'confidence': result.confidence
                    },
                    security_level=SecurityLevel.MEDIUM
                )
            
            self.logger.debug(f"Analyzed stress: {result.stress_level.value}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error analyzing stress: {e}")
            raise
    
    async def analyze_psychological_profile(self,
                                          audio_segment: AudioSegment,
                                          text_content: str) -> PsychologicalProfile:
        """
        Analyze psychological profile from audio and text.
        
        Args:
            audio_segment: Audio segment to analyze
            text_content: Text content of speech
            
        Returns:
            Psychological profile result
        """
        try:
            # Extract features
            features = await self.feature_extractor.extract_features(audio_segment)
            
            # Analyze psychological profile
            result = await self.psychological_profiler.analyze_psychological_profile(features, text_content)
            
            # Update statistics
            self.statistics['total_analyses'] += 1
            self.statistics['psychological_analyses'] += 1
            
            # Log to audit
            if self.audit_logger:
                self.audit_logger.audit(
                    event_type=AuditEventType.SYSTEM_EVENT,
                    action="voice_psychological_profile_analyzed",
                    details={
                        'personality_type': result.personality_type,
                        'confidence': result.confidence,
                        'traits_count': len(result.traits)
                    },
                    security_level=SecurityLevel.MEDIUM
                )
            
            self.logger.debug(f"Analyzed psychological profile: {result.personality_type}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error analyzing psychological profile: {e}")
            raise
    
    async def analyze_deception(self,
                              audio_segment: AudioSegment,
                              text_content: str) -> DeceptionResult:
        """
        Analyze deception from audio and text.
        
        Args:
            audio_segment: Audio segment to analyze
            text_content: Text content of speech
            
        Returns:
            Deception analysis result
        """
        try:
            # Extract features
            features = await self.feature_extractor.extract_features(audio_segment)
            
            # Analyze deception
            result = await self.deception_analyzer.analyze_deception(features, text_content)
            
            # Update statistics
            self.statistics['total_analyses'] += 1
            self.statistics['deception_analyses'] += 1
            
            # Log to audit if high deception probability
            if result.deception_probability > 0.7 and self.audit_logger:
                self.audit_logger.audit(
                    event_type=AuditEventType.SECURITY_EVENT,
                    action="high_deception_probability_detected",
                    details={
                        'deception_probability': result.deception_probability,
                        'confidence': result.confidence,
                        'indicators': result.indicators
                    },
                    security_level=SecurityLevel.HIGH
                )
            
            self.logger.debug(f"Analyzed deception: {result.deception_probability:.2f}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error analyzing deception: {e}")
            raise
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get voice analysis statistics.
        
        Returns:
            Dictionary containing statistics
        """
        return self.statistics.copy()
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        try:
            self.logger.info("Voice analysis manager cleanup complete")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")


# Global voice analysis manager instance
_global_voice_analysis_manager: Optional[VoiceAnalysisManager] = None


def get_voice_analysis_manager() -> Optional[VoiceAnalysisManager]:
    """
    Get the global voice analysis manager instance.
    
    Returns:
        Global VoiceAnalysisManager instance or None if not initialized
    """
    return _global_voice_analysis_manager


def initialize_voice_analysis_manager(config: FrameworkConfig,
                                    audit_logger: Optional[AuditLogger] = None) -> VoiceAnalysisManager:
    """
    Initialize the global voice analysis manager.
    
    Args:
        config: Framework configuration
        audit_logger: Audit logger instance
        
    Returns:
        Initialized VoiceAnalysisManager instance
    """
    global _global_voice_analysis_manager
    _global_voice_analysis_manager = VoiceAnalysisManager(config, audit_logger)
    return _global_voice_analysis_manager


def shutdown_voice_analysis_manager() -> None:
    """Shutdown the global voice analysis manager."""
    global _global_voice_analysis_manager
    if _global_voice_analysis_manager:
        asyncio.create_task(_global_voice_analysis_manager.cleanup())
        _global_voice_analysis_manager = None
