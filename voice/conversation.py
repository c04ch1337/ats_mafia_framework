"""
ATS MAFIA Framework Conversation Management System

This module provides conversation management capabilities for the ATS MAFIA framework.
Includes dialogue strategy, response generation, and conversation tracking.
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


class DialogueStrategy(Enum):
    """Dialogue strategies for conversations."""
    NEUTRAL = "neutral"
    FRIENDLY = "friendly"
    AUTHORITATIVE = "authoritative"
    INVESTIGATIVE = "investigative"
    PERSUASIVE = "persuasive"
    TECHNICAL = "technical"
    CASUAL = "casual"
    FORMAL = "formal"
    URGENT = "urgent"
    SUSPICIOUS = "suspicious"


class ScenarioType(Enum):
    """Types of conversation scenarios."""
    TRAINING = "training"
    TESTING = "testing"
    DEMONSTRATION = "demonstration"
    LIVE = "live"
    SIMULATION = "simulation"
    ASSESSMENT = "assessment"


class MessageType(Enum):
    """Types of messages in conversations."""
    TEXT = "text"
    AUDIO = "audio"
    SYSTEM = "system"
    METADATA = "metadata"


class MessagePriority(Enum):
    """Priority levels for messages."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class ConversationObjective:
    """Objective for a conversation."""
    objective_id: str
    name: str
    description: str
    priority: int  # 1-10
    completion_threshold: float  # 0.0-1.0
    current_progress: float = 0.0
    completed: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'objective_id': self.objective_id,
            'name': self.name,
            'description': self.description,
            'priority': self.priority,
            'completion_threshold': self.completion_threshold,
            'current_progress': self.current_progress,
            'completed': self.completed,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationObjective':
        """Create from dictionary."""
        return cls(
            objective_id=data['objective_id'],
            name=data['name'],
            description=data['description'],
            priority=data['priority'],
            completion_threshold=data['completion_threshold'],
            current_progress=data.get('current_progress', 0.0),
            completed=data.get('completed', False),
            created_at=datetime.fromisoformat(data['created_at'])
        )


@dataclass
class DialogueMessage:
    """Message in a conversation."""
    message_id: str
    turn: str  # 'agent' or 'participant'
    content: str
    message_type: MessageType
    priority: MessagePriority
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'message_id': self.message_id,
            'turn': self.turn,
            'content': self.content,
            'message_type': self.message_type.value,
            'priority': self.priority.value,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DialogueMessage':
        """Create from dictionary."""
        return cls(
            message_id=data['message_id'],
            turn=data['turn'],
            content=data['content'],
            message_type=MessageType(data['message_type']),
            priority=MessagePriority(data['priority']),
            timestamp=datetime.fromisoformat(data['timestamp']),
            metadata=data.get('metadata', {})
        )


@dataclass
class DialogueTurn:
    """Turn in a conversation."""
    turn_id: str
    turn_number: int
    turn_type: str  # 'agent' or 'participant'
    messages: List[DialogueMessage]
    start_time: datetime
    end_time: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'turn_id': self.turn_id,
            'turn_number': self.turn_number,
            'turn_type': self.turn_type,
            'messages': [msg.to_dict() for msg in self.messages],
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DialogueTurn':
        """Create from dictionary."""
        return cls(
            turn_id=data['turn_id'],
            turn_number=data['turn_number'],
            turn_type=data['turn_type'],
            messages=[DialogueMessage.from_dict(msg) for msg in data['messages']],
            start_time=datetime.fromisoformat(data['start_time']),
            end_time=datetime.fromisoformat(data['end_time']) if data.get('end_time') else None,
            metadata=data.get('metadata', {})
        )


