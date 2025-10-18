# ATS MAFIA Framework Voice System

## Overview

The ATS MAFIA Framework Voice System provides comprehensive voice processing capabilities for social engineering training scenarios. It includes text-to-speech synthesis, speech recognition, voice analysis, phone integration, conversation management, and ethical safeguards.

## Architecture

### Core Components

1. **Voice Engine** (`core.py`)
   - Central voice processing engine
   - Real-time audio processing
   - Voice persona management
   - Command queue and processing

2. **Voice Engines** (`engines.py`)
   - Text-to-Speech (TTS) engines
   - Speech-to-Text (STT) engines
   - Voice analysis engines
   - Multiple engine support (pyttsx3, Azure, Google, AWS)

3. **Phone Integration** (`phone.py`)
   - VoIP/SIP phone integration
   - Call management system
   - Audio routing and processing
   - Call recording and analytics

4. **Voice Analysis** (`analysis.py`)
   - Emotion detection
   - Stress analysis
   - Psychological profiling
   - Deception detection

5. **Conversation Management** (`conversation.py`)
   - Dialogue strategy implementation
   - Conversation tracking
   - Objective management
   - Response generation

6. **Voice Tools** (`tools.py`)
   - Phone calling interface
   - Voice analysis tools
   - Conversation management tools
   - Vishing simulation tools

7. **Ethical Safeguards** (`ethics.py`)
   - Compliance validation
   - Ethical boundary enforcement
   - Training environment isolation
   - Audit and logging

## Features

### Voice Persona Management

The system supports multiple voice personas with configurable parameters:

- **Pitch**: Voice pitch adjustment (0.5 to 2.0)
- **Rate**: Speech rate control (0.5 to 2.0)
- **Volume**: Volume control (0.0 to 1.0)
- **Tone**: Voice tone (neutral, warm, cold, etc.)
- **Accent**: Accent simulation (neutral, american, british, etc.)
- **Emotion Modulation**: Emotional expression level (0.0 to 1.0)

### Real-Time Voice Adaptation

- Dynamic persona switching
- Emotion-based voice adaptation
- Stress-responsive voice changes
- Context-aware voice adjustments

### Phone Integration

- VoIP/SIP protocol support
- Call state management
- Audio streaming and recording
- Call analytics and metrics

### Voice Analysis

- **Emotion Detection**: Happiness, sadness, anger, fear, surprise, disgust, neutral
- **Stress Analysis**: Low, medium, high, extreme stress levels
- **Psychological Profiling**: Big Five personality traits, cognitive state, behavioral patterns
- **Deception Detection**: Probability-based deception analysis with risk assessment

### Conversation Management

- Multiple dialogue strategies
- Objective tracking and completion
- Real-time response generation
- Conversation analytics

### Ethical Safeguards

- Training environment isolation
- Content filtering and validation
- Ethical boundary enforcement
- Comprehensive audit logging

## Installation

### Dependencies

```bash
pip install pyttsx3
pip install SpeechRecognition
pip install numpy
pip install pyaudio
```

### Optional Dependencies

For enhanced functionality:

```bash
pip install azure-cognitiveservices-speech
pip install google-cloud-texttospeech
pip install boto3
```

## Configuration

### Basic Configuration

```python
from ats_mafia_framework.config.settings import FrameworkConfig

config = FrameworkConfig()
config.voice_enabled = True
config.voice_engine = "pyttsx3"
config.speech_recognition_engine = "speech_recognition"
config.voice_language = "en-US"
config.voice_rate = 200
config.voice_volume = 0.9
```

### Phone Configuration

```python
config.voice.phone.manager_type = "mock"  # or "sip"
config.voice.phone.sip.server = "sip.example.com"
config.voice.phone.sip.port = 5060
config.voice.phone.sip.username = "username"
config.voice.phone.sip.password = "password"
```

### Ethics Configuration

```python
config.voice.ethics.enabled = True
config.voice.ethics.training_isolation = True
config.voice.ethics.compliance_monitoring = True
config.voice.ethics.audit_logging = True
```

## Usage

### Basic Voice Operations

```python
from ats_mafia_framework.voice import (
    initialize_voice_engine,
    get_voice_engine,
    VoicePersona
)

# Initialize voice engine
voice_engine = initialize_voice_engine(config)

# Set voice persona
voice_engine.set_persona(VoicePersona.AUTHORITATIVE.value)

# Synthesize speech
command_id = voice_engine.add_command(
    command_type="speak",
    parameters={"text": "Hello, this is a test message."},
    priority=1
)
```

