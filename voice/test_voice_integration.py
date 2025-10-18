"""
ATS MAFIA Framework Voice System Integration Test

This script tests the integration of the voice system with the core framework.
"""

import asyncio
import logging
import sys
import os
import time
from typing import Dict, Any

# Add the parent directory to the path to import framework modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import FrameworkConfig
from core.logging import AuditLogger, AuditEventType, SecurityLevel
from voice import (
    initialize_voice_system_manager,
    get_voice_system_manager,
    initialize_puppet_master_integration,
    get_puppet_master_integration,
    VoicePersona,
    VishingScenario
)


async def test_voice_system_initialization():
    """Test voice system initialization."""
    print("Testing voice system initialization...")
    
    try:
        # Create configuration
        config = FrameworkConfig()
        config.voice_enabled = True
        config.voice_engine = "pyttsx3"
        config.speech_recognition_engine = "speech_recognition"
        config.voice_language = "en-US"
        config.voice_rate = 200
        config.voice_volume = 0.9
        
        # Create audit logger
        audit_logger = AuditLogger("voice_system_test")
        
        # Initialize voice system manager
        voice_system_manager = initialize_voice_system_manager(config, audit_logger)
        
        # Wait for initialization
        await asyncio.sleep(2)
        
        # Check if initialized
        state = voice_system_manager.get_state()
        print(f"Voice system state: {state.value}")
        
        if state.value in ['ready', 'active']:
            print("✓ Voice system initialized successfully")
            return True
        else:
            print("✗ Voice system initialization failed")
            return False
            
    except Exception as e:
        print(f"✗ Error initializing voice system: {e}")
        return False


async def test_voice_synthesis():
    """Test voice synthesis."""
    print("Testing voice synthesis...")
    
    try:
        voice_system_manager = get_voice_system_manager()
        if not voice_system_manager:
            print("✗ Voice system manager not available")
            return False
        
        # Test synthesis with different personas
        test_text = "This is a test of the voice synthesis system."
        personas = [VoicePersona.NEUTRAL.value, VoicePersona.PROFESSIONAL.value, VoicePersona.AUTHORITATIVE.value]
        
        for persona in personas:
            print(f"Testing synthesis with persona: {persona}")
            
            # Synthesize speech
            audio_segment = await voice_system_manager.synthesize_speech(
                text=test_text,
                persona=persona
            )
            
            if audio_segment:
                print(f"✓ Synthesis successful for persona {persona}")
                print(f"  Duration: {audio_segment.duration:.2f}s")
                print(f"  Sample rate: {audio_segment.sample_rate}")
                print(f"  Channels: {audio_segment.channels}")
            else:
                print(f"✗ Synthesis failed for persona {persona}")
                return False
        
        print("✓ Voice synthesis test passed")
        return True
        
    except Exception as e:
        print(f"✗ Error testing voice synthesis: {e}")
        return False


async def test_conversation_management():
    """Test conversation management."""
    print("Testing conversation management...")
    
    try:
        voice_system_manager = get_voice_system_manager()
        if not voice_system_manager:
            print("✗ Voice system manager not available")
            return False
        
        # Test starting a conversation
        from voice.conversation import DialogueStrategy, ScenarioType, ConversationObjective
        
        objectives = [
            ConversationObjective(
                objective_id="test_objective",
                name="Test Objective",
                description="Test objective for conversation",
                priority=5,
                completion_threshold=0.8
            )
        ]
        
        conversation_id = await voice_system_manager.start_conversation(
            participant_id="test_participant",
            participant_info={"name": "Test User"},
            scenario_type=ScenarioType.TRAINING,
            strategy=DialogueStrategy.NEUTRAL,
            objectives=objectives
        )
        
        if conversation_id:
            print(f"✓ Conversation started successfully: {conversation_id}")
            
            # Test adding messages
            await voice_system_manager.conversation_manager.add_message(
                conversation_id=conversation_id,
                turn='participant',
                content='Hello, this is a test message.'
            )
            
            # Test generating response
            response = await voice_system_manager.conversation_manager.generate_response(
                conversation_id=conversation_id
            )
            
            if response:
                print(f"✓ Response generated: {response}")
            else:
                print("✗ Failed to generate response")
                return False
            
            # End conversation
            success = await voice_system_manager.end_conversation(conversation_id)
            if success:
                print("✓ Conversation ended successfully")
            else:
                print("✗ Failed to end conversation")
                return False
            
            return True
        else:
            print("✗ Failed to start conversation")
            return False
            
    except Exception as e:
        print(f"✗ Error testing conversation management: {e}")
        return False