@dataclass
class Conversation:
    """A conversation between agent and participant."""
    conversation_id: str
    participant_id: str
    participant_info: Dict[str, Any]
    scenario_type: ScenarioType
    strategy: DialogueStrategy
    objectives: List[ConversationObjective]
    turns: List[DialogueTurn]
    start_time: datetime
    end_time: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'conversation_id': self.conversation_id,
            'participant_id': self.participant_id,
            'participant_info': self.participant_info,
            'scenario_type': self.scenario_type.value,
            'strategy': self.strategy.value,
            'objectives': [obj.to_dict() for obj in self.objectives],
            'turns': [turn.to_dict() for turn in self.turns],
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Conversation':
        """Create from dictionary."""
        return cls(
            conversation_id=data['conversation_id'],
            participant_id=data['participant_id'],
            participant_info=data['participant_info'],
            scenario_type=ScenarioType(data['scenario_type']),
            strategy=DialogueStrategy(data['strategy']),
            objectives=[ConversationObjective.from_dict(obj) for obj in data['objectives']],
            turns=[DialogueTurn.from_dict(turn) for turn in data['turns']],
            start_time=datetime.fromisoformat(data['start_time']),
            end_time=datetime.fromisoformat(data['end_time']) if data.get('end_time') else None,
            metadata=data.get('metadata', {})
        )
    
    def get_duration(self) -> float:
        """Get conversation duration in seconds."""
        end_time = self.end_time or datetime.now(timezone.utc)
        return (end_time - self.start_time).total_seconds()
    
    def get_last_message(self) -> Optional[DialogueMessage]:
        """Get the last message in the conversation."""
        if not self.turns:
            return None
        
        last_turn = self.turns[-1]
        if not last_turn.messages:
            return None
        
        return last_turn.messages[-1]
    
    def get_turn_count(self) -> int:
        """Get the number of turns in the conversation."""
        return len(self.turns)
    
    def get_message_count(self) -> int:
        """Get the total number of messages in the conversation."""
        return sum(len(turn.messages) for turn in self.turns)


@dataclass
class ResponseTemplate:
    """Template for generating responses."""
    template_id: str
    name: str
    description: str
    strategy: DialogueStrategy
    template_text: str
    variables: List[str]
    conditions: Dict[str, Any]
    priority: int = 5
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'template_id': self.template_id,
            'name': self.name,
            'description': self.description,
            'strategy': self.strategy.value,
            'template_text': self.template_text,
            'variables': self.variables,
            'conditions': self.conditions,
            'priority': self.priority
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ResponseTemplate':
        """Create from dictionary."""
        return cls(
            template_id=data['template_id'],
            name=data['name'],
            description=data['description'],
            strategy=DialogueStrategy(data['strategy']),
            template_text=data['template_text'],
            variables=data['variables'],
            conditions=data['conditions'],
            priority=data.get('priority', 5)
        )