### Phone Operations

```python
from ats_mafia_framework.voice import (
    initialize_phone_call_manager,
    get_phone_call_manager
)

# Initialize phone manager
phone_manager = initialize_phone_call_manager(config)

# Make a call
call_id = await phone_manager.make_call(
    phone_number="+1234567890",
    participant_name="Test Participant",
    scenario_type="vishing_simulation"
)

# Send audio to call
from ats_mafia_framework.voice.core import AudioSegment, AudioFormat
audio_segment = await voice_engine.synthesize(
    text="This is a test call",
    persona=voice_engine.active_persona,
    format=AudioFormat.WAV
)

await phone_manager.send_audio(call_id, audio_segment)

# End call
await phone_manager.end_call(call_id)
```

### Voice Analysis

```python
from ats_mafia_framework.voice.analysis import (
    EmotionAnalyzer,
    StressAnalyzer,
    PsychologicalProfiler
)

# Analyze emotion
emotion_analyzer = EmotionAnalyzer(config)
emotion_result = await emotion_analyzer.analyze(audio_segment)

# Analyze stress
stress_analyzer = StressAnalyzer(config)
stress_result = await stress_analyzer.analyze(audio_segment)

# Analyze psychological profile
profiler = PsychologicalProfiler(config)
profile_result = await profiler.analyze(audio_segment, text_content)
```

### Conversation Management

```python
from ats_mafia_framework.voice import (
    initialize_conversation_manager,
    get_conversation_manager,
    ScenarioType,
    DialogueStrategy,
    ConversationObjective
)

# Initialize conversation manager
conversation_manager = initialize_conversation_manager(config)

# Define objectives
objectives = [
    ConversationObjective(
        objective_id="get_info",
        name="Get Information",
        description="Obtain specific information from participant",
        priority=8,
        completion_threshold=0.8
    )
]

# Start conversation
conversation_id = await conversation_manager.start_conversation(
    participant_id="participant_001",
    participant_info={"name": "Test User"},
    scenario_type=ScenarioType.VISHING_SIMULATION,
    strategy=DialogueStrategy.AUTHORITY,
    objectives=objectives
)

# Generate response
response = await conversation_manager.generate_agent_response(
    conversation_id=conversation_id,
    participant_message="I'm not sure about this",
    persona_name="authoritative"
)
```

### Ethical Safeguards

```python
from ats_mafia_framework.voice import (
    initialize_ethics_safeguards,
    get_ethics_safeguards,
    InteractionType,
    ScopeType
)

# Initialize ethics safeguards
ethics_safeguards = initialize_ethics_safeguards(config)

# Validate interaction
compliance_result = await ethics_safeguards.validate_interaction(
    interaction_id="interaction_001",
    interaction_type=InteractionType.TRAINING,
    scope_id=ScopeType.CONTROLLED_SIMULATION.value,
    participant_id="participant_001",
    content={"text": "Sample interaction content"}
)

# Check compliance
if compliance_result.compliance_level.value == "compliant":
    print("Interaction is compliant")
else:
    print(f"Violations: {compliance_result.violations}")
    print(f"Warnings: {compliance_result.warnings}")
```

## Voice Tools

### Phone Calling Tool

```python
from ats_mafia_framework.voice.tools import PhoneCallingTool

tool = PhoneCallingTool()
result = await tool.execute({
    "action": "make_call",
    "phone_number": "+1234567890",
    "scenario_type": "vishing_simulation"
}, context)
```

### Voice Analysis Tool

```python
from ats_mafia_framework.voice.tools import VoiceAnalysisTool

tool = VoiceAnalysisTool()
result = await tool.execute({
    "action": "analyze_emotion",
    "audio_data": audio_segment,
    "analysis_types": ["emotion", "stress", "psychological"]
}, context)
```

### Vishing Simulation Tool

```python
from ats_mafia_framework.voice.tools import VishingSimulationTool

tool = VishingSimulationTool()
result = await tool.execute({
    "action": "start_simulation",
    "scenario_type": "bank_verification",
    "participant_info": {"name": "Test User"},
    "objectives": ["get_account_info", "get_credentials"]
}, context)
```

## Ethical Guidelines

The voice system includes comprehensive ethical safeguards:

