
"""
ATS MAFIA Framework Voice Adaptation

This module provides real-time voice adaptation capabilities for the ATS MAFIA framework.
Includes voice modulation, persona adaptation, and dynamic response adjustment.
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
import numpy as np

from .core import VoicePersonaConfig, AudioSegment, AudioFormat
from .analysis import (
    Emotion, StressResult, PsychologicalProfile,
    VoiceAnalysisManager
)
from ..config.settings import FrameworkConfig
from ..core.logging import AuditLogger, AuditEventType, SecurityLevel


class AdaptationType(Enum):
    """Types of voice adaptations."""
    PITCH = "pitch"
    RATE = "rate"
    VOLUME = "volume"
    TONE = "tone"
    EMOTION = "emotion"
    ACCENT = "accent"
    BREATHING = "breathing"
    PERSONALITY = "personality"


class AdaptationTrigger(Enum):
    """Triggers for voice adaptation."""
    EMOTION_CHANGE = "emotion_change"
    STRESS_LEVEL = "stress_level"
    PARTICIPANT_RESPONSE = "participant_response"
    OBJECTIVE_PROGRESS = "objective_progress"
    TIME_ELAPSED = "time_elapsed"
    CONVERSATION_STATE = "conversation_state"
    CUSTOM = "custom"


@dataclass
class AdaptationRule:
    """Rule for voice adaptation."""
    rule_id: str
    name: str
    description: str
    adaptation_type: AdaptationType
    trigger: AdaptationTrigger
    conditions: Dict[str, Any]
    adjustments: Dict[str, Any]
    priority: int = 5  # 1-10, 10 is highest
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'rule_id': self.rule_id,
            'name': self.name,
            'description': self.description,
            'adaptation_type': self.adaptation_type.value,
            'trigger': self.trigger.value,
            'conditions': self.conditions,
            'adjustments': self.adjustments,
            'priority': self.priority,
            'enabled': self.enabled,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AdaptationRule':
        """Create from dictionary."""
        return cls(
            rule_id=data['rule_id'],
            name=data['name'],
            description=data['description'],
            adaptation_type=AdaptationType(data['adaptation_type']),
            trigger=AdaptationTrigger(data['trigger']),
            conditions=data['conditions'],
            adjustments=data['adjustments'],
            priority=data.get('priority', 5),
            enabled=data.get('enabled', True),
            metadata=data.get('metadata', {})
        )


@dataclass
class AdaptationEvent:
    """Event that triggers adaptation."""
    event_id: str
    trigger: AdaptationTrigger
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'event_id': self.event_id,
            'trigger': self.trigger.value,
            'data': self.data,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }


@dataclass
class AdaptationResult:
    """Result of voice adaptation."""
    adaptation_id: str
    rule_id: str
    original_persona: VoicePersonaConfig
    adapted_persona: VoicePersonaConfig
    adjustments_applied: Dict[str, Any]
    confidence: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'adaptation_id': self.adaptation_id,
            'rule_id': self.rule_id,
            'original_persona': self.original_persona.to_dict(),
            'adapted_persona': self.adapted_persona.to_dict(),
            'adjustments_applied': self.adjustments_applied,
            'confidence': self.confidence,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }


class VoiceAdapter:
    """Adapter for voice characteristics."""
    
    def __init__(self, config: FrameworkConfig):
        """
        Initialize the voice adapter.
        
        Args:
            config: Framework configuration
        """
        self.config = config
        self.logger = logging.getLogger("voice_adapter")
    
    def adapt_pitch(self, 
                   persona: VoicePersonaConfig,
                   adjustment: float) -> VoicePersonaConfig:
        """
        Adapt voice pitch.
        
        Args:
            persona: Original persona
            adjustment: Pitch adjustment (-1.0 to 1.0)
            
        Returns:
            Adapted persona
        """
        try:
            # Create adapted persona
            adapted_persona = VoicePersonaConfig(
                name=persona.name,
                description=persona.description,
                pitch=np.clip(persona.pitch + adjustment, 0.5, 2.0),
                rate=persona.rate,
                volume=persona.volume,
                tone=persona.tone,
                accent=persona.accent,
                emotion_modulation=persona.emotion_modulation,
                breathing_style=persona.breathing_style,
                speech_patterns=persona.speech_patterns.copy(),
                psychological_profile=persona.psychological_profile.copy()
            )
            
            return adapted_persona
            
        except Exception as e:
            self.logger.error(f"Error adapting pitch: {e}")
            return persona
    
    def adapt_rate(self, 
                  persona: VoicePersonaConfig,
                  adjustment: float) -> VoicePersonaConfig:
        """
        Adapt voice rate.
        
        Args:
            persona: Original persona
            adjustment: Rate adjustment (-1.0 to 1.0)
            
        Returns:
            Adapted persona
        """
        try:
            # Create adapted persona
            adapted_persona = VoicePersonaConfig(
                name=persona.name,
                description=persona.description,
                pitch=persona.pitch,
                rate=np.clip(persona.rate + adjustment, 0.5, 2.0),
                volume=persona.volume,
                tone=persona.tone,
                accent=persona.accent,
                emotion_modulation=persona.emotion_modulation,
                breathing_style=persona.breathing_style,
                speech_patterns=persona.speech_patterns.copy(),
                psychological_profile=persona.psychological_profile.copy()
            )
            
            return adapted_persona
            
        except Exception as e:
            self.logger.error(f"Error adapting rate: {e}")
            return persona
    
    def adapt_volume(self, 
                    persona: VoicePersonaConfig,
                    adjustment: float) -> VoicePersonaConfig:
        """
        Adapt voice volume.
        
        Args:
            persona: Original persona
            adjustment: Volume adjustment (-1.0 to 1.0)
            
        Returns:
            Adapted persona
        """
        try:
            # Create adapted persona
            adapted_persona = VoicePersonaConfig(
                name=persona.name,
                description=persona.description,
                pitch=persona.pitch,
                rate=persona.rate,
                volume=np.clip(persona.volume + adjustment, 0.0, 1.0),
                tone=persona.tone,
                accent=persona.accent,
                emotion_modulation=persona.emotion_modulation,
                breathing_style=persona.breathing_style,
                speech_patterns=persona.speech_patterns.copy(),
                psychological_profile=persona.psychological_profile.copy()
            )
            
            return adapted_persona
            
        except Exception as e:
            self.logger.error(f"Error adapting volume: {e}")
            return persona
    
    def adapt_tone(self, 
                  persona: VoicePersonaConfig,
                  tone: str) -> VoicePersonaConfig:
        """
        Adapt voice tone.
        
        Args:
            persona: Original persona
            tone: New tone
            
        Returns:
            Adapted persona
        """
        try:
            # Create adapted persona
            adapted_persona = VoicePersonaConfig(
                name=persona.name,
                description=persona.description,
                pitch=persona.pitch,
                rate=persona.rate,
                volume=persona.volume,
                tone=tone,
                accent=persona.accent,
                emotion_modulation=persona.emotion_modulation,
                breathing_style=persona.breathing_style,
                speech_patterns=persona.speech_patterns.copy(),
                psychological_profile=persona.psychological_profile.copy()
            )
            
            return adapted_persona
            
        except Exception as e:
            self.logger.error(f"Error adapting tone: {e}")
            return persona
    
    def adapt_emotion(self, 
                    persona: VoicePersonaConfig,
                    emotion_modulation: float) -> VoicePersonaConfig:
        """
        Adapt emotion modulation.
        
        Args:
            persona: Original persona
            emotion_modulation: New emotion modulation level
            
        Returns:
            Adapted persona
        """
        try:
            # Create adapted persona
            adapted_persona = VoicePersonaConfig(
                name=persona.name,
                description=persona.description,
                pitch=persona.pitch,
                rate=persona.rate,
                volume=persona.volume,
                tone=persona.tone,
                accent=persona.accent,
                emotion_modulation=np.clip(emotion_modulation, 0.0, 1.0),
                breathing_style=persona.breathing_style,
                speech_patterns=persona.speech_patterns.copy(),
                psychological_profile=persona.psychological_profile.copy()
            )
            
            return adapted_persona
            
        except Exception as e:
            self.logger.error(f"Error adapting emotion: {e}")
            return persona
    
    def adapt_psychological_profile(self, 
                                   persona: VoicePersonaConfig,
                                   profile_adjustments: Dict[str, float]) -> VoicePersonaConfig:
        """
        Adapt psychological profile.
        
        Args:
            persona: Original persona
            profile_adjustments: Adjustments to psychological profile
            
        Returns:
            Adapted persona
        """
        try:
            # Create adapted psychological profile
            adapted_profile = persona.psychological_profile.copy()
            
            for trait, adjustment in profile_adjustments.items():
                if trait in adapted_profile:
                    adapted_profile[trait] = np.clip(adapted_profile[trait] + adjustment, 0.0, 1.0)
            
            # Create adapted persona
            adapted_persona = VoicePersonaConfig(
                name=persona.name,
                description=persona.description,
                pitch=persona.pitch,
                rate=persona.rate,
                volume=persona.volume,
                tone=persona.tone,
                accent=persona.accent,
                emotion_modulation=persona.emotion_modulation,
                breathing_style=persona.breathing_style,
                speech_patterns=persona.speech_patterns.copy(),
                psychological_profile=adapted_profile
            )
            
            return adapted_persona
            
        except Exception as e:
            self.logger.error(f"Error adapting psychological profile: {e}")
            return persona


class AdaptationEngine:
    """Engine for managing voice adaptations."""
    
    def __init__(self, 
                 config: FrameworkConfig,
                 audit_logger: Optional[AuditLogger] = None):
        """
        Initialize the adaptation engine.
        
        Args:
            config: Framework configuration
            audit_logger: Audit logger instance
        """
        self.config = config
        self.audit_logger = audit_logger
        self.logger = logging.getLogger("adaptation_engine")
        
        # Voice adapter
        self.voice_adapter = VoiceAdapter(config)
        
        # Adaptation rules
        self.adaptation_rules: Dict[str, AdaptationRule] = {}
        
        # Adaptation history
        self.adaptation_history: List[AdaptationResult] = []
        
        # Event queue
        self.event_queue: List[AdaptationEvent] = []
        
        # Configuration
        self.adaptation_enabled = config.get('voice.adaptation.enabled', True)
        self.max_adaptations_per_minute = config.get('voice.adaptation.max_per_minute', 10)
        self.adaptation_confidence_threshold = config.get('voice.adaptation.confidence_threshold', 0.7)
        
        # Statistics
        self.stats = {
            'total_adaptations': 0,
            'successful_adaptations': 0,
            'failed_adaptations': 0,
            'adaptations_by_type': {},
            'average_confidence': 0.0
        }
        
        # Load default rules
        self._load_default_rules()
    
    def _load_default_rules(self) -> None:
        """Load default adaptation rules."""
        # Emotion-based adaptation rules
        emotion_rules = [
            AdaptationRule(
                rule_id="emotion_stress_high",
                name="High Stress Adaptation",
                description="Adapt voice when participant shows high stress",
                adaptation_type=AdaptationType.TONE,
                trigger=AdaptationTrigger.STRESS_LEVEL,
                conditions={
                    'stress_level': {'operator': '>', 'value': 0.7}
                },
                adjustments={
                    'tone': 'concerned',
                    'emotion_modulation': 0.3,
                    'rate': -0.2
                },
                priority=8
            ),
            AdaptationRule(
                rule_id="emotion_fear_response",
                name="Fear Response Adaptation",
                description="Adapt voice when participant shows fear",
                adaptation_type=AdaptationType.EMOTION,
                trigger=AdaptationTrigger.EMOTION_CHANGE,
                conditions={
                    'emotion': {'operator': '==', 'value': 'fearful'}
                },
                adjustments={
                    'tone': 'reassuring',
                    'emotion_modulation': 0.4,
                    'volume': -0.1
                },
                priority=7
            ),
            AdaptationRule(
                rule_id="emotion_anger_response",
                name="Anger Response Adaptation",
                description="Adapt voice when participant shows anger",
                adaptation_type=AdaptationType.TONE,
                trigger=AdaptationTrigger.EMOTION_CHANGE,
                conditions={
                    'emotion': {'operator': '==', 'value': 'angry'}
                },
                adjustments={
                    'tone': 'calm',
                    'emotion_modulation': 0.2,
                    'rate': -0.1
                },
                priority=7
            )
        ]
        
        # Objective-based adaptation rules
        objective_rules = [
            AdaptationRule(
                rule_id="objective_high_priority",
                name="High Priority Objective Adaptation",
                description="Adapt voice for high priority objectives",
                adaptation_type=AdaptationType.PERSONALITY,
                trigger=AdaptationTrigger.OBJECTIVE_PROGRESS,
                conditions={
                    'priority': {'operator': '>', 'value': 7},
                    'progress': {'operator': '<', 'value': 0.5}
                },
                adjustments={
                    'psychological_profile': {
                        'authority_level': 0.2,
                        'confidence_level': 0.1
                    }
                },
                priority=6
            ),
            AdaptationRule(
                rule_id="objective_near_completion",
                name="Near Completion Adaptation",
                description="Adapt voice when objectives are near completion",
                adaptation_type=AdaptationType.EMOTION,
                trigger=AdaptationTrigger.OBJECTIVE_PROGRESS,
                conditions={
                    'progress': {'operator': '>', 'value': 0.8}
                },
                adjustments={
                    'tone': 'confident',
                    'emotion_modulation': 0.1,
                    'rate': 0.1
                },
                priority=5
            )
        ]
        
        # Time-based adaptation rules
        time_rules = [
            AdaptationRule(
                rule_id="time_urgency_increase",
                name="Time Urgency Adaptation",
                description="Increase urgency over time",
                adaptation_type=AdaptationType.RATE,
                trigger=AdaptationTrigger.TIME_ELAPSED,
                conditions={
                    'elapsed_minutes': {'operator': '>', 'value': 5}
                },
                adjustments={
                    'rate': 0.1,
                    'volume': 0.1
                },
                priority=4
            )
        ]
        
        # Add all rules
        for rule in emotion_rules + objective_rules + time_rules:
            self.adaptation_rules[rule.rule_id] = rule
    
    async def process_event(self, event: AdaptationEvent) -> Optional[AdaptationResult]:
        """
        Process an adaptation event.
        
        Args:
            event: Adaptation event to process
            
        Returns:
            Adaptation result or None if no adaptation was made
        """
        try:
            if not self.adaptation_enabled:
                return None
            
            # Add to event queue
            self.event_queue.append(event)
            
            # Find matching rules
            matching_rules = self._find_matching_rules(event)
            
            if not matching_rules:
                return None
            
            # Sort by priority (highest first)
            matching_rules.sort(key=lambda x: x.priority, reverse=True)
            
            # Apply highest priority rule
            rule = matching_rules[0]
            
            # Apply adaptation
            result = await self._apply_adaptation_rule(rule, event)
            
            if result:
                self.stats['total_adaptations'] += 1
                
                if result.confidence >= self.adaptation_confidence_threshold:
                    self.stats['successful_adaptations'] += 1
                else:
                    self.stats['failed_adaptations'] += 1
                
                # Update adaptation type statistics
                adaptation_type = rule.adaptation_type.value
                self.stats['adaptations_by_type'][adaptation_type] = self.stats['adaptations_by_type'].get(adaptation_type, 0) + 1
                
                # Update average confidence
                total = self.stats['total_adaptations']
                current_avg = self.stats['average_confidence']
                self.stats['average_confidence'] = (current_avg * (total - 1) + result.confidence) / total
                
                # Log adaptation
                if self.audit_logger:
                    self.audit_logger.audit(
                        event_type=AuditEventType.SYSTEM_EVENT,
                        action="voice_adaptation_applied",
                        details={
                            'adaptation_id': result.adaptation_id,
                            'rule_id': rule.rule_id,
                            'trigger': event.trigger.value,
                            'confidence': result.confidence
                        },
                        security_level=SecurityLevel.LOW
                    )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing adaptation event: {e}")
            return None
    
    def _find_matching_rules(self, event: AdaptationEvent) -> List[AdaptationRule]:
        """Find rules that match the event."""
        matching_rules = []
        
        for rule in self.adaptation_rules.values():
            if not rule.enabled:
                continue
            
            if rule.trigger != event.trigger:
                continue
            
            # Check conditions
            if self._evaluate_conditions(rule.conditions, event.data):
                matching_rules.append(rule)
        
        return matching_rules
    
    def _evaluate_conditions(self,
                            conditions: Dict[str, Any],
                            event_data: Dict[str, Any]) -> bool:
        """Evaluate rule conditions against event data."""
        try:
            for field, condition in conditions.items():
                if field not in event_data:
                    return False
                
                operator = condition.get('operator')
                value = condition.get('value')
                event_value = event_data[field]
                
                if operator == '==':
                    if event_value != value:
                        return False
                elif operator == '!=':
                    if event_value == value:
                        return False
                elif operator == '>':
                    if not (event_value > value):
                        return False
                elif operator == '<':
                    if not (event_value < value):
                        return False
                elif operator == '>=':
                    if not (event_value >= value):
                        return False
                elif operator == '<=':
                    if not (event_value <= value):
                        return False
                elif operator == 'in':
                    if event_value not in value:
                        return False
                elif operator == 'not_in':
                    if event_value in value:
                        return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error evaluating conditions: {e}")
            return False
    
    async def _apply_adaptation_rule(self,
                                    rule: AdaptationRule,
                                    event: AdaptationEvent) -> Optional[AdaptationResult]:
        """Apply an adaptation rule to create an adaptation result."""
        try:
            # Get current persona from event data
            current_persona = event.data.get('persona')
            if not current_persona:
                return None
            
            # Apply adaptations based on type
            adapted_persona = current_persona
            adjustments_applied = {}
            
            if rule.adaptation_type == AdaptationType.PITCH and 'pitch' in rule.adjustments:
                adapted_persona = self.voice_adapter.adapt_pitch(
                    adapted_persona, rule.adjustments['pitch']
                )
                adjustments_applied['pitch'] = rule.adjustments['pitch']
            
            elif rule.adaptation_type == AdaptationType.RATE and 'rate' in rule.adjustments:
                adapted_persona = self.voice_adapter.adapt_rate(
                    adapted_persona, rule.adjustments['rate']
                )
                adjustments_applied['rate'] = rule.adjustments['rate']
            
            elif rule.adaptation_type == AdaptationType.VOLUME and 'volume' in rule.adjustments:
                adapted_persona = self.voice_adapter.adapt_volume(
                    adapted_persona, rule.adjustments['volume']
                )
                adjustments_applied['volume'] = rule.adjustments['volume']
            
            elif rule.adaptation_type == AdaptationType.TONE and 'tone' in rule.adjustments:
                adapted_persona = self.voice_adapter.adapt_tone(
                    adapted_persona, rule.adjustments['tone']
                )
                adjustments_applied['tone'] = rule.adjustments['tone']
            
            elif rule.adaptation_type == AdaptationType.EMOTION and 'emotion_modulation' in rule.adjustments:
                adapted_persona = self.voice_adapter.adapt_emotion(
                    adapted_persona, rule.adjustments['emotion_modulation']
                )
                adjustments_applied['emotion_modulation'] = rule.adjustments['emotion_modulation']
            
            elif rule.adaptation_type == AdaptationType.PERSONALITY and 'psychological_profile' in rule.adjustments:
                adapted_persona = self.voice_adapter.adapt_psychological_profile(
                    adapted_persona, rule.adjustments['psychological_profile']
                )
                adjustments_applied['psychological_profile'] = rule.adjustments['psychological_profile']
            
            # Calculate confidence based on priority and conditions
            confidence = min(rule.priority / 10.0, 0.9)
            
            # Create adaptation result
            result = AdaptationResult(
                adaptation_id=str(uuid.uuid4()),
                rule_id=rule.rule_id,
                original_persona=current_persona,
                adapted_persona=adapted_persona,
                adjustments_applied=adjustments_applied,
                confidence=confidence
            )
            
            # Add to history
            self.adaptation_history.append(result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error applying adaptation rule: {e}")
            return None
    
    def add_adaptation_rule(self, rule: AdaptationRule) -> None:
        """
        Add an adaptation rule.
        
        Args:
            rule: Adaptation rule to add
        """
        self.adaptation_rules[rule.rule_id] = rule
        
        if self.audit_logger:
            self.audit_logger.audit(
                event_type=AuditEventType.SYSTEM_EVENT,
                action="adaptation_rule_added",
                details={'rule_id': rule.rule_id, 'trigger': rule.trigger.value},
                security_level=SecurityLevel.LOW
            )
        
        self.logger.info(f"Adaptation rule added: {rule.rule_id}")
    
    def remove_adaptation_rule(self, rule_id: str) -> bool:
        """
        Remove an adaptation rule.
        
        Args:
            rule_id: ID of the rule to remove
            
        Returns:
            True if removed, False if not found
        """
        if rule_id in self.adaptation_rules:
            del self.adaptation_rules[rule_id]
            
            if self.audit_logger:
                self.audit_logger.audit(
                    event_type=AuditEventType.SYSTEM_EVENT,
                    action="adaptation_rule_removed",
                    details={'rule_id': rule_id},
                    security_level=SecurityLevel.LOW
                )
            
            self.logger.info(f"Adaptation rule removed: {rule_id}")
            return True
        
        return False
    
    def get_adaptation_rule(self, rule_id: str) -> Optional[AdaptationRule]:
        """
        Get an adaptation rule by ID.
        
        Args:
            rule_id: ID of the rule
            
        Returns:
            Adaptation rule or None if not found
        """
        return self.adaptation_rules.get(rule_id)
    
    def get_adaptation_rules(self) -> List[AdaptationRule]:
        """
        Get all adaptation rules.
        
        Returns:
            List of adaptation rules
        """
        return list(self.adaptation_rules.values())
    
    def get_adaptation_history(self, limit: Optional[int] = None) -> List[AdaptationResult]:
        """
        Get adaptation history.
        
        Args:
            limit: Maximum number of results to return
            
        Returns:
            List of adaptation results
        """
        if limit:
            return self.adaptation_history[-limit:]
        return self.adaptation_history.copy()
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get adaptation statistics.
        
        Returns:
            Dictionary containing statistics
        """
        return {
            'total_adaptations': self.stats['total_adaptations'],
            'successful_adaptations': self.stats['successful_adaptations'],
            'failed_adaptations': self.stats['failed_adaptations'],
            'success_rate': (
                self.stats['successful_adaptations'] / max(self.stats['total_adaptations'], 1)
            ),
            'adaptations_by_type': self.stats['adaptations_by_type'],
            'average_confidence': self.stats['average_confidence'],
            'total_rules': len(self.adaptation_rules),
            'enabled_rules': len([r for r in self.adaptation_rules.values() if r.enabled])
        }
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        self.event_queue.clear()
        self.logger.info("Adaptation engine cleanup complete")


# Global adaptation engine instance
_global_adaptation_engine: Optional[AdaptationEngine] = None


def get_adaptation_engine() -> Optional[AdaptationEngine]:
    """
    Get the global adaptation engine instance.
    
    Returns:
        Global AdaptationEngine instance or None if not initialized
    """
    return _global_adaptation_engine


def initialize_adaptation_engine(config: FrameworkConfig,
                                audit_logger: Optional[AuditLogger] = None) -> AdaptationEngine:
    """
    Initialize the global adaptation engine.
    
    Args:
        config: Framework configuration
        audit_logger: Audit logger instance
        
    Returns:
        Initialized AdaptationEngine instance
    """
    global _global_adaptation_engine
    _global_adaptation_engine = AdaptationEngine(config, audit_logger)
    return _global_adaptation_engine


def shutdown_adaptation_engine() -> None:
    """Shutdown the global adaptation engine."""
    global _global_adaptation_engine
    if _global_adaptation_engine:
        asyncio.create_task(_global_adaptation_engine.cleanup())
        _global_adaptation_engine = None