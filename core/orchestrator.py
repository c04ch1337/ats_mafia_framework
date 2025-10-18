"""
ATS MAFIA Framework Training Orchestrator

This module provides the training orchestration infrastructure for the ATS MAFIA framework.
It manages training sessions, scenario execution, agent coordination, and progress tracking.
"""

import asyncio
import uuid
import time
import json
import threading
from typing import Dict, Any, Optional, List, Union, Callable
from dataclasses import dataclass, asdict, field
from enum import Enum
from datetime import datetime, timezone
from pathlib import Path
import logging

from ..config.settings import FrameworkConfig
from .logging import AuditLogger, AuditEventType, SecurityLevel
from .profile_manager import ProfileManager, AgentProfile
from .tool_system import ToolRegistry
from .communication import CommunicationProtocol, Message, MessageType
from .llm_models import ModelRegistry, ModelSelector, LLMModel
from .cost_tracker import CostTracker
from .scenario_engine import (
    ScenarioLibrary, Scenario, AdaptiveDifficulty,
    DifficultyLevel, initialize_scenario_library, get_scenario_library
)


class SessionStatus(Enum):
    """Status of training sessions."""
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScenarioType(Enum):
    """Types of training scenarios."""
    RED_TEAM_EXERCISE = "red_team_exercise"
    BLUE_TEAM_DEFENSE = "blue_team_defense"
    SOCIAL_ENGINEERING = "social_engineering"
    INCIDENT_RESPONSE = "incident_response"
    THREAT_HUNTING = "threat_hunting"
    MALWARE_ANALYSIS = "malware_analysis"
    PENETRATION_TESTING = "penetration_testing"
    CUSTOM = "custom"


class AgentRole(Enum):
    """Roles that agents can play in scenarios."""
    ATTACKER = "attacker"
    DEFENDER = "defender"
    VICTIM = "victim"
    OBSERVER = "observer"
    COORDINATOR = "coordinator"
    FACILITATOR = "facilitator"


@dataclass
class ScenarioConfig:
    """Configuration for training scenarios."""
    id: str
    name: str
    description: str
    scenario_type: ScenarioType
    duration: int  # Maximum duration in seconds
    max_agents: int
    required_profiles: List[str] = field(default_factory=list)
    optional_profiles: List[str] = field(default_factory=list)
    environment_config: Dict[str, Any] = field(default_factory=dict)
    success_criteria: Dict[str, Any] = field(default_factory=dict)
    evaluation_metrics: List[str] = field(default_factory=list)
    resources: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert scenario config to dictionary."""
        data = asdict(self)
        data['scenario_type'] = self.scenario_type.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScenarioConfig':
        """Create scenario config from dictionary."""
        data['scenario_type'] = ScenarioType(data['scenario_type'])
        return cls(**data)


@dataclass
class AgentInstance:
    """Instance of an agent in a training session."""
    id: str
    profile_id: str
    role: AgentRole
    status: str = "initialized"
    config: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    communication_endpoint: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert agent instance to dictionary."""
        data = asdict(self)
        data['role'] = self.role.value
        if self.start_time:
            data['start_time'] = self.start_time.isoformat()
        if self.end_time:
            data['end_time'] = self.end_time.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentInstance':
        """Create agent instance from dictionary."""
        data['role'] = AgentRole(data['role'])
        if data.get('start_time'):
            data['start_time'] = datetime.fromisoformat(data['start_time'])
        if data.get('end_time'):
            data['end_time'] = datetime.fromisoformat(data['end_time'])
        return cls(**data)