1. **Training Environment Isolation**: All interactions must remain within controlled training environments
2. **No Real-World Harm**: Prevents actions that could cause real-world harm
3. **Transparency**: Requires disclosure of AI nature and training purpose
4. **Data Privacy**: Protects participant data and privacy
5. **Content Filtering**: Blocks harmful or inappropriate content
6. **Time Limitation**: Limits interaction duration
7. **Compliance Monitoring**: Real-time compliance validation

## Performance Metrics

### Voice Processing
- **Response Time**: <300ms for voice synthesis
- **Persona Switch Time**: <100ms
- **Emotion Accuracy**: >85%
- **Stress Detection Accuracy**: >75%

### Phone Integration
- **Call Setup Time**: <5 seconds
- **Audio Latency**: <150ms
- **Call Quality**: >90% satisfaction

### Analysis Accuracy
- **Emotion Detection**: >80% accuracy
- **Stress Detection**: >75% accuracy
- **Psychological Profiling**: >70% accuracy
- **Deception Detection**: >60% accuracy

## Troubleshooting

### Common Issues

1. **Voice Engine Not Initializing**
   - Check if pyttsx3 is installed
   - Verify audio system is working
   - Check permissions

2. **Phone Integration Issues**
   - Verify SIP configuration
   - Check network connectivity
   - Validate credentials

3. **Analysis Engine Errors**
   - Check audio format compatibility
   - Verify sufficient audio data
   - Check model initialization

4. **Ethics Compliance Failures**
   - Review interaction content
   - Verify training environment setup
   - Check policy configurations

### Debug Mode

Enable debug mode for detailed logging:

```python
config.debug_mode = True
config.verbose_logging = True
```

## API Reference

### VoiceEngine Class

```python
class VoiceEngine:
    def __init__(self, config: FrameworkConfig, audit_logger: Optional[AuditLogger] = None)
    async def initialize(self) -> bool
    def add_command(self, command_type: str, parameters: Dict[str, Any], 
                   persona: Optional[VoicePersonaConfig] = None, 
                   priority: int = 0, callback: Optional[Callable] = None) -> str
    def set_persona(self, persona_name: str) -> bool
    def get_state(self) -> Dict[str, Any]
    def get_metrics(self) -> Dict[str, Any]
    async def shutdown(self) -> None
```

### PhoneCallManager Class

```python
class PhoneCallManager:
    def __init__(self, config: FrameworkConfig, audit_logger: Optional[AuditLogger] = None)
    async def initialize(self) -> bool
    async def make_call(self, phone_number: str, participant_name: Optional[str] = None, 
                       scenario_type: str = "general") -> Optional[str]
    async def end_call(self, call_id: str) -> bool
    async def send_audio(self, call_id: str, audio: AudioSegment) -> bool
    def get_call(self, call_id: str) -> Optional[CallInfo]
    def get_active_calls(self) -> List[CallInfo]
    def get_statistics(self) -> Dict[str, Any]
    async def cleanup(self) -> None
```

### ConversationManager Class

```python
class ConversationManager:
    def __init__(self, config: FrameworkConfig, audit_logger: Optional[AuditLogger] = None)
    async def start_conversation(self, participant_id: str, participant_info: Dict[str, Any], 
                               scenario_type: ScenarioType, strategy: DialogueStrategy, 
                               objectives: List[ConversationObjective]) -> Optional[str]
    async def end_conversation(self, conversation_id: str) -> bool
    async def add_message(self, conversation_id: str, message_type: MessageType, 
                         content: str, sender: str, persona: Optional[str] = None, 
                         priority: MessagePriority = MessagePriority.NORMAL, 
                         metadata: Dict[str, Any] = None) -> Optional[str]
    async def generate_agent_response(self, conversation_id: str, participant_message: str, 
                                     persona_name: str = "neutral") -> Optional[str]
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]
    def get_active_conversations(self) -> List[Conversation]
    def get_statistics(self) -> Dict[str, Any]
    async def cleanup(self) -> None
```

## Contributing

When contributing to the voice system:

1. Follow the existing code style and patterns
2. Add comprehensive tests for new features
3. Update documentation for any API changes
4. Ensure ethical safeguards are maintained
5. Test with various voice engines and configurations

## License

This voice system is part of the ATS MAFIA Framework and is subject to the same license terms.

## Support

For support and questions:

1. Check the troubleshooting section
2. Review the API documentation
3. Enable debug mode for detailed logging
4. Contact the ATS MAFIA development team