async def test_puppet_master_integration():
    """Test Puppet Master integration."""
    print("Testing Puppet Master integration...")
    
    try:
        # Create configuration
        config = FrameworkConfig()
        config.voice_enabled = True
        config.voice_puppet_master_enable_voice_manipulation = True
        config.voice_puppet_master_enable_psychological_profiling = True
        config.voice_puppet_master_enable_real_time_adaptation = True
        config.voice_puppet_master_enable_vishing_simulation = True
        config.voice_puppet_master_enable_ethical_safeguards = True
        
        # Create audit logger
        audit_logger = AuditLogger("puppet_master_test")
        
        # Initialize Puppet Master integration
        pm_integration = initialize_puppet_master_integration(config, audit_logger)
        
        # Test starting a vishing session
        session_id = await pm_integration.start_vishing_session(
            participant_id="test_participant",
            participant_info={"name": "Test User"},
            scenario_type=VishingScenario.IT_SUPPORT
        )
        
        if session_id:
            print(f"✓ Vishing session started successfully: {session_id}")
            
            # Test processing participant input
            response = await pm_integration.process_participant_input(
                session_id=session_id,
                input_text="I'm having computer issues."
            )
            
            if response:
                print(f"✓ Response generated: {response}")
            else:
                print("✗ Failed to generate response")
                return False
            
            # Test synthesizing response
            audio_response = await pm_integration.synthesize_response(
                session_id=session_id,
                text=response
            )
            
            if audio_response:
                print(f"✓ Response synthesized successfully")
                print(f"  Duration: {audio_response.duration:.2f}s")
            else:
                print("✗ Failed to synthesize response")
                return False
            
            # End session
            summary = await pm_integration.end_vishing_session(session_id)
            if summary:
                print(f"✓ Session ended successfully")
                print(f"  Duration: {summary['duration_seconds']:.2f}s")
                print(f"  Success score: {summary['success_score']:.2f}")
            else:
                print("✗ Failed to end session")
                return False
            
            return True
        else:
            print("✗ Failed to start vishing session")
            return False
            
    except Exception as e:
        print(f"✗ Error testing Puppet Master integration: {e}")
        return False


async def test_voice_analysis():
    """Test voice analysis."""
    print("Testing voice analysis...")
    
    try:
        voice_system_manager = get_voice_system_manager()
        if not voice_system_manager:
            print("✗ Voice system manager not available")
            return False
        
        # Create mock audio data
        import numpy as np
        duration = 2.0  # 2 seconds
        sample_rate = 22050
        samples = int(sample_rate * duration)
        
        # Generate sine wave audio
        frequency = 440.0  # A4 note
        t = np.linspace(0, duration, samples)
        audio_data = np.sin(2 * np.pi * frequency * t) * 0.5
        
        from voice.core import AudioSegment, AudioFormat
        audio_segment = AudioSegment(
            data=audio_data,
            sample_rate=sample_rate,
            channels=1,
            format=AudioFormat.WAV,
            duration=duration
        )
        
        # Test analysis
        results = await voice_system_manager.analyze_voice(
            audio=audio_segment,
            text="This is a test audio for analysis.",
            analysis_types=['emotion', 'stress', 'psychological']
        )
        
        if results:
            print("✓ Voice analysis completed successfully")
            for analysis_type, result in results.items():
                print(f"  {analysis_type}: {result}")
            return True
        else:
            print("✗ Voice analysis failed")
            return False
            
    except Exception as e:
        print(f"✗ Error testing voice analysis: {e}")
        return False