@dataclass
class TrainingSession:
    """Training session definition."""
    id: str
    name: str
    description: str
    scenario: ScenarioConfig
    agents: List[AgentInstance] = field(default_factory=list)
    status: SessionStatus = SessionStatus.INITIALIZING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    config: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    results: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary."""
        data = asdict(self)
        data['scenario'] = self.scenario.to_dict()
        data['status'] = self.status.value
        data['agents'] = [agent.to_dict() for agent in self.agents]
        if self.start_time:
            data['start_time'] = self.start_time.isoformat()
        if self.end_time:
            data['end_time'] = self.end_time.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TrainingSession':
        """Create session from dictionary."""
        data['scenario'] = ScenarioConfig.from_dict(data['scenario'])
        data['status'] = SessionStatus(data['status'])
        data['agents'] = [AgentInstance.from_dict(agent) for agent in data.get('agents', [])]
        if data.get('start_time'):
            data['start_time'] = datetime.fromisoformat(data['start_time'])
        if data.get('end_time'):
            data['end_time'] = datetime.fromisoformat(data['end_time'])
        return cls(**data)


class ScenarioRunner:
    """Base class for scenario runners."""
    
    def __init__(self, scenario: ScenarioConfig):
        """
        Initialize scenario runner.
        
        Args:
            scenario: Scenario configuration
        """
        self.scenario = scenario
        self.logger = logging.getLogger(f"scenario_runner.{scenario.id}")
    
    async def initialize(self, session: TrainingSession) -> bool:
        """
        Initialize the scenario.
        
        Args:
            session: Training session
            
        Returns:
            True if initialization successful, False otherwise
        """
        # Override in subclasses
        return True
    
    async def execute(self, session: TrainingSession) -> Dict[str, Any]:
        """
        Execute the scenario.
        
        Args:
            session: Training session
            
        Returns:
            Scenario execution results
        """
        # Override in subclasses
        return {}
    
    async def cleanup(self, session: TrainingSession) -> None:
        """
        Clean up after scenario execution.
        
        Args:
            session: Training session
        """
        # Override in subclasses
        pass
    
    async def evaluate(self, session: TrainingSession) -> Dict[str, Any]:
        """
        Evaluate scenario execution results.
        
        Args:
            session: Training session
            
        Returns:
            Evaluation results
        """
        # Override in subclasses
        return {}


class TrainingOrchestrator:
    """
    Main training orchestrator for ATS MAFIA framework.
    
    Manages training sessions, scenario execution, agent coordination,
    and progress tracking with comprehensive monitoring and reporting.
    """
    
    def __init__(self,
                 config: FrameworkConfig,
                 profile_manager: ProfileManager,
                 tool_registry: ToolRegistry,
                 communication: CommunicationProtocol,
                 audit_logger: Optional[AuditLogger] = None):
        """
        Initialize the training orchestrator.
        
        Args:
            config: Framework configuration
            profile_manager: Profile manager instance
            tool_registry: Tool registry instance
            communication: Communication protocol instance
            audit_logger: Audit logger instance
        """
        self.config = config
        self.profile_manager = profile_manager
        self.tool_registry = tool_registry
        self.communication = communication
        self.audit_logger = audit_logger
        self.logger = logging.getLogger("training_orchestrator")
        
        # Initialize LLM management system
        self.model_registry = ModelRegistry()
        self.model_selector = ModelSelector(self.model_registry)
        self.cost_tracker = CostTracker(
            self.model_registry,
            storage_path="logs/llm_usage.json"
        )
        
        # Set up default budget alerts (75%, 90%, 100%)
        self._setup_default_budget_alerts()
        
        # Session management
        self.sessions: Dict[str, TrainingSession] = {}
        self.active_sessions: Dict[str, TrainingSession] = {}
        self.session_lock = threading.RLock()
        
        # Scenario management - legacy support
        self.scenarios: Dict[str, ScenarioConfig] = {}
        self.scenario_runners: Dict[str, type] = {}
        
        # New scenario engine integration
        self.scenario_library = initialize_scenario_library(config, audit_logger)
        self.adaptive_difficulty: Dict[str, AdaptiveDifficulty] = {}
        
        # Background tasks
        self.monitor_task = None
        self.cleanup_task = None
        
        # Statistics
        self.stats = {
            'sessions_created': 0,
            'sessions_completed': 0,
            'sessions_failed': 0,
            'scenarios_executed': 0,
            'total_execution_time': 0.0
        }
        
        # Load default scenarios
        self._load_default_scenarios()
        
        # Start background tasks
        self._start_background_tasks()
    
    def _setup_default_budget_alerts(self) -> None:
        """Set up default budget alert thresholds."""
        # These will be applied to sessions that set budgets
        self.default_alert_thresholds = [0.75, 0.90, 1.0]
        
        def budget_alert_callback(entity_id: str, spent: float, budget: float):
            """Default callback for budget alerts."""
            percentage = (spent / budget * 100) if budget > 0 else 0
            self.logger.warning(
                f"Budget alert for {entity_id}: ${spent:.2f} / ${budget:.2f} ({percentage:.1f}%)"
            )
            
            if self.audit_logger:
                self.audit_logger.audit(
                    event_type=AuditEventType.SYSTEM_EVENT,
                    action="budget_alert_triggered",
                    details={
                        'entity_id': entity_id,
                        'spent': spent,
                        'budget': budget,
                        'percentage': percentage
                    },
                    security_level=SecurityLevel.MEDIUM
                )
        
        self.budget_alert_callback = budget_alert_callback
    
    def _load_default_scenarios(self) -> None:
        """Load default training scenarios."""
        # Create basic red team scenario
        red_team_scenario = ScenarioConfig(
            id="basic_red_team",
            name="Basic Red Team Exercise",
            description="A basic red team exercise for penetration testing training",
            scenario_type=ScenarioType.RED_TEAM_EXERCISE,
            duration=3600,  # 1 hour
            max_agents=4,
            required_profiles=["red_team_operator"],
            optional_profiles=["social_engineer"],
            environment_config={
                "network": "training_network",
                "targets": ["target_1", "target_2"],
                "tools": ["nmap", "metasploit", "burp_suite"]
            },
            success_criteria={
                "compromise_targets": 1,
                "exfiltrate_data": True,
                "maintain_access": True
            },
            evaluation_metrics=[
                "time_to_compromise",
                "stealth_score",
                "coverage_score",
                "technique_diversity"
            ]
        )
        
        self.scenarios[red_team_scenario.id] = red_team_scenario
        
        # Create basic blue team scenario
        blue_team_scenario = ScenarioConfig(
            id="basic_blue_team",
            name="Basic Blue Team Defense",
            description="A basic blue team exercise for defensive security training",
            scenario_type=ScenarioType.BLUE_TEAM_DEFENSE,
            duration=3600,  # 1 hour
            max_agents=4,
            required_profiles=["security_analyst"],
            optional_profiles=["incident_responder", "threat_hunter"],
            environment_config={
                "network": "training_network",
                "sensors": ["ids_1", "siem_1"],
                "tools": ["wireshark", "splunk", "elastic"]
            },
            success_criteria={
                "detect_intrusion": True,
                "contain_threat": True,
                "preserve_evidence": True
            },
            evaluation_metrics=[
                "detection_time",
                "response_time",
                "accuracy_score",
                "coordination_score"
            ]
        )
        
        self.scenarios[blue_team_scenario.id] = blue_team_scenario
        
        self.logger.info(f"Loaded {len(self.scenarios)} default scenarios")
    
    def _start_background_tasks(self) -> None:
        """Start background monitoring and cleanup tasks."""
        self.monitor_task = asyncio.create_task(self._monitor_sessions())
        self.cleanup_task = asyncio.create_task(self._cleanup_resources())
    
    async def _monitor_sessions(self) -> None:
        """Monitor active training sessions."""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                current_time = datetime.now(timezone.utc)
                sessions_to_check = list(self.active_sessions.values())
                
                for session in sessions_to_check:
                    # Check timeout
                    if (session.start_time and 
                        (current_time - session.start_time).total_seconds() > session.scenario.duration):
                        
                        self.logger.warning(f"Session {session.id} timed out")
                        await self.complete_session(session.id, "timeout")
                    
                    # Check agent health
                    for agent in session.agents:
                        if agent.status == "failed":
                            self.logger.warning(f"Agent {agent.id} in session {session.id} failed")
                            # Handle agent failure
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in session monitoring: {e}")
    
    async def _cleanup_resources(self) -> None:
        """Clean up completed session resources."""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                
                current_time = datetime.now(timezone.utc)
                sessions_to_cleanup = []
                
                for session in self.sessions.values():
                    if (session.end_time and 
                        (current_time - session.end_time).total_seconds() > 3600):  # 1 hour after completion
                        sessions_to_cleanup.append(session.id)
                
                for session_id in sessions_to_cleanup:
                    self.cleanup_session(session_id)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in resource cleanup: {e}")
    
    def register_scenario(self, scenario: ScenarioConfig) -> None:
        """
        Register a training scenario (legacy method).
        
        Args:
            scenario: Scenario configuration to register
        """
        self.scenarios[scenario.id] = scenario
        
        if self.audit_logger:
            self.audit_logger.audit(
                event_type=AuditEventType.SYSTEM_EVENT,
                action="scenario_registered",
                details={'scenario_id': scenario.id, 'name': scenario.name},
                security_level=SecurityLevel.LOW
            )
        
        self.logger.info(f"Registered scenario: {scenario.id}")
    
    def register_new_scenario(self, scenario: Scenario) -> None:
        """
        Register a scenario using the new scenario engine.
        
        Args:
            scenario: Scenario object from scenario_engine
        """
        self.scenario_library.register_scenario(scenario)
        self.logger.info(f"Registered new-style scenario: {scenario.id}")
    
    def get_scenario_library(self) -> ScenarioLibrary:
        """
        Get the scenario library instance.
        
        Returns:
            ScenarioLibrary instance
        """
        return self.scenario_library
    
    def get_new_scenario(self, scenario_id: str) -> Optional[Scenario]:
        """
        Get a scenario from the new scenario engine.
        
        Args:
            scenario_id: ID of the scenario
            
        Returns:
            Scenario object or None if not found
        """
        return self.scenario_library.get_scenario(scenario_id)
    
    def list_new_scenarios(self, **filters) -> List[Dict[str, Any]]:
        """
        List scenarios from the new scenario engine.
        
        Args:
            **filters: Optional filters (scenario_type, difficulty, tags)
            
        Returns:
            List of scenario dictionaries
        """
        return self.scenario_library.list_scenarios(**filters)
    
    def register_scenario_runner(self, scenario_type: ScenarioType, runner_class: type) -> None:
        """
        Register a scenario runner class.
        
        Args:
            scenario_type: Type of scenario
            runner_class: Runner class
        """
        self.scenario_runners[scenario_type.value] = runner_class
        self.logger.info(f"Registered scenario runner for {scenario_type.value}")
    
    def _select_model_for_agent(self,
                                profile: AgentProfile,
                                task_type: str,
                                llm_config: Dict[str, Any]) -> Optional[LLMModel]:
        """
        Select the optimal LLM model for an agent based on profile and task.
        
        Args:
            profile: Agent profile
            task_type: Type of task/scenario
            llm_config: LLM configuration from profile
            
        Returns:
            Selected model or None if no suitable model found
        """
        try:
            # Extract configuration
            max_cost = llm_config.get('max_cost_per_request')
            preferred_tier = llm_config.get('preferred_tier')
            
            # Map task type to supported task types
            task_mapping = {
                'red_team_exercise': 'exploitation',
                'penetration_testing': 'exploitation',
                'blue_team_defense': 'defense',
                'social_engineering': 'social_engineering',
                'incident_response': 'defense',
                'threat_hunting': 'reconnaissance',
                'malware_analysis': 'analysis'
            }
            
            mapped_task = task_mapping.get(task_type, 'reconnaissance')
            
            # Select model
            model = self.model_selector.select_model(
                task_type=mapped_task,
                profile_config=llm_config,
                max_cost_per_request=max_cost,
                preferred_tier=None  # Will use profile's primary_model if specified
            )
            
            if model:
                self.logger.info(
                    f"Selected model {model.get_full_name()} for profile {profile.metadata.id} "
                    f"(task: {mapped_task})"
                )
            else:
                self.logger.warning(
                    f"No suitable model found for profile {profile.metadata.id} "
                    f"(task: {mapped_task})"
                )
            
            return model
            
        except Exception as e:
            self.logger.error(f"Error selecting model for agent: {e}")
            return None
    
    def get_model_registry(self) -> ModelRegistry:
        """
        Get the model registry instance.
        
        Returns:
            Model registry
        """
        return self.model_registry
    
    def get_cost_tracker(self) -> CostTracker:
        """
        Get the cost tracker instance.
        
        Returns:
            Cost tracker
        """
        return self.cost_tracker
    
    def get_session_llm_costs(self, session_id: str) -> Dict[str, Any]:
        """
        Get LLM costs for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dictionary with cost information
        """
        total_cost = self.cost_tracker.get_session_cost(session_id)
        tokens = self.cost_tracker.get_session_tokens(session_id)
        breakdown = self.cost_tracker.get_cost_breakdown(session_id=session_id)
        budget = self.cost_tracker.session_budgets.get(session_id)
        remaining = self.cost_tracker.get_remaining_budget(session_id)
        
        return {
            'session_id': session_id,
            'total_cost': total_cost,
            'tokens': tokens,
            'breakdown_by_model': breakdown,
            'budget': budget,
            'remaining_budget': remaining,
            'within_budget': self.cost_tracker.is_within_budget(session_id)
        }
    
    def list_scenarios(self) -> List[Dict[str, Any]]:
        """
        List available scenarios (includes both legacy and new scenarios).
        
        Returns:
            List of scenario configurations
        """
        # Legacy scenarios
        legacy = [scenario.to_dict() for scenario in self.scenarios.values()]
        
        # New scenarios
        new_scenarios = self.scenario_library.list_scenarios()
        
        # Combine and deduplicate by ID
        all_scenarios = {s['id']: s for s in legacy + new_scenarios}
        
        return list(all_scenarios.values())
    
    def get_scenario(self, scenario_id: str) -> Optional[ScenarioConfig]:
        """
        Get a scenario by ID.
        
        Args:
            scenario_id: ID of the scenario
            
        Returns:
            Scenario configuration or None if not found
        """
        return self.scenarios.get(scenario_id)
    
    async def create_session(self,
                           name: str,
                           description: str,
                           scenario_id: str,
                           agent_configs: List[Dict[str, Any]],
                           session_config: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Create a new training session.
        
        Args:
            name: Session name
            description: Session description
            scenario_id: ID of the scenario to run
            agent_configs: List of agent configurations
            session_config: Additional session configuration
            
        Returns:
            Session ID if created successfully, None otherwise
        """
        try:
            # Try to get scenario from new engine first, fallback to legacy
            new_scenario = self.scenario_library.get_scenario(scenario_id)
            scenario = self.get_scenario(scenario_id)
            
            if not scenario and not new_scenario:
                self.logger.error(f"Scenario not found: {scenario_id}")
                return None
            
            # Use legacy scenario for session creation (maintain compatibility)
            if not scenario and new_scenario:
                # For now, we require legacy scenario for session creation
                # TODO: Add full new scenario support to TrainingSession
                self.logger.warning(f"New-style scenario {scenario_id} found but needs legacy adapter")
                return None
            
            # Validate agent configurations
            if len(agent_configs) > scenario.max_agents:
                self.logger.error(f"Too many agents for scenario {scenario_id}: {len(agent_configs)} > {scenario.max_agents}")
                return None
            
            # Create session
            session = TrainingSession(
                id=str(uuid.uuid4()),
                name=name,
                description=description,
                scenario=scenario,
                config=session_config or {}
            )
            
            # Initialize adaptive difficulty if new scenario available
            if new_scenario:
                self.adaptive_difficulty[session.id] = AdaptiveDifficulty(
                    new_scenario.difficulty
                )
            
            # Add agents
            for agent_config in agent_configs:
                profile_id = agent_config.get('profile_id')
                if not profile_id:
                    self.logger.error("Agent configuration missing profile_id")
                    return None
                
                # Verify profile exists
                profile = self.profile_manager.get_profile(profile_id)
                if not profile:
                    self.logger.error(f"Profile not found: {profile_id}")
                    return None
                
                # Get LLM configuration from profile
                llm_config = profile.custom_data.get('llm_configuration', {})
                
                # Select model for this agent
                task_type = scenario.scenario_type.value if scenario else "reconnaissance"
                selected_model = self._select_model_for_agent(
                    profile=profile,
                    task_type=task_type,
                    llm_config=llm_config
                )
                
                agent = AgentInstance(
                    id=str(uuid.uuid4()),
                    profile_id=profile_id,
                    role=AgentRole(agent_config.get('role', 'participant')),
                    config={
                        **agent_config,
                        'selected_model': selected_model.get_full_name() if selected_model else None
                    }
                )
                
                session.agents.append(agent)
            
            # Store session
            with self.session_lock:
                self.sessions[session.id] = session
            
            # Set up session budget if configured
            if session_config and 'budget' in session_config:
                budget = session_config['budget']
                self.cost_tracker.set_session_budget(session.id, budget)
                
                # Add default alert thresholds
                for threshold in self.default_alert_thresholds:
                    self.cost_tracker.add_budget_alert(
                        session.id,
                        threshold,
                        self.budget_alert_callback
                    )
            
            self.stats['sessions_created'] += 1
            
            if self.audit_logger:
                self.audit_logger.audit(
                    event_type=AuditEventType.TRAINING_EVENT,
                    action="session_created",
                    details={
                        'session_id': session.id,
                        'name': name,
                        'scenario_id': scenario_id,
                        'agents': len(session.agents)
                    },
                    security_level=SecurityLevel.LOW
                )
            
            self.logger.info(f"Created training session: {session.id}")
            return session.id
            
        except Exception as e:
            self.logger.error(f"Error creating training session: {e}")
            return None
    
    async def start_session(self, session_id: str) -> bool:
        """
        Start a training session.
        
        Args:
            session_id: ID of the session to start
            
        Returns:
            True if session started successfully, False otherwise
        """
        try:
            with self.session_lock:
                session = self.sessions.get(session_id)
                if not session:
                    self.logger.error(f"Session not found: {session_id}")
                    return False
                
                if session.status != SessionStatus.INITIALIZING:
                    self.logger.error(f"Session {session_id} is not in initializing state")
                    return False
            
            # Initialize scenario
            scenario_runner = self._get_scenario_runner(session.scenario)
            if not await scenario_runner.initialize(session):
                self.logger.error(f"Failed to initialize scenario for session {session_id}")
                session.status = SessionStatus.FAILED
                return False
            
            # Update session status
            session.status = SessionStatus.RUNNING
            session.start_time = datetime.now(timezone.utc)
            
            # Add to active sessions
            self.active_sessions[session_id] = session
            
            # Start agent instances
            for agent in session.agents:
                agent.status = "running"
                agent.start_time = datetime.now(timezone.utc)
            
            # Execute scenario
            asyncio.create_task(self._execute_session(session_id))
            
            if self.audit_logger:
                self.audit_logger.audit(
                    event_type=AuditEventType.TRAINING_EVENT,
                    action="session_started",
                    details={'session_id': session_id},
                    security_level=SecurityLevel.LOW
                )
            
            self.logger.info(f"Started training session: {session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting session {session_id}: {e}")
            return False
    
    async def _execute_session(self, session_id: str) -> None:
        """
        Execute a training session.
        
        Args:
            session_id: ID of the session to execute
        """
        try:
            with self.session_lock:
                session = self.sessions.get(session_id)
                if not session:
                    return
            
            # Get scenario runner
            scenario_runner = self._get_scenario_runner(session.scenario)
            
            # Execute scenario
            results = await scenario_runner.execute(session)
            session.results.update(results)
            
            # Evaluate results
            evaluation = await scenario_runner.evaluate(session)
            session.metrics.update(evaluation)
            
            # Complete session
            await self.complete_session(session_id, "completed")
            
        except Exception as e:
            self.logger.error(f"Error executing session {session_id}: {e}")
            await self.complete_session(session_id, "failed", str(e))
    
    def _get_scenario_runner(self, scenario: ScenarioConfig) -> ScenarioRunner:
        """
        Get a scenario runner for the given scenario.
        
        Args:
            scenario: Scenario configuration
            
        Returns:
            Scenario runner instance
        """
        runner_class = self.scenario_runners.get(scenario.scenario_type.value, ScenarioRunner)
        return runner_class(scenario)
    
    async def pause_session(self, session_id: str) -> bool:
        """
        Pause a training session.
        
        Args:
            session_id: ID of the session to pause
            
        Returns:
            True if session paused successfully, False otherwise
        """
        try:
            with self.session_lock:
                session = self.sessions.get(session_id)
                if not session:
                    return False
                
                if session.status != SessionStatus.RUNNING:
                    return False
                
                session.status = SessionStatus.PAUSED
            
            if self.audit_logger:
                self.audit_logger.audit(
                    event_type=AuditEventType.TRAINING_EVENT,
                    action="session_paused",
                    details={'session_id': session_id},
                    security_level=SecurityLevel.LOW
                )
            
            self.logger.info(f"Paused training session: {session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error pausing session {session_id}: {e}")
            return False
    
    async def resume_session(self, session_id: str) -> bool:
        """
        Resume a paused training session.
        
        Args:
            session_id: ID of the session to resume
            
        Returns:
            True if session resumed successfully, False otherwise
        """
        try:
            with self.session_lock:
                session = self.sessions.get(session_id)
                if not session:
                    return False
                
                if session.status != SessionStatus.PAUSED:
                    return False
                
                session.status = SessionStatus.RUNNING
            
            if self.audit_logger:
                self.audit_logger.audit(
                    event_type=AuditEventType.TRAINING_EVENT,
                    action="session_resumed",
                    details={'session_id': session_id},
                    security_level=SecurityLevel.LOW
                )
            
            self.logger.info(f"Resumed training session: {session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error resuming session {session_id}: {e}")
            return False
    
    async def cancel_session(self, session_id: str, reason: str = "cancelled") -> bool:
        """
        Cancel a training session.
        
        Args:
            session_id: ID of the session to cancel
            reason: Reason for cancellation
            
        Returns:
            True if session cancelled successfully, False otherwise
        """
        try:
            with self.session_lock:
                session = self.sessions.get(session_id)
                if not session:
                    return False
                
                session.status = SessionStatus.CANCELLED
                session.end_time = datetime.now(timezone.utc)
            
            # Remove from active sessions
            self.active_sessions.pop(session_id, None)
            
            # Stop agents
            for agent in session.agents:
                agent.status = "cancelled"
                agent.end_time = datetime.now(timezone.utc)
            
            if self.audit_logger:
                self.audit_logger.audit(
                    event_type=AuditEventType.TRAINING_EVENT,
                    action="session_cancelled",
                    details={'session_id': session_id, 'reason': reason},
                    security_level=SecurityLevel.LOW
                )
            
            self.logger.info(f"Cancelled training session: {session_id} - {reason}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error cancelling session {session_id}: {e}")
            return False
    
    async def complete_session(self, session_id: str, result: str, error: Optional[str] = None) -> bool:
        """
        Complete a training session.
        
        Args:
            session_id: ID of the session to complete
            result: Completion result ("completed", "failed", "timeout")
            error: Error message if failed
            
        Returns:
            True if session completed successfully, False otherwise
        """
        try:
            with self.session_lock:
                session = self.sessions.get(session_id)
                if not session:
                    return False
                
                # Update session status
                if result == "completed":
                    session.status = SessionStatus.COMPLETED
                    self.stats['sessions_completed'] += 1
                else:
                    session.status = SessionStatus.FAILED
                    self.stats['sessions_failed'] += 1
                
                session.end_time = datetime.now(timezone.utc)
                
                # Calculate execution time
                if session.start_time:
                    execution_time = (session.end_time - session.start_time).total_seconds()
                    session.metrics['execution_time'] = execution_time
                    self.stats['total_execution_time'] += execution_time
                
                # Stop agents
                for agent in session.agents:
                    agent.status = result
                    agent.end_time = session.end_time
            
            # Record performance metrics (Phase 4 integration)
            await self._record_session_analytics(session, result)
            
            # Remove from active sessions
            self.active_sessions.pop(session_id, None)
            
            # Get scenario runner for cleanup
            scenario_runner = self._get_scenario_runner(session.scenario)
            await scenario_runner.cleanup(session)
            
            if self.audit_logger:
                self.audit_logger.audit(
                    event_type=AuditEventType.TRAINING_EVENT,
                    action="session_completed",
                    details={
                        'session_id': session_id,
                        'result': result,
                        'execution_time': session.metrics.get('execution_time'),
                        'error': error
                    },
                    security_level=SecurityLevel.LOW
                )
            
            self.logger.info(f"Completed training session: {session_id} - {result}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error completing session {session_id}: {e}")
            return False
    
    def get_session(self, session_id: str) -> Optional[TrainingSession]:
        """
        Get a training session by ID.
        
        Args:
            session_id: ID of the session
            
        Returns:
            Training session or None if not found
        """
        with self.session_lock:
            return self.sessions.get(session_id)
    
    def list_sessions(self, 
                     status: Optional[SessionStatus] = None,
                     scenario_type: Optional[ScenarioType] = None) -> List[Dict[str, Any]]:
        """
        List training sessions with optional filtering.
        
        Args:
            status: Filter by session status
            scenario_type: Filter by scenario type
            
        Returns:
            List of session dictionaries
        """
        with self.session_lock:
            sessions = []
            
            for session in self.sessions.values():
                # Apply filters
                if status and session.status != status:
                    continue
                
                if scenario_type and session.scenario.scenario_type != scenario_type:
                    continue
                
                sessions.append(session.to_dict())
            
            return sessions
    
    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """
        Get all active training sessions.
        
        Returns:
            List of active session dictionaries
        """
        return [session.to_dict() for session in self.active_sessions.values()]
    
    def get_session_logs(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get logs for a training session.
        
        Args:
            session_id: ID of the session
            
        Returns:
            List of log entries
        """
        with self.session_lock:
            session = self.sessions.get(session_id)
            if session:
                return session.logs.copy()
            return []
    
    def add_session_log(self, session_id: str, log_entry: Dict[str, Any]) -> bool:
        """
        Add a log entry to a training session.
        
        Args:
            session_id: ID of the session
            log_entry: Log entry to add
            
        Returns:
            True if log added successfully, False otherwise
        """
        try:
            with self.session_lock:
                session = self.sessions.get(session_id)
                if not session:
                    return False
                
                # Add timestamp if not present
                if 'timestamp' not in log_entry:
                    log_entry['timestamp'] = datetime.now(timezone.utc).isoformat()
                
                session.logs.append(log_entry)
                
                # Limit log size
                if len(session.logs) > 10000:
                    session.logs = session.logs[-5000:]
                
                return True
                
        except Exception as e:
            self.logger.error(f"Error adding log to session {session_id}: {e}")
            return False
    
    def get_session_metrics(self, session_id: str) -> Dict[str, Any]:
        """
        Get metrics for a training session.
        
        Args:
            session_id: ID of the session
            
        Returns:
            Session metrics dictionary
        """
        with self.session_lock:
            session = self.sessions.get(session_id)
            if session:
                return session.metrics.copy()
            return {}
    
    def update_agent_metrics(self, session_id: str, agent_id: str, metrics: Dict[str, Any]) -> bool:
        """
        Update metrics for an agent in a session.
        
        Args:
            session_id: ID of the session
            agent_id: ID of the agent
            metrics: Metrics to update
            
        Returns:
            True if metrics updated successfully, False otherwise
        """
        try:
            with self.session_lock:
                session = self.sessions.get(session_id)
                if not session:
                    return False
                
                # Find agent
                for agent in session.agents:
                    if agent.id == agent_id:
                        agent.metrics.update(metrics)
                        return True
                
                return False
                
        except Exception as e:
            self.logger.error(f"Error updating agent metrics: {e}")
            return False
    
    def cleanup_session(self, session_id: str) -> bool:
        """
        Clean up resources for a completed session.
        
        Args:
            session_id: ID of the session to clean up
            
        Returns:
            True if cleanup successful, False otherwise
        """
        try:
            with self.session_lock:
                if session_id in self.sessions:
                    del self.sessions[session_id]
            
            self.active_sessions.pop(session_id, None)
            
            if self.audit_logger:
                self.audit_logger.audit(
                    event_type=AuditEventType.SYSTEM_EVENT,
                    action="session_cleaned_up",
                    details={'session_id': session_id},
                    security_level=SecurityLevel.LOW
                )
            
            self.logger.info(f"Cleaned up session: {session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error cleaning up session {session_id}: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get orchestrator statistics.
        
        Returns:
            Dictionary containing statistics
        """
        with self.session_lock:
            active_count = len(self.active_sessions)
            total_count = len(self.sessions)
            
            sessions_by_status = {}
            sessions_by_scenario = {}
            
            for session in self.sessions.values():
                # Count by status
                status = session.status.value
                sessions_by_status[status] = sessions_by_status.get(status, 0) + 1
                
                # Count by scenario
                scenario = session.scenario.name
                sessions_by_scenario[scenario] = sessions_by_scenario.get(scenario, 0) + 1
            
            return {
                'total_sessions': total_count,
                'active_sessions': active_count,
                'sessions_by_status': sessions_by_status,
                'sessions_by_scenario': sessions_by_scenario,
                'available_scenarios': len(self.scenarios),
                **self.stats
            }
    
    async def _record_session_analytics(self, session: TrainingSession, result: str) -> None:
        """
        Record session analytics for performance tracking (Phase 4 integration).
        
        Args:
            session: Completed training session
            result: Session result
        """
        try:
            # This method provides a hook for Phase 4 analytics integration
            # The actual analytics recording would be done by a registered analytics engine
            
            # Extract session data for analytics
            session_data = {
                'session_id': session.id,
                'scenario_id': session.scenario.id,
                'start_time': session.start_time,
                'end_time': session.end_time,
                'duration_seconds': session.metrics.get('execution_time', 0),
                'success': result == "completed",
                'agents': [agent.to_dict() for agent in session.agents],
                'metrics': session.metrics
            }
            
            # Log analytics hook
            self.logger.debug(f"Session analytics recorded for {session.id}")
            
            # Note: Actual integration with PerformanceMetricsEngine, TrainingEffectivenessTracker,
            # and ProgressTracker would be done here when the analytics system is initialized
            # with the orchestrator. For example:
            # if hasattr(self, 'performance_engine'):
            #     self.performance_engine.record_session_performance(session_data)
            
        except Exception as e:
            self.logger.error(f"Error recording session analytics: {e}")
    
    async def shutdown(self) -> None:
        """Shutdown the training orchestrator and clean up resources."""
        try:
            # Cancel background tasks
            if self.monitor_task:
                self.monitor_task.cancel()
            if self.cleanup_task:
                self.cleanup_task.cancel()
            
            # Cancel all active sessions
            active_session_ids = list(self.active_sessions.keys())
            for session_id in active_session_ids:
                await self.cancel_session(session_id, "system_shutdown")
            
            # Clean up all sessions
            with self.session_lock:
                self.sessions.clear()
                self.active_sessions.clear()
            
            self.logger.info("Training orchestrator shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during orchestrator shutdown: {e}")


# Global training orchestrator instance
_global_orchestrator: Optional[TrainingOrchestrator] = None


def get_training_orchestrator() -> Optional[TrainingOrchestrator]:
    """
    Get the global training orchestrator instance.
    
    Returns:
        Global TrainingOrchestrator instance or None if not initialized
    """
    return _global_orchestrator


def initialize_training_orchestrator(config: FrameworkConfig,
                                   profile_manager: ProfileManager,
                                   tool_registry: ToolRegistry,
                                   communication: CommunicationProtocol,
                                   audit_logger: Optional[AuditLogger] = None) -> TrainingOrchestrator:
    """
    Initialize the global training orchestrator.
    
    Args:
        config: Framework configuration
        profile_manager: Profile manager instance
        tool_registry: Tool registry instance
        communication: Communication protocol instance
        audit_logger: Audit logger instance
        
    Returns:
        Initialized TrainingOrchestrator instance
    """
    global _global_orchestrator
    _global_orchestrator = TrainingOrchestrator(
        config, profile_manager, tool_registry, communication, audit_logger
    )
    return _global_orchestrator


def shutdown_training_orchestrator() -> None:
    """Shutdown the global training orchestrator."""
    global _global_orchestrator
    if _global_orchestrator:
        asyncio.create_task(_global_orchestrator.shutdown())
        _global_orchestrator = None