class DialogueStrategyEngine:
    """Engine for managing dialogue strategies and response generation."""
    
    def __init__(self, config: FrameworkConfig):
        """
        Initialize the dialogue strategy engine.
        
        Args:
            config: Framework configuration
        """
        self.config = config
        self.logger = logging.getLogger("dialogue_strategy_engine")
        
        # Response templates
        self.templates: Dict[str, ResponseTemplate] = {}
        
        # Load default templates
        self._load_default_templates()
    
    def _load_default_templates(self) -> None:
        """Load default response templates."""
        # Neutral strategy templates
        self.templates['neutral_greeting'] = ResponseTemplate(
            template_id='neutral_greeting',
            name='Neutral Greeting',
            description='Generic greeting for neutral conversations',
            strategy=DialogueStrategy.NEUTRAL,
            template_text='Hello, I\'m {agent_name}. How can I help you today?',
            variables=['agent_name'],
            conditions={'turn_number': 1, 'context': 'greeting'}
        )
        
        self.templates['neutral_followup'] = ResponseTemplate(
            template_id='neutral_followup',
            name='Neutral Follow-up',
            description='Generic follow-up question',
            strategy=DialogueStrategy.NEUTRAL,
            template_text='I understand. Can you tell me more about {topic}?',
            variables=['topic'],
            conditions={'turn_number': 2, 'context': 'followup'}
        )
        
        # Friendly strategy templates
        self.templates['friendly_greeting'] = ResponseTemplate(
            template_id='friendly_greeting',
            name='Friendly Greeting',
            description='Warm greeting for friendly conversations',
            strategy=DialogueStrategy.FRIENDLY,
            template_text='Hi there! I\'m {agent_name}. It\'s great to connect with you today!',
            variables=['agent_name'],
            conditions={'turn_number': 1, 'context': 'greeting'}
        )
        
        self.templates['friendly_empathy'] = ResponseTemplate(
            template_id='friendly_empathy',
            name='Friendly Empathy',
            description='Empathetic response for friendly conversations',
            strategy=DialogueStrategy.FRIENDLY,
            template_text='I really appreciate you sharing that with me. It sounds like {situation} has been {emotion} for you.',
            variables=['situation', 'emotion'],
            conditions={'context': 'empathy'}
        )
        
        # Authoritative strategy templates
        self.templates['authoritative_greeting'] = ResponseTemplate(
            template_id='authoritative_greeting',
            name='Authoritative Greeting',
            description='Formal greeting for authoritative conversations',
            strategy=DialogueStrategy.AUTHORITATIVE,
            template_text='Good {time_of_day}. I\'m {agent_name} from {organization}. I need to discuss {matter} with you.',
            variables=['time_of_day', 'agent_name', 'organization', 'matter'],
            conditions={'turn_number': 1, 'context': 'greeting'}
        )
        
        self.templates['authoritative_request'] = ResponseTemplate(
            template_id='authoritative_request',
            name='Authoritative Request',
            description='Direct request for information',
            strategy=DialogueStrategy.AUTHORITATIVE,
            template_text='I need you to provide {information_type} immediately. This is {urgency_level} priority.',
            variables=['information_type', 'urgency_level'],
            conditions={'context': 'request'}
        )
        
        # Investigative strategy templates
        self.templates['investigative_inquiry'] = ResponseTemplate(
            template_id='investigative_inquiry',
            name='Investigative Inquiry',
            description='Detailed inquiry for investigative conversations',
            strategy=DialogueStrategy.INVESTIGATIVE,
            template_text='I need to understand the specifics of {situation}. Can you describe {details_needed} in detail?',
            variables=['situation', 'details_needed'],
            conditions={'context': 'inquiry'}
        )
        
        self.templates['investigative_verification'] = ResponseTemplate(
            template_id='investigative_verification',
            name='Investigative Verification',
            description='Verification question for investigative conversations',
            strategy=DialogueStrategy.INVESTIGATIVE,
            template_text='Just to confirm, you mentioned that {statement}. Is that correct?',
            variables=['statement'],
            conditions={'context': 'verification'}
        )
        
        # Persuasive strategy templates
        self.templates['persuasive_proposal'] = ResponseTemplate(
            template_id='persuasive_proposal',
            name='Persuasive Proposal',
            description='Persuasive proposal for convincing conversations',
            strategy=DialogueStrategy.PERSUASIVE,
            template_text='Based on what you\'ve told me, I believe {solution} would be perfect for your needs. It offers {benefits}.',
            variables=['solution', 'benefits'],
            conditions={'context': 'proposal'}
        )
        
        self.templates['persuasive_urgency'] = ResponseTemplate(
            template_id='persuasive_urgency',
            name='Persuasive Urgency',
            description='Create urgency for persuasive conversations',
            strategy=DialogueStrategy.PERSUASIVE,
            template_text='I should mention that this {opportunity} is only available until {deadline}. We wouldn\'t want you to miss out.',
            variables=['opportunity', 'deadline'],
            conditions={'context': 'urgency'}
        )
        
        # Suspicious strategy templates
        self.templates['suspicious_inquiry'] = ResponseTemplate(
            template_id='suspicious_inquiry',
            name='Suspicious Inquiry',
            description='Cautious inquiry for suspicious conversations',
            strategy=DialogueStrategy.SUSPICIOUS,
            template_text='I need to verify some information. You mentioned that {statement}, but that seems {inconsistency}. Can you explain?',
            variables=['statement', 'inconsistency'],
            conditions={'context': 'verification'}
        )
        
        self.templates['suspicious_challenge'] = ResponseTemplate(
            template_id='suspicious_challenge',
            name='Suspicious Challenge',
            description='Challenge for suspicious conversations',
            strategy=DialogueStrategy.SUSPICIOUS,
            template_text='I\'m having trouble understanding why {behavior}. Most people in this situation would {expected_behavior}.',
            variables=['behavior', 'expected_behavior'],
            conditions={'context': 'challenge'}
        )
    
    def generate_response(self, 
                          strategy: DialogueStrategy,
                          context: Dict[str, Any]) -> Optional[str]:
        """
        Generate a response based on strategy and context.
        
        Args:
            strategy: Dialogue strategy to use
            context: Context for response generation
            
        Returns:
            Generated response or None
        """
        try:
            # Find matching templates
            matching_templates = []
            
            for template in self.templates.values():
                if template.strategy == strategy:
                    # Check if template conditions match context
                    if self._template_matches_context(template, context):
                        matching_templates.append(template)
            
            if not matching_templates:
                # Fallback response
                return self._generate_fallback_response(strategy, context)
            
            # Sort by priority
            matching_templates.sort(key=lambda t: t.priority, reverse=True)
            
            # Use highest priority template
            template = matching_templates[0]
            
            # Fill variables
            response = template.template_text
            for variable in template.variables:
                if variable in context:
                    response = response.replace(f'{{{variable}}}', str(context[variable]))
                else:
                    # Use default value
                    response = response.replace(f'{{{variable}}}', f'[{variable}]')
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            return self._generate_fallback_response(strategy, context)
    
    def _template_matches_context(self, template: ResponseTemplate, context: Dict[str, Any]) -> bool:
        """Check if a template matches the given context."""
        try:
            conditions = template.conditions
            
            # Check turn number
            if 'turn_number' in conditions:
                if context.get('turn_number') != conditions['turn_number']:
                    return False
            
            # Check context type
            if 'context' in conditions:
                if context.get('context_type') != conditions['context']:
                    return False
            
            # Additional condition checks can be added here
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking template match: {e}")
            return False
    
    def _generate_fallback_response(self, strategy: DialogueStrategy, context: Dict[str, Any]) -> str:
        """Generate a fallback response when no template matches."""
        fallback_responses = {
            DialogueStrategy.NEUTRAL: "I understand. Can you tell me more about that?",
            DialogueStrategy.FRIENDLY: "That's interesting! I'd love to hear more about it.",
            DialogueStrategy.AUTHORITATIVE: "I need more information to proceed. Please provide the details.",
            DialogueStrategy.INVESTIGATIVE: "I need to understand this better. Can you elaborate?",
            DialogueStrategy.PERSUASIVE: "I think you'll find this quite beneficial. Let me explain.",
            DialogueStrategy.TECHNICAL: "I need to analyze the technical aspects. Can you provide specifications?",
            DialogueStrategy.CASUAL: "Oh, really? Tell me more about that.",
            DialogueStrategy.FORMAL: "Thank you for that information. I require additional details.",
            DialogueStrategy.URGENT: "This requires immediate attention. Please provide necessary information.",
            DialogueStrategy.SUSPICIOUS: "I need to verify that information. Can you confirm?"
        }
        
        return fallback_responses.get(strategy, "I understand. Please continue.")
    
    def add_template(self, template: ResponseTemplate) -> None:
        """Add a response template."""
        self.templates[template.template_id] = template
    
    def remove_template(self, template_id: str) -> bool:
        """Remove a response template."""
        if template_id in self.templates:
            del self.templates[template_id]
            return True
        return False
    
    def get_templates(self, strategy: Optional[DialogueStrategy] = None) -> List[ResponseTemplate]:
        """Get response templates, optionally filtered by strategy."""
        templates = list(self.templates.values())
        if strategy:
            templates = [t for t in templates if t.strategy == strategy]
        return templates