async def test_ethics_safeguards():
    """Test ethics safeguards."""
    print("Testing ethics safeguards...")
    
    try:
        voice_system_manager = get_voice_system_manager()
        if not voice_system_manager:
            print("✗ Voice system manager not available")
            return False
        
        ethics_safeguards = voice_system_manager.ethics_safeguards
        if not ethics_safeguards:
            print("✗ Ethics safeguards not available")
            return False
        
        # Test validation
        from voice.ethics import InteractionType, ScopeType
        
        results = await ethics_safeguards.validate_interaction(
            interaction_id="test_interaction",
            interaction_type=InteractionType.TRAINING,
            scope_id=ScopeType.CONTROLLED.value,
            participant_id="test_participant",
            content={
                'text': 'This is a test interaction.',
                'scope_type': 'controlled',
                'consent_obtained': True,
                'encryption_enabled': True,
                'anonymization_enabled': True,
                'recording_notified': True
            }
        )
        
        if results:
            print("✓ Ethics validation completed successfully")
            
            # Check for violations
            violations = [r for r in results if not r.compliant]
            if violations:
                print(f"  Violations found: {len(violations)}")
                for violation in violations:
                    print(f"    {violation.rule_name}: {violation.details}")
            else:
                print("  No violations found")
            
            return True
        else:
            print("✗ Ethics validation failed")
            return False
            
    except Exception as e:
        print(f"✗ Error testing ethics safeguards: {e}")
        return False


async def test_system_metrics():
    """Test system metrics collection."""
    print("Testing system metrics...")
    
    try:
        voice_system_manager = get_voice_system_manager()
        if not voice_system_manager:
            print("✗ Voice system manager not available")
            return False
        
        # Get metrics
        metrics = voice_system_manager.get_metrics()
        
        if metrics:
            print("✓ System metrics retrieved successfully")
            print(f"  Total interactions: {metrics.total_interactions}")
            print(f"  Successful interactions: {metrics.successful_interactions}")
            print(f"  Failed interactions: {metrics.failed_interactions}")
            print(f"  Average latency: {metrics.average_latency_ms:.2f}ms")
            print(f"  System uptime: {metrics.system_uptime:.2f}s")
            return True
        else:
            print("✗ Failed to retrieve system metrics")
            return False
            
    except Exception as e:
        print(f"✗ Error testing system metrics: {e}")
        return False


async def run_all_tests():
    """Run all voice system tests."""
    print("=" * 60)
    print("ATS MAFIA Framework Voice System Integration Test")
    print("=" * 60)
    
    tests = [
        ("Voice System Initialization", test_voice_system_initialization),
        ("Voice Synthesis", test_voice_synthesis),
        ("Conversation Management", test_conversation_management),
        ("Puppet Master Integration", test_puppet_master_integration),
        ("Voice Analysis", test_voice_analysis),
        ("Ethics Safeguards", test_ethics_safeguards),
        ("System Metrics", test_system_metrics)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'-' * 40}")
        print(f"Running: {test_name}")
        print(f"{'-' * 40}")
        
        start_time = time.time()
        result = await test_func()
        end_time = time.time()
        
        duration = end_time - start_time
        results.append((test_name, result, duration))
        
        print(f"Test completed in {duration:.2f}s")
    
    # Print summary
    print(f"\n{'=' * 60}")
    print("Test Summary")
    print(f"{'=' * 60}")
    
    passed = sum(1 for _, result, _ in results if result)
    total = len(results)
    
    for test_name, result, duration in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name:<30} {status:<10} ({duration:.2f}s)")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Voice system is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the voice system configuration.")
    
    return passed == total


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run tests
    result = asyncio.run(run_all_tests())
    
    # Exit with appropriate code
    sys.exit(0 if result else 1)