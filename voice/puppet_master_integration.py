"""
ATS MAFIA Framework Puppet Master Voice Integration

This module provides specialized voice integration for the Puppet Master profile.
Includes advanced voice manipulation, vishing simulation, and psychological profiling.
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

from .core import VoicePersonaConfig, AudioSegment, AudioFormat
from .integration import get_voice_system_manager
from .conversation import DialogueStrategy, ScenarioType, ConversationObjective
from .adaptation import AdaptationEngine, AdaptationEvent, AdaptationTrigger
from .analysis import VoiceAnalysisManager
from .ethics import EthicsSafeguards, InteractionType, ScopeType
from ..config.settings import FrameworkConfig
from ..core.logging import AuditLogger, AuditEventType, SecurityLevel


class PuppetMasterPersona(Enum):
    """Puppet Master specific voice personas."""
    NEUTRAL = "neutral"
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    AUTHORITATIVE = "authoritative"
    CONCERNED = "concerned"
    URGENT = "urgent"
    CALM = "calm"
    SUSPICIOUS = "suspicious"
    IT_SUPPORT = "it_support"
    BANK_VERIFICATION = "bank_verification"
    SURVEY_CONDUCTOR = "survey_conductor"
    CUSTOMER_SERVICE = "customer_service"
    SALES_REPRESENTATIVE = "sales_representative"


class VishingScenario(Enum):
    """Vishing scenario types."""
    IT_SUPPORT = "it_support"
    BANK_VERIFICATION = "bank_verification"
    SURVEY = "survey"
    CUSTOMER_SERVICE = "customer_service"
    SALES = "sales"
    GENERAL = "general"


@dataclass
class PuppetMasterConfig:
    """Configuration for Puppet Master voice integration."""
    enable_voice_manipulation: bool = True
    enable_psychological_profiling: bool = True
    enable_real_time_adaptation: bool = True
    enable_vishing_simulation: bool = True
    enable_ethical_safeguards: bool = True
    max_conversation_duration: int = 30  # minutes
    max_objectives: int = 5
    auto_persona_switching: bool = True
    emotion_response_enabled: bool = True
    stress_detection_enabled: bool = True
    strategy_adaptation_enabled: bool = True
    compliance_monitoring: bool = True
    audit_logging: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'enable_voice_manipulation': self.enable_voice_manipulation,
            'enable_psychological_profiling': self.enable_psychological_profiling,
            'enable_real_time_adaptation': self.enable_real_time_adaptation,
            'enable_vishing_simulation': self.enable_vishing_simulation,
            'enable_ethical_safeguards': self.enable_ethical_safeguards,
            'max_conversation_duration': self.max_conversation_duration,
            'max_objectives': self.max_objectives,
            'auto_persona_switching': self.auto_persona_switching,
            'emotion_response_enabled': self.emotion_response_enabled,
            'stress_detection_enabled': self.stress_detection_enabled,
            'strategy_adaptation_enabled': self.strategy_adaptation_enabled,
            'compliance_monitoring': self.compliance_monitoring,
            'audit_logging': self.audit_logging
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PuppetMasterConfig':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class VishingScenarioConfig:
    """Configuration for vishing scenarios."""
    scenario_id: str
    name: str
    description: str
    persona: PuppetMasterPersona
    strategy: DialogueStrategy
    objectives: List[ConversationObjective]
    script_templates: List[str]
    compliance_rules: List[str]
    success_criteria: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'scenario_id': self.scenario_id,
            'name': self.name,
            'description': self.description,
            'persona': self.persona.value,
            'strategy': self.strategy.value,
            'objectives': [obj.to_dict() for obj in self.objectives],
            'script_templates': self.script_templates,
            'compliance_rules': self.compliance_rules,
            'success_criteria': self.success_criteria
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VishingScenarioConfig':
        """Create from dictionary."""
        return cls(
            scenario_id=data['scenario_id'],
            name=data['name'],
            description=data['description'],
            persona=PuppetMasterPersona(data['persona']),
            strategy=DialogueStrategy(data['strategy']),
            objectives=[ConversationObjective.from_dict(obj) for obj in data['objectives']],
            script_templates=data['script_templates'],
            compliance_rules=data['compliance_rules'],
            success_criteria=data['success_criteria']
        )


class PuppetMasterVoiceIntegration:
    """
    Voice integration for the Puppet Master profile.
    
    Provides advanced voice manipulation and vishing simulation capabilities.
    """
    
    def __init__(self, 
                 config: FrameworkConfig,
                 audit_logger: Optional[AuditLogger] = None):
        """
        Initialize the Puppet Master voice integration.
        
        Args:
            config: Framework configuration
            audit_logger: Audit logger instance
        """
        self.config = config
        self.audit_logger = audit_logger
        self.logger = logging.getLogger("puppet_master_voice_integration")
        
        # Puppet Master configuration
        self.pm_config = PuppetMasterConfig(
            enable_voice_manipulation=config.get('voice.puppet_master.enable_voice_manipulation', True),
            enable_psychological_profiling=config.get('voice.puppet_master.enable_psychological_profiling', True),
            enable_real_time_adaptation=config.get('voice.puppet_master.enable_real_time_adaptation', True),
            enable_vishing_simulation=config.get('voice.puppet_master.enable_vishing_simulation', True),
            enable_ethical_safeguards=config.get('voice.puppet_master.enable_ethical_safeguards', True),
            max_conversation_duration=config.get('voice.puppet_master.max_conversation_duration', 30),
            max_objectives=config.get('voice.puppet_master.max_objectives', 5),
            auto_persona_switching=config.get('voice.puppet_master.auto_persona_switching', True),
            emotion_response_enabled=config.get('voice.puppet_master.emotion_response_enabled', True),
            stress_detection_enabled=config.get('voice.puppet_master.stress_detection_enabled', True),
            strategy_adaptation_enabled=config.get('voice.puppet_master.strategy_adaptation_enabled', True),
            compliance_monitoring=config.get('voice.puppet_master.compliance_monitoring', True),
            audit_logging=config.get('voice.puppet_master.audit_logging', True)
        )
        
        # Voice system manager
        self.voice_system_manager = get_voice_system_manager()
        
        # Puppet Master personas
        self.pm_personas: Dict[str, VoicePersonaConfig] = {}
        
        # Vishing scenarios
        self.vishing_scenarios: Dict[str, VishingScenarioConfig] = {}
        
        # Active sessions
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        
        # Performance metrics
        self.metrics = {
            'total_sessions': 0,
            'successful_sessions': 0,
            'failed_sessions': 0,
            'average_duration': 0.0,
            'persona_switches': 0,
            'adaptations_applied': 0,
            'compliance_violations': 0,
            'objectives_completed': 0
        }
        
        # Load Puppet Master personas
        self._load_pm_personas()
        
        # Load vishing scenarios
        self._load_vishing_scenarios()
    
    def _load_pm_personas(self) -> None:
        """Load Puppet Master specific personas."""
        # IT Support persona
        self.pm_personas[PuppetMasterPersona.IT_SUPPORT.value] = VoicePersonaConfig(
            name="IT Support",
            description="Technical support professional persona",
            pitch=1.0,
            rate=0.9,
            volume=0.8,
            tone="professional",
            accent="neutral",
            emotion_modulation=0.3,
            breathing_style="natural",
            speech_patterns={
                'technical_terms': True,
                'explanatory_style': True,
                'problem_solving_focus': True
            },
            psychological_profile={
                'trust_level': 0.8,
                'confidence_level': 0.9,
                'authority_level': 0.7,
                'friendliness_level': 0.6,
                'technical_credibility': 0.9
            }
        )
        
        # Bank Verification persona
        self.pm_personas[PuppetMasterPersona.BANK_VERIFICATION.value] = VoicePersonaConfig(
            name="Bank Verification",
            description="Bank verification specialist persona",
            pitch=1.1,
            rate=0.8,
            volume=0.7,
            tone="concerned",
            accent="neutral",
            emotion_modulation=0.4,
            breathing_style="measured",
            speech_patterns={
                'security_focused': True,
                'verification_style': True,
                'formal_language': True
            },
            psychological_profile={
                'trust_level': 0.9,
                'confidence_level': 0.8,
                'authority_level': 0.8,
                'friendliness_level': 0.5,
                'security_awareness': 0.9
            }
        )
        
        # Survey Conductor persona
        self.pm_personas[PuppetMasterPersona.SURVEY_CONDUCTOR.value] = VoicePersonaConfig(
            name="Survey Conductor",
            description="Survey researcher persona",
            pitch=1.0,
            rate=1.0,
            volume=0.8,
            tone="friendly",
            accent="neutral",
            emotion_modulation=0.5,
            breathing_style="natural",
            speech_patterns={
                'question_focused': True,
                'information_gathering': True,
                'neutral_stance': True
            },
            psychological_profile={
                'trust_level': 0.7,
                'confidence_level': 0.6,
                'authority_level': 0.4,
                'friendliness_level': 0.8,
                'research_orientation': 0.9
            }
        )
        
        # Customer Service persona
        self.pm_personas[PuppetMasterPersona.CUSTOMER_SERVICE.value] = VoicePersonaConfig(
            name="Customer Service",
            description="Customer service representative persona",
            pitch=1.1,
            rate=0.9,
            volume=0.8,
            tone="helpful",
            accent="neutral",
            emotion_modulation=0.6,
            breathing_style="natural",
            speech_patterns={
                'service_oriented': True,
                'problem_resolution': True,
                'polite_language': True
            },
            psychological_profile={
                'trust_level': 0.7,
                'confidence_level': 0.7,
                'authority_level': 0.5,
                'friendliness_level': 0.9,
                'service_orientation': 0.9
            }
        )
        
        # Sales Representative persona
        self.pm_personas[PuppetMasterPersona.SALES_REPRESENTATIVE.value] = VoicePersonaConfig(
            name="Sales Representative",
            description="Sales representative persona",
            pitch=1.0,
            rate=1.1,
            volume=0.9,
            tone="enthusiastic",
            accent="neutral",
            emotion_modulation=0.7,
            breathing_style="energetic",
            speech_patterns={
                'persuasion_focused': True,
                'benefit_oriented': True,
                'closing_techniques': True
            },
            psychological_profile={
                'trust_level': 0.6,
                'confidence_level': 0.8,
                'authority_level': 0.5,
                'friendliness_level': 0.8,
                'persuasion_skill': 0.9
            }
        )
    
    def _load_vishing_scenarios(self) -> None:
        """Load vishing scenarios."""
        # IT Support scenario
        self.vishing_scenarios[VishingScenario.IT_SUPPORT.value] = VishingScenarioConfig(
            scenario_id="it_support",
            name="IT Support Scam",
            description="Simulate IT support calling to verify security issues",
            persona=PuppetMasterPersona.IT_SUPPORT,
            strategy=DialogueStrategy.AUTHORITY,
            objectives=[
                ConversationObjective(
                    objective_id="verify_system",
                    name="Verify System Information",
                    description="Get participant to verify system information",
                    priority=8,
                    completion_threshold=0.8
                ),
                ConversationObjective(
                    objective_id="gain_access",
                    name="Gain Remote Access",
                    description="Convince participant to allow remote access",
                    priority=9,
                    completion_threshold=0.9
                )
            ],
            script_templates=[
                "Hello, I'm calling from IT support. We've detected suspicious activity on your account.",
                "We need to verify your system information to secure your account.",
                "Can you please tell me what operating system you're using?",
                "I need to connect to your computer to run a security scan."
            ],
            compliance_rules=["training_environment_only", "no_real_access", "disclosure_required"],
            success_criteria={
                'information_gathered': 0.8,
                'trust_established': 0.7,
                'compliance_score': 0.95
            }
        )
        
        # Bank Verification scenario
        self.vishing_scenarios[VishingScenario.BANK_VERIFICATION.value] = VishingScenarioConfig(
            scenario_id="bank_verification",
            name="Bank Verification Scam",
            description="Simulate bank calling to verify account information",
            persona=PuppetMasterPersona.BANK_VERIFICATION,
            strategy=DialogueStrategy.AUTHORITY,
            objectives=[
                ConversationObjective(
                    objective_id="verify_account",
                    name="Verify Account Information",
                    description="Get participant to verify account details",
                    priority=8,
                    completion_threshold=0.8
                ),
                ConversationObjective(
                    objective_id="security_code",
                    name="Get Security Code",
                    description="Obtain security verification code",
                    priority=9,
                    completion_threshold=0.9
                )
            ],
            script_templates=[
                "Hello, I'm calling from {bank_name} security department.",
                "We've detected unusual activity on your account and need to verify some information.",
                "Can you please confirm your account number?",
                "We've sent a verification code to your phone. Can you read it back to me?"
            ],
            compliance_rules=["training_environment_only", "no_real_accounts", "disclosure_required"],
            success_criteria={
                'information_gathered': 0.8,
                'trust_established': 0.7,
                'compliance_score': 0.95
            }
        )
        
        # Survey scenario
        self.vishing_scenarios[VishingScenario.SURVEY.value] = VishingScenarioConfig(
            scenario_id="survey",
            name="Information Gathering Survey",
            description="Simulate survey to gather personal information",
            persona=PuppetMasterPersona.SURVEY_CONDUCTOR,
            strategy=DialogueStrategy.BUILDING_RAPPORT,
            objectives=[
                ConversationObjective(
                    objective_id="personal_info",
                    name="Gather Personal Information",
                    description="Collect personal details through survey",
                    priority=7,
                    completion_threshold=0.7
                ),
                ConversationObjective(
                    objective_id="behavior_patterns",
                    name="Identify Behavior Patterns",
                    description="Understand participant behaviors and preferences",
                    priority=6,
                    completion_threshold=0.6
                )
            ],
            script_templates=[
                "Hello, I'm conducting a survey about {survey_topic}.",
                "This will only take a few minutes of your time.",
                "Can I ask you some questions about your {survey_topic} habits?",
                "For our records, could you please provide some basic information?"
            ],
            compliance_rules=["training_environment_only", "no_real_data_collection", "disclosure_required"],
            success_criteria={
                'information_gathered': 0.7,
                'trust_established': 0.6,
                'compliance_score': 0.95
            }
        )
    
    async def start_vishing_session(self,
                                  participant_id: str,
                                  participant_info: Dict[str, Any],
                                  scenario_type: VishingScenario,
                                  custom_parameters: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Start a vishing session.
        
        Args:
            participant_id: ID of the participant
            participant_info: Information about the participant
            scenario_type: Type of vishing scenario
            custom_parameters: Custom parameters for the session
            
        Returns:
            Session ID or None if error
        """
        try:
            if not self.voice_system_manager:
                self.logger.error("Voice system manager not available")
                return None
            
            # Get scenario configuration
            scenario_config = self.vishing_scenarios.get(scenario_type.value)
            if not scenario_config:
                self.logger.error(f"Scenario configuration not found: {scenario_type.value}")
                return None
            
            # Create session
            session_id = str(uuid.uuid4())
            session_data = {
                'session_id': session_id,
                'participant_id': participant_id,
                'participant_info': participant_info,
                'scenario_type': scenario_type.value,
                'scenario_config': scenario_config,
                'start_time': datetime.now(timezone.utc),
                'custom_parameters': custom_parameters or {},
                'objectives_progress': {obj.objective_id: 0.0 for obj in scenario_config.objectives},
                'persona_switches': 0,
                'adaptations_applied': 0,
                'compliance_violations': 0
            }
            
            # Store session
            self.active_sessions[session_id] = session_data
            
            # Start ethics monitoring
            if self.pm_config.enable_ethical_safeguards and self.voice_system_manager.ethics_safeguards:
                await self.voice_system_manager.ethics_safeguards.start_monitoring(
                    session_id=session_id,
                    interaction_id=str(uuid.uuid4()),
                    interaction_type=InteractionType.TRAINING,
                    scope_id=ScopeType.CONTROLLED.value,
                    scope_type=ScopeType.CONTROLLED,
                    participant_id=participant_id,
                    metadata={
                        'scenario_type': scenario_type.value,
                        'puppet_master_session': True
                    }
                )
            
            # Start conversation
            conversation_id = await self.voice_system_manager.start_conversation(
                participant_id=participant_id,
                participant_info=participant_info,
                scenario_type=ScenarioType.VISHING_SIMULATION,
                strategy=scenario_config.strategy,
                objectives=scenario_config.objectives
            )
            
            if conversation_id:
                session_data['conversation_id'] = conversation_id
                
                # Set initial persona
                persona_name = scenario_config.persona.value
                if self.voice_system_manager.voice_engine:
                    self.voice_system_manager.voice_engine.set_persona(persona_name)
                
                # Update metrics
                self.metrics['total_sessions'] += 1
                
                # Log to audit
                if self.audit_logger:
                    self.audit_logger.audit(
                        event_type=AuditEventType.SYSTEM_EVENT,
                        action="puppet_master_vishing_session_started",
                        details={
                            'session_id': session_id,
                            'participant_id': participant_id,
                            'scenario_type': scenario_type.value,
                            'conversation_id': conversation_id
                        },
                        security_level=SecurityLevel.HIGH
                    )
                
                self.logger.info(f"Started vishing session {session_id} for participant {participant_id}")
                return session_id
            else:
                # Clean up session if conversation failed
                del self.active_sessions[session_id]
                return None
                
        except Exception as e:
            self.logger.error(f"Error starting vishing session: {e}")
            return None
    
    async def process_participant_input(self,
                                      session_id: str,
                                      input_text: str,
                                      audio_data: Optional[AudioSegment] = None) -> Optional[str]:
        """
        Process participant input and generate response.
        
        Args:
            session_id: ID of the session
            input_text: Text input from participant
            audio_data: Audio data from participant
            
        Returns:
            Generated response or None if error
        """
        try:
            if session_id not in self.active_sessions:
                self.logger.error(f"Session not found: {session_id}")
                return None
            
            session_data = self.active_sessions[session_id]
            conversation_id = session_data['conversation_id']
            
            # Analyze participant input if audio provided
            analysis_results = {}
            if audio_data and self.pm_config.enable_psychological_profiling:
                analysis_results = await self.voice_system_manager.analyze_voice(
                    audio=audio_data,
                    text=input_text,
                    analysis_types=['emotion', 'stress', 'psychological']
                )
                
                # Store analysis results
                session_data['last_analysis'] = analysis_results
                
                # Trigger adaptation if enabled
                if self.pm_config.enable_real_time_adaptation:
                    await self._trigger_adaptation(session_id, analysis_results)
            
            # Add participant message to conversation
            if self.voice_system_manager.conversation_manager:
                await self.voice_system_manager.conversation_manager.add_message(
                    conversation_id=conversation_id,
                    turn='participant',
                    content=input_text
                )
            
            # Generate agent response
            response = await self.voice_system_manager.conversation_manager.generate_response(
                conversation_id=conversation_id
            )
            
            if response:
                # Add agent message to conversation
                await self.voice_system_manager.conversation_manager.add_message(
                    conversation_id=conversation_id,
                    turn='agent',
                    content=response
                )
                
                # Update session
                session_data['last_response'] = response
                session_data['last_activity'] = datetime.now(timezone.utc)
                
                # Check objectives progress
                await self._update_objectives_progress(session_id, input_text, response)
                
                # Log interaction
                if self.audit_logger:
                    self.audit_logger.audit(
                        event_type=AuditEventType.SYSTEM_EVENT,
                        action="puppet_master_interaction_processed",
                        details={
                            'session_id': session_id,
                            'participant_input': input_text,
                            'agent_response': response,
                            'analysis_results': analysis_results
                        },
                        security_level=SecurityLevel.HIGH
                    )
                
                return response
            else:
                self.logger.error("Failed to generate response")
                return None
                
        except Exception as e:
            self.logger.error(f"Error processing participant input: {e}")
            return None
    
    async def synthesize_response(self,
                                 session_id: str,
                                 text: str,
                                 persona_override: Optional[str] = None) -> Optional[AudioSegment]:
        """
        Synthesize response audio.
        
        Args:
            session_id: ID of the session
            text: Text to synthesize
            persona_override: Override persona for this response
            
        Returns:
            Audio segment or None if error
        """
        try:
            if session_id not in self.active_sessions:
                self.logger.error(f"Session not found: {session_id}")
                return None
            
            session_data = self.active_sessions[session_id]
            scenario_config = session_data['scenario_config']
            
            # Determine persona
            persona_name = persona_override or scenario_config.persona.value
            
            # Synthesize speech
            audio_segment = await self.voice_system_manager.synthesize_speech(
                text=text,
                persona=persona_name
            )
            
            if audio_segment:
                session_data['last_synthesis'] = {
                    'text': text,
                    'persona': persona_name,
                    'duration': audio_segment.duration,
                    'timestamp': datetime.now(timezone.utc)
                }
                
                return audio_segment
            else:
                self.logger.error("Failed to synthesize speech")
                return None
                
        except Exception as e:
            self.logger.error(f"Error synthesizing response: {e}")
            return None
    
    async def _trigger_adaptation(self, session_id: str, analysis_results: Dict[str, Any]) -> None:
        """Trigger voice adaptation based on analysis results."""
        try:
            if not self.voice_system_manager.adaptation_engine:
                return
            
            session_data = self.active_sessions[session_id]
            
            # Check for emotion-based adaptation
            if 'emotion' in analysis_results:
                emotion_data = analysis_results['emotion']
                event = AdaptationEvent(
                    event_id=str(uuid.uuid4()),
                    trigger=AdaptationTrigger.EMOTION_CHANGE,
                    data={
                        'emotion': emotion_data.get('emotion_type'),
                        'intensity': emotion_data.get('intensity'),
                        'persona': self.voice_system_manager.voice_engine.get_active_persona()
                    }
                )
                result = await self.voice_system_manager.adaptation_engine.process_event(event)
                if result:
                    session_data['adaptations_applied'] += 1
                    self.metrics['adaptations_applied'] += 1
            
            # Check for stress-based adaptation
            if 'stress' in analysis_results:
                stress_data = analysis_results['stress']
                event = AdaptationEvent(
                    event_id=str(uuid.uuid4()),
                    trigger=AdaptationTrigger.STRESS_LEVEL,
                    data={
                        'stress_level': stress_data.get('stress_value'),
                        'persona': self.voice_system_manager.voice_engine.get_active_persona()
                    }
                )
                result = await self.voice_system_manager.adaptation_engine.process_event(event)
                if result:
                    session_data['adaptations_applied'] += 1
                    self.metrics['adaptations_applied'] += 1
            
            # Check for persona switching
            if self.pm_config.auto_persona_switching:
                await self._evaluate_persona_switch(session_id, analysis_results)
                
        except Exception as e:
            self.logger.error(f"Error triggering adaptation: {e}")
    
    async def _evaluate_persona_switch(self, session_id: str, analysis_results: Dict[str, Any]) -> None:
        """Evaluate if persona switching is needed."""
        try:
            session_data = self.active_sessions[session_id]
            scenario_config = session_data['scenario_config']
            current_persona = scenario_config.persona
            
            # Simple logic for persona switching based on analysis
            switch_to_persona = None
            
            if 'emotion' in analysis_results:
                emotion_data = analysis_results['emotion']
                emotion_type = emotion_data.get('emotion_type')
                
                if emotion_type == 'fearful' and current_persona != PuppetMasterPersona.CONCERNED:
                    switch_to_persona = PuppetMasterPersona.CONCERNED
                elif emotion_type == 'angry' and current_persona != PuppetMasterPersona.CALM:
                    switch_to_persona = PuppetMasterPersona.CALM
                elif emotion_type == 'happy' and current_persona != PuppetMasterPersona.FRIENDLY:
                    switch_to_persona = PuppetMasterPersona.FRIENDLY
            
            if switch_to_persona and self.voice_system_manager.voice_engine:
                # Switch persona
                self.voice_system_manager.voice_engine.set_persona(switch_to_persona.value)
                session_data['persona_switches'] += 1
                self.metrics['persona_switches'] += 1
                
                # Update scenario config
                session_data['scenario_config'].persona = switch_to_persona
                
                self.logger.info(f"Switched persona to {switch_to_persona.value} for session {session_id}")
                
        except Exception as e:
            self.logger.error(f"Error evaluating persona switch: {e}")
    
    async def _update_objectives_progress(self, session_id: str, participant_input: str, agent_response: str) -> None:
        """Update objectives progress based on conversation."""
        try:
            session_data = self.active_sessions[session_id]
            scenario_config = session_data['scenario_config']
            objectives_progress = session_data['objectives_progress']
            
            # Simple progress calculation based on keywords
            for objective in scenario_config.objectives:
                current_progress = objectives_progress[objective.objective_id]
                
                # Check for objective-related keywords
                if objective.objective_id == "verify_system":
                    if any(keyword in participant_input.lower() for keyword in ['windows', 'mac', 'computer', 'system']):
                        objectives_progress[objective.objective_id] = min(1.0, current_progress + 0.2)
                
                elif objective.objective_id == "gain_access":
                    if any(keyword in participant_input.lower() for keyword in ['yes', 'okay', 'sure', 'allow']):
                        objectives_progress[objective.objective_id] = min(1.0, current_progress + 0.3)
                
                elif objective.objective_id == "verify_account":
                    if any(keyword in participant_input.lower() for keyword in ['account', 'number', 'bank']):
                        objectives_progress[objective.objective_id] = min(1.0, current_progress + 0.2)
                
                elif objective.objective_id == "security_code":
                    if any(keyword in participant_input.lower() for keyword in ['code', 'verification', 'number']):
                        objectives_progress[objective.objective_id] = min(1.0, current_progress + 0.3)
                
                elif objective.objective_id == "personal_info":
                    if any(keyword in participant_input.lower() for keyword in ['name', 'email', 'phone', 'address']):
                        objectives_progress[objective.objective_id] = min(1.0, current_progress + 0.2)
            
            # Check for completed objectives
            completed_objectives = sum(1 for progress in objectives_progress.values() if progress >= objective.completion_threshold)
            session_data['completed_objectives'] = completed_objectives
            
            # Update metrics
            self.metrics['objectives_completed'] = max(self.metrics['objectives_completed'], completed_objectives)
            
        except Exception as e:
            self.logger.error(f"Error updating objectives progress: {e}")
    
    async def end_vishing_session(self, session_id: str) -> Dict[str, Any]:
        """
        End a vishing session.
        
        Args:
            session_id: ID of the session to end
            
        Returns:
            Session summary
        """
        try:
            if session_id not in self.active_sessions:
                self.logger.error(f"Session not found: {session_id}")
                return {}
            
            session_data = self.active_sessions[session_id]
            conversation_id = session_data['conversation_id']
            
            # Calculate session duration
            end_time = datetime.now(timezone.utc)
            duration = (end_time - session_data['start_time']).total_seconds()
            
            # End conversation
            if self.voice_system_manager.conversation_manager:
                await self.voice_system_manager.end_conversation(conversation_id)
            
            # End ethics monitoring
            if self.pm_config.enable_ethical_safeguards and self.voice_system_manager.ethics_safeguards:
                await self.voice_system_manager.ethics_safeguards.end_monitoring(session_id)
            
            # Create session summary
            summary = {
                'session_id': session_id,
                'participant_id': session_data['participant_id'],
                'scenario_type': session_data['scenario_type'],
                'duration_seconds': duration,
                'objectives_progress': session_data['objectives_progress'],
                'completed_objectives': session_data.get('completed_objectives', 0),
                'persona_switches': session_data['persona_switches'],
                'adaptations_applied': session_data['adaptations_applied'],
                'compliance_violations': session_data['compliance_violations'],
                'success_score': self._calculate_success_score(session_data)
            }
            
            # Update metrics
            self.metrics['successful_sessions'] += 1
            total_duration = self.metrics['average_duration'] * (self.metrics['successful_sessions'] - 1)
            self.metrics['average_duration'] = (total_duration + duration) / self.metrics['successful_sessions']
            
            # Remove session
            del self.active_sessions[session_id]
            
            # Log to audit
            if self.audit_logger:
                self.audit_logger.audit(
                    event_type=AuditEventType.SYSTEM_EVENT,
                    action="puppet_master_vishing_session_ended",
                    details=summary,
                    security_level=SecurityLevel.HIGH
                )
            
            self.logger.info(f"Ended vishing session {session_id}")
            return summary
            
        except Exception as e:
            self.logger.error(f"Error ending vishing session: {e}")
            return {}
    
    def _calculate_success_score(self, session_data: Dict[str, Any]) -> float:
        """Calculate success score for the session."""
        try:
            objectives_progress = session_data['objectives_progress']
            scenario_config = session_data['scenario_config']
            
            # Calculate objective completion score
            total_objectives = len(scenario_config.objectives)
            if total_objectives == 0:
                return 0.0
            
            completed_objectives = sum(
                1 for obj_id, progress in objectives_progress.items()
                if progress >= 0.8  # Consider 80% as completion
            )
            
            objective_score = completed_objectives / total_objectives
            
            # Calculate engagement score (based on duration and interactions)
            duration_score = min(1.0, session_data.get('duration_seconds', 0) / 300)  # 5 minutes max
            
            # Calculate adaptation effectiveness
            adaptation_score = min(1.0, session_data.get('adaptations_applied', 0) / 5)
            
            # Weighted average
            success_score = (
                objective_score * 0.6 +
                duration_score * 0.2 +
                adaptation_score * 0.2
            )
            
            return success_score
            
        except Exception as e:
            self.logger.error(f"Error calculating success score: {e}")
            return 0.0
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data."""
        return self.active_sessions.get(session_id)
    
    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """Get all active sessions."""
        return list(self.active_sessions.values())
    
    def get_available_scenarios(self) -> List[VishingScenarioConfig]:
        """Get available vishing scenarios."""
        return list(self.vishing_scenarios.values())
    
    def get_available_personas(self) -> List[VoicePersonaConfig]:
        """Get available Puppet Master personas."""
        return list(self.pm_personas.values())
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get Puppet Master metrics."""
        return {
            **self.metrics,
            'active_sessions': len(self.active_sessions),
            'available_scenarios': len(self.vishing_scenarios),
            'available_personas': len(self.pm_personas)
        }
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        try:
            # End all active sessions
            session_ids = list(self.active_sessions.keys())
            for session_id in session_ids:
                await self.end_vishing_session(session_id)
            
            self.logger.info("Puppet Master voice integration cleanup complete")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")


# Global Puppet Master voice integration instance
_global_puppet_master_integration: Optional[PuppetMasterVoiceIntegration] = None


def get_puppet_master_integration() -> Optional[PuppetMasterVoiceIntegration]:
    """
    Get the global Puppet Master voice integration instance.
    
    Returns:
        Global PuppetMasterVoiceIntegration instance or None if not initialized
    """
    return _global_puppet_master_integration


def initialize_puppet_master_integration(config: FrameworkConfig,
                                       audit_logger: Optional[AuditLogger] = None) -> PuppetMasterVoiceIntegration:
    """
    Initialize the global Puppet Master voice integration.
    
    Args:
        config: Framework configuration
        audit_logger: Audit logger instance
        
    Returns:
        Initialized PuppetMasterVoiceIntegration instance
    """
    global _global_puppet_master_integration
    _global_puppet_master_integration = PuppetMasterVoiceIntegration(config, audit_logger)
    return _global_puppet_master_integration


def shutdown_puppet_master_integration() -> None:
    """Shutdown the global Puppet Master voice integration."""
    global _global_puppet_master_integration
    if _global_puppet_master_integration:
        asyncio.create_task(_global_puppet_master_integration.cleanup())
        _global_puppet_master_integration = None