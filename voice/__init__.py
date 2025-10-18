"""
ATS MAFIA Framework Voice Module

This module contains comprehensive voice processing and synthesis components for the ATS MAFIA framework.
Includes speech recognition, text-to-speech, voice analysis, phone integration, conversation management,
and ethical safeguards for social engineering training scenarios.
"""

# Core components
from .core import (
    VoiceEngine,
    VoiceState,
    AudioFormat,
    VoicePersona,
    VoicePersonaConfig,
    AudioSegment,
    VoiceCommand,
    VoiceProcessor,
    TTSEngine,
    STTEngine,
    VoiceAnalysisEngine,
    get_voice_engine,
    initialize_voice_engine,
    shutdown_voice_engine
)

# Voice engines
from .engines import (
    VoiceSynthesizer,
    SpeechRecognizer,
    TTSProvider,
    STTProvider,
    VoiceModel,
    PyTTSEngine,
    SpeechRecognitionEngine,
    VoiceAnalysisEngineImpl,
    get_voice_synthesizer,
    get_speech_recognizer,
    initialize_voice_engines,
    shutdown_voice_engines
)

# Phone integration
from .phone import (
    PhoneCallManager,
    PhoneCall,
    CallParticipant,
    CallState,
    CallType,
    ScenarioType,
    AudioDirection,
    VoIPProvider,
    MockVoIPProvider,
    get_phone_call_manager,
    initialize_phone_call_manager,
    shutdown_phone_call_manager
)

# Conversation management
from .conversation import (
    ConversationManager,
    Conversation,
    ConversationObjective,
    DialogueMessage,
    DialogueStrategy,
    DialogueTurn,
    ScenarioType as ConvScenarioType,
    ResponseTemplate,
    DialogueStrategyEngine,
    get_conversation_manager,
    initialize_conversation_manager,
    shutdown_conversation_manager
)

# Ethics safeguards
from .ethics import (
    EthicsSafeguards,
    ComplianceEngine,
    MonitoringEngine,
    ComplianceRule,
    ComplianceResult,
    InteractionSession,
    InteractionType,
    ComplianceLevel,
    RiskLevel,
    ScopeType,
    get_ethics_safeguards,
    initialize_ethics_safeguards,
    shutdown_ethics_safeguards
)

# Voice tools
from .tools import (
    PhoneCallingTool,
    VoiceAnalysisTool,
    ConversationManagementTool,
    VoiceSynthesisTool,
    SpeechRecognitionTool,
    EthicsValidationTool,
    TOOL_METADATA,
    TOOL_CLASSES,
    create_tool,
    get_all_tools,
    get_tool_metadata
)

# Voice integration
from .integration import (
    VoiceSystemManager,
    VoiceSystemState,
    VoiceSystemConfig,
    VoiceSystemMetrics,
    VoicePerformanceMonitor,
    get_voice_system_manager,
    initialize_voice_system_manager,
    shutdown_voice_system_manager
)

# Puppet Master integration
from .puppet_master_integration import (
    PuppetMasterVoiceIntegration,
    PuppetMasterPersona,
    VishingScenario,
    PuppetMasterConfig,
    VishingScenarioConfig,
    get_puppet_master_integration,
    initialize_puppet_master_integration,
    shutdown_puppet_master_integration
)

__all__ = [
    # Core components
    "VoiceEngine",
    "VoiceState",
    "AudioFormat",
    "VoicePersona",
    "VoicePersonaConfig",
    "AudioSegment",
    "VoiceCommand",
    "VoiceProcessor",
    "TTSEngine",
    "STTEngine",
    "VoiceAnalysisEngine",
    "get_voice_engine",
    "initialize_voice_engine",
    "shutdown_voice_engine",
    
    # Voice engines
    "VoiceSynthesizer",
    "SpeechRecognizer",
    "TTSProvider",
    "STTProvider",
    "VoiceModel",
    "PyTTSEngine",
    "SpeechRecognitionEngine",
    "VoiceAnalysisEngineImpl",
    "get_voice_synthesizer",
    "get_speech_recognizer",
    "initialize_voice_engines",
    "shutdown_voice_engines",
    
    # Phone integration
    "PhoneCallManager",
    "PhoneCall",
    "CallParticipant",
    "CallState",
    "CallType",
    "ScenarioType",
    "AudioDirection",
    "VoIPProvider",
    "MockVoIPProvider",
    "get_phone_call_manager",
    "initialize_phone_call_manager",
    "shutdown_phone_call_manager",
    
    # Conversation management
    "ConversationManager",
    "Conversation",
    "ConversationObjective",
    "DialogueMessage",
    "DialogueStrategy",
    "DialogueTurn",
    "ConvScenarioType",
    "ResponseTemplate",
    "DialogueStrategyEngine",
    "get_conversation_manager",
    "initialize_conversation_manager",
    "shutdown_conversation_manager",
    
    # Ethics safeguards
    "EthicsSafeguards",
    "ComplianceEngine",
    "MonitoringEngine",
    "ComplianceRule",
    "ComplianceResult",
    "InteractionSession",
    "InteractionType",
    "ComplianceLevel",
    "RiskLevel",
    "ScopeType",
    "get_ethics_safeguards",
    "initialize_ethics_safeguards",
    "shutdown_ethics_safeguards",
    
    # Voice tools
    "PhoneCallingTool",
    "VoiceAnalysisTool",
    "ConversationManagementTool",
    "VoiceSynthesisTool",
    "SpeechRecognitionTool",
    "EthicsValidationTool",
    "TOOL_METADATA",
    "TOOL_CLASSES",
    "create_tool",
    "get_all_tools",
    "get_tool_metadata",
    
    # Voice integration
    "VoiceSystemManager",
    "VoiceSystemState",
    "VoiceSystemConfig",
    "VoiceSystemMetrics",
    "VoicePerformanceMonitor",
    "get_voice_system_manager",
    "initialize_voice_system_manager",
    "shutdown_voice_system_manager",
    
    # Puppet Master integration
    "PuppetMasterVoiceIntegration",
    "PuppetMasterPersona",
    "VishingScenario",
    "PuppetMasterConfig",
    "VishingScenarioConfig",
    "get_puppet_master_integration",
    "initialize_puppet_master_integration",
    "shutdown_puppet_master_integration"
]