class ConversationManager:
    """
    Manager for conversations in the ATS MAFIA framework.
    
    Handles conversation lifecycle, message management, and response generation.
    """
    
    def __init__(self, 
                 config: FrameworkConfig,
                 audit_logger: Optional[AuditLogger] = None):
        """
        Initialize the conversation manager.
        
        Args:
            config: Framework configuration
            audit_logger: Audit logger instance
        """
        self.config = config
        self.audit_logger = audit_logger
        self.logger = logging.getLogger("conversation_manager")
        
        # Strategy engine
        self.strategy_engine = DialogueStrategyEngine(config)
        
        # Active conversations
        self.active_conversations: Dict[str, Conversation] = {}
        
        # Statistics
        self.statistics = {
            'total_conversations': 0,
            'active_conversations': 0,
            'completed_conversations': 0,
            'total_messages': 0,
            'total_turns': 0
        }
    
    async def start_conversation(self, 
                               participant_id: str,
                               participant_info: Dict[str, Any],
                               scenario_type: ScenarioType,
                               strategy: DialogueStrategy,
                               objectives: List[ConversationObjective]) -> str:
        """
        Start a new conversation.
        
        Args:
            participant_id: ID of the participant
            participant_info: Information about the participant
            scenario_type: Type of scenario
            strategy: Dialogue strategy to use
            objectives: List of conversation objectives
            
        Returns:
            Conversation ID
        """
        try:
            # Generate conversation ID
            conversation_id = str(uuid.uuid4())
            
            # Create conversation
            conversation = Conversation(
                conversation_id=conversation_id,
                participant_id=participant_id,
                participant_info=participant_info,
                scenario_type=scenario_type,
                strategy=strategy,
                objectives=objectives,
                turns=[],
                start_time=datetime.now(timezone.utc)
            )
            
            # Store conversation
            self.active_conversations[conversation_id] = conversation
            
            # Update statistics
            self.statistics['total_conversations'] += 1
            self.statistics['active_conversations'] += 1
            
            # Log to audit
            if self.audit_logger:
                self.audit_logger.audit(
                    event_type=AuditEventType.SYSTEM_EVENT,
                    action="conversation_started",
                    details={
                        'conversation_id': conversation_id,
                        'participant_id': participant_id,
                        'scenario_type': scenario_type.value,
                        'strategy': strategy.value,
                        'objectives_count': len(objectives)
                    },
                    security_level=SecurityLevel.MEDIUM
                )
            
            self.logger.info(f"Started conversation {conversation_id} with participant {participant_id}")
            return conversation_id
            
        except Exception as e:
            self.logger.error(f"Error starting conversation: {e}")
            raise
    
    async def end_conversation(self, conversation_id: str) -> bool:
        """
        End a conversation.
        
        Args:
            conversation_id: ID of the conversation to end
            
        Returns:
            True if conversation ended successfully, False otherwise
        """
        try:
            if conversation_id not in self.active_conversations:
                self.logger.warning(f"Conversation not found: {conversation_id}")
                return False
            
            conversation = self.active_conversations[conversation_id]
            
            # Update end time
            conversation.end_time = datetime.now(timezone.utc)
            
            # Update statistics
            self.statistics['active_conversations'] -= 1
            self.statistics['completed_conversations'] += 1
            
            # Remove from active conversations
            del self.active_conversations[conversation_id]
            
            # Log to audit
            if self.audit_logger:
                self.audit_logger.audit(
                    event_type=AuditEventType.SYSTEM_EVENT,
                    action="conversation_ended",
                    details={
                        'conversation_id': conversation_id,
                        'duration': conversation.get_duration(),
                        'turns_count': conversation.get_turn_count(),
                        'messages_count': conversation.get_message_count()
                    },
                    security_level=SecurityLevel.MEDIUM
                )
            
            self.logger.info(f"Ended conversation {conversation_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error ending conversation {conversation_id}: {e}")
            return False
    
    async def add_message(self, 
                         conversation_id: str,
                         turn: str,
                         content: str,
                         metadata: Dict[str, Any] = None) -> bool:
        """
        Add a message to a conversation.
        
        Args:
            conversation_id: ID of the conversation
            turn: Who is speaking ('agent' or 'participant')
            content: Message content
            metadata: Additional message metadata
            
        Returns:
            True if message added successfully, False otherwise
        """
        try:
            if conversation_id not in self.active_conversations:
                self.logger.warning(f"Conversation not found: {conversation_id}")
                return False
            
            conversation = self.active_conversations[conversation_id]
            
            # Create message
            message = DialogueMessage(
                message_id=str(uuid.uuid4()),
                turn=turn,
                content=content,
                message_type=MessageType.TEXT,
                priority=MessagePriority.NORMAL,
                timestamp=datetime.now(timezone.utc),
                metadata=metadata or {}
            )
            
            # Check if we need a new turn
            if not conversation.turns or conversation.turns[-1].turn_type != turn:
                # Create new turn
                new_turn = DialogueTurn(
                    turn_id=str(uuid.uuid4()),
                    turn_number=len(conversation.turns) + 1,
                    turn_type=turn,
                    messages=[message],
                    start_time=datetime.now(timezone.utc)
                )
                conversation.turns.append(new_turn)
            else:
                # Add to existing turn
                conversation.turns[-1].messages.append(message)
            
            # Update statistics
            self.statistics['total_messages'] += 1
            
            # Log to audit
            if self.audit_logger:
                self.audit_logger.audit(
                    event_type=AuditEventType.SYSTEM_EVENT,
                    action="conversation_message_added",
                    details={
                        'conversation_id': conversation_id,
                        'turn': turn,
                        'message_length': len(content)
                    },
                    security_level=SecurityLevel.LOW
                )
            
            self.logger.debug(f"Added message to conversation {conversation_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding message to conversation {conversation_id}: {e}")
            return False
    
    async def generate_response(self, 
                               conversation_id: str,
                               context: Dict[str, Any] = None) -> Optional[str]:
        """
        Generate a response for a conversation.
        
        Args:
            conversation_id: ID of the conversation
            context: Additional context for response generation
            
        Returns:
            Generated response or None
        """
        try:
            if conversation_id not in self.active_conversations:
                self.logger.warning(f"Conversation not found: {conversation_id}")
                return None
            
            conversation = self.active_conversations[conversation_id]
            
            # Prepare context
            if context is None:
                context = {}
            
            # Add conversation context
            context.update({
                'conversation_id': conversation_id,
                'strategy': conversation.strategy,
                'turn_number': len(conversation.turns) + 1,
                'participant_info': conversation.participant_info,
                'objectives': conversation.objectives
            })
            
            # Get last message for context
            last_message = conversation.get_last_message()
            if last_message:
                context['last_message'] = last_message.content
                context['last_turn'] = last_message.turn
            
            # Generate response
            response = self.strategy_engine.generate_response(
                strategy=conversation.strategy,
                context=context
            )
            
            self.logger.debug(f"Generated response for conversation {conversation_id}")
            return response
            
        except Exception as e:
            self.logger.error(f"Error generating response for conversation {conversation_id}: {e}")
            return None
    
    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """
        Get a conversation by ID.
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            Conversation or None if not found
        """
        return self.active_conversations.get(conversation_id)
    
    def get_active_conversations(self) -> List[Conversation]:
        """
        Get all active conversations.
        
        Returns:
            List of active conversations
        """
        return list(self.active_conversations.values())
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get conversation statistics.
        
        Returns:
            Dictionary containing statistics
        """
        return self.statistics.copy()
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        try:
            # End all active conversations
            conversation_ids = list(self.active_conversations.keys())
            for conversation_id in conversation_ids:
                await self.end_conversation(conversation_id)
            
            self.logger.info("Conversation manager cleanup complete")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")


# Global conversation manager instance
_global_conversation_manager: Optional[ConversationManager] = None


def get_conversation_manager() -> Optional[ConversationManager]:
    """
    Get the global conversation manager instance.
    
    Returns:
        Global ConversationManager instance or None if not initialized
    """
    return _global_conversation_manager


def initialize_conversation_manager(config: FrameworkConfig,
                                  audit_logger: Optional[AuditLogger] = None) -> ConversationManager:
    """
    Initialize the global conversation manager.
    
    Args:
        config: Framework configuration
        audit_logger: Audit logger instance
        
    Returns:
        Initialized ConversationManager instance
    """
    global _global_conversation_manager
    _global_conversation_manager = ConversationManager(config, audit_logger)
    return _global_conversation_manager


def shutdown_conversation_manager() -> None:
    """Shutdown the global conversation manager."""
    global _global_conversation_manager
    if _global_conversation_manager:
        asyncio.create_task(_global_conversation_manager.cleanup())
        _global_conversation_manager = None