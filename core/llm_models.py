"""
ATS MAFIA Framework LLM Model Selection System

This module provides comprehensive LLM model management including model registry,
intelligent selection, load balancing, and task-based optimization.
"""

import logging
import threading
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict, field
from enum import Enum
from datetime import datetime, timezone
import random


class ModelTier(Enum):
    """Model capability and cost tiers."""
    ENTRY = "entry"
    STANDARD = "standard"
    ADVANCED = "advanced"
    PREMIUM = "premium"


class ModelCapability(Enum):
    """Model capabilities and strengths."""
    REASONING = "reasoning"
    SPEED = "speed"
    COST_EFFICIENT = "cost_efficient"
    CREATIVE = "creative"
    ANALYTICAL = "analytical"
    VISION = "vision"
    FUNCTION_CALLING = "function_calling"
    JSON_MODE = "json_mode"
    STREAMING = "streaming"


@dataclass
class LLMModel:
    """
    LLM model definition with comprehensive metadata.
    
    Attributes:
        name: Model identifier (e.g., "gpt-4o")
        provider: Provider name (e.g., "openai", "anthropic")
        display_name: Human-readable name
        tier: Model tier (entry, standard, advanced, premium)
        capabilities: List of model capabilities
        cost_per_1k_input_tokens: Cost per 1000 input tokens in USD
        cost_per_1k_output_tokens: Cost per 1000 output tokens in USD
        context_window: Maximum context window in tokens
        reasoning_score: Reasoning capability score (0.0-1.0)
        speed_score: Speed/latency score (0.0-1.0)
        recommended_for: Task types this model excels at
        max_requests_per_minute: Rate limit if known
    """
    name: str
    provider: str
    display_name: str
    tier: ModelTier
    capabilities: List[ModelCapability]
    cost_per_1k_input_tokens: float
    cost_per_1k_output_tokens: float
    context_window: int
    reasoning_score: float
    speed_score: float
    recommended_for: List[str] = field(default_factory=list)
    max_requests_per_minute: Optional[int] = None
    
    def __post_init__(self):
        """Validate model data."""
        if not 0.0 <= self.reasoning_score <= 1.0:
            raise ValueError("reasoning_score must be between 0.0 and 1.0")
        if not 0.0 <= self.speed_score <= 1.0:
            raise ValueError("speed_score must be between 0.0 and 1.0")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            'name': self.name,
            'provider': self.provider,
            'display_name': self.display_name,
            'tier': self.tier.value,
            'capabilities': [cap.value for cap in self.capabilities],
            'cost_per_1k_input_tokens': self.cost_per_1k_input_tokens,
            'cost_per_1k_output_tokens': self.cost_per_1k_output_tokens,
            'context_window': self.context_window,
            'reasoning_score': self.reasoning_score,
            'speed_score': self.speed_score,
            'recommended_for': self.recommended_for,
            'max_requests_per_minute': self.max_requests_per_minute
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LLMModel':
        """Create model from dictionary."""
        data['tier'] = ModelTier(data['tier'])
        data['capabilities'] = [ModelCapability(cap) for cap in data['capabilities']]
        return cls(**data)
    
    def get_full_name(self) -> str:
        """Get full model identifier (provider/name)."""
        return f"{self.provider}/{self.name}"
    
    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate cost for given token usage.
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Total cost in USD
        """
        input_cost = (input_tokens / 1000) * self.cost_per_1k_input_tokens
        output_cost = (output_tokens / 1000) * self.cost_per_1k_output_tokens
        return input_cost + output_cost


class ModelRegistry:
    """
    Centralized registry for all available LLM models.
    
    Maintains a database of models with their capabilities, costs, and
    performance characteristics. Supports filtering and recommendation.
    """
    
    def __init__(self):
        """Initialize the model registry."""
        self.models: Dict[str, LLMModel] = {}
        self.lock = threading.RLock()
        self.logger = logging.getLogger("model_registry")
        
        # Load default models
        self._load_default_models()
    
    def _load_default_models(self) -> None:
        """Load default OpenRouter and major provider models."""
        default_models = [
            # OpenAI Models
            LLMModel(
                name="gpt-4o",
                provider="openai",
                display_name="GPT-4o",
                tier=ModelTier.ADVANCED,
                capabilities=[ModelCapability.REASONING, ModelCapability.VISION, 
                            ModelCapability.FUNCTION_CALLING, ModelCapability.SPEED],
                cost_per_1k_input_tokens=0.0025,
                cost_per_1k_output_tokens=0.01,
                context_window=128000,
                reasoning_score=0.92,
                speed_score=0.88,
                recommended_for=["reconnaissance", "analysis", "exploitation"]
            ),
            LLMModel(
                name="gpt-4o-mini",
                provider="openai",
                display_name="GPT-4o Mini",
                tier=ModelTier.STANDARD,
                capabilities=[ModelCapability.SPEED, ModelCapability.COST_EFFICIENT,
                            ModelCapability.VISION, ModelCapability.FUNCTION_CALLING],
                cost_per_1k_input_tokens=0.00015,
                cost_per_1k_output_tokens=0.0006,
                context_window=128000,
                reasoning_score=0.82,
                speed_score=0.95,
                recommended_for=["reconnaissance", "social_engineering"]
            ),
            LLMModel(
                name="gpt-4-turbo",
                provider="openai",
                display_name="GPT-4 Turbo",
                tier=ModelTier.PREMIUM,
                capabilities=[ModelCapability.REASONING, ModelCapability.VISION,
                            ModelCapability.FUNCTION_CALLING, ModelCapability.JSON_MODE],
                cost_per_1k_input_tokens=0.01,
                cost_per_1k_output_tokens=0.03,
                context_window=128000,
                reasoning_score=0.94,
                speed_score=0.75,
                recommended_for=["analysis", "defense", "exploitation"]
            ),
            
            # Anthropic Models
            LLMModel(
                name="claude-3.5-sonnet",
                provider="anthropic",
                display_name="Claude 3.5 Sonnet",
                tier=ModelTier.PREMIUM,
                capabilities=[ModelCapability.REASONING, ModelCapability.ANALYTICAL,
                            ModelCapability.VISION, ModelCapability.FUNCTION_CALLING],
                cost_per_1k_input_tokens=0.003,
                cost_per_1k_output_tokens=0.015,
                context_window=200000,
                reasoning_score=0.96,
                speed_score=0.85,
                recommended_for=["exploitation", "analysis", "defense"]
            ),
            LLMModel(
                name="claude-3.5-haiku",
                provider="anthropic",
                display_name="Claude 3.5 Haiku",
                tier=ModelTier.STANDARD,
                capabilities=[ModelCapability.SPEED, ModelCapability.COST_EFFICIENT,
                            ModelCapability.VISION],
                cost_per_1k_input_tokens=0.00025,
                cost_per_1k_output_tokens=0.00125,
                context_window=200000,
                reasoning_score=0.84,
                speed_score=0.96,
                recommended_for=["reconnaissance", "social_engineering"]
            ),
            LLMModel(
                name="claude-3-opus",
                provider="anthropic",
                display_name="Claude 3 Opus",
                tier=ModelTier.PREMIUM,
                capabilities=[ModelCapability.REASONING, ModelCapability.ANALYTICAL,
                            ModelCapability.VISION, ModelCapability.CREATIVE],
                cost_per_1k_input_tokens=0.015,
                cost_per_1k_output_tokens=0.075,
                context_window=200000,
                reasoning_score=0.98,
                speed_score=0.65,
                recommended_for=["analysis", "defense", "exploitation"]
            ),
            
            # Google Models
            LLMModel(
                name="gemini-1.5-pro",
                provider="google",
                display_name="Gemini 1.5 Pro",
                tier=ModelTier.ADVANCED,
                capabilities=[ModelCapability.REASONING, ModelCapability.VISION,
                            ModelCapability.FUNCTION_CALLING],
                cost_per_1k_input_tokens=0.00125,
                cost_per_1k_output_tokens=0.005,
                context_window=2000000,
                reasoning_score=0.90,
                speed_score=0.82,
                recommended_for=["analysis", "reconnaissance"]
            ),
            LLMModel(
                name="gemini-1.5-flash",
                provider="google",
                display_name="Gemini 1.5 Flash",
                tier=ModelTier.STANDARD,
                capabilities=[ModelCapability.SPEED, ModelCapability.COST_EFFICIENT,
                            ModelCapability.VISION],
                cost_per_1k_input_tokens=0.000075,
                cost_per_1k_output_tokens=0.0003,
                context_window=1000000,
                reasoning_score=0.80,
                speed_score=0.98,
                recommended_for=["reconnaissance", "social_engineering"]
            ),
            
            # DeepSeek Models
            LLMModel(
                name="deepseek-chat",
                provider="deepseek",
                display_name="DeepSeek Chat",
                tier=ModelTier.STANDARD,
                capabilities=[ModelCapability.COST_EFFICIENT, ModelCapability.REASONING],
                cost_per_1k_input_tokens=0.00027,
                cost_per_1k_output_tokens=0.0011,
                context_window=64000,
                reasoning_score=0.86,
                speed_score=0.85,
                recommended_for=["reconnaissance", "exploitation"]
            ),
            
            # Groq Models (Ultra-fast)
            LLMModel(
                name="llama-3.1-70b",
                provider="groq",
                display_name="Llama 3.1 70B (Groq)",
                tier=ModelTier.ENTRY,
                capabilities=[ModelCapability.SPEED, ModelCapability.COST_EFFICIENT],
                cost_per_1k_input_tokens=0.00059,
                cost_per_1k_output_tokens=0.00079,
                context_window=8000,
                reasoning_score=0.78,
                speed_score=0.99,
                recommended_for=["reconnaissance", "social_engineering"],
                max_requests_per_minute=30
            ),
            
            # OpenRouter aggregated models
            LLMModel(
                name="openai/gpt-4o",
                provider="openrouter",
                display_name="GPT-4o (OpenRouter)",
                tier=ModelTier.ADVANCED,
                capabilities=[ModelCapability.REASONING, ModelCapability.VISION,
                            ModelCapability.FUNCTION_CALLING],
                cost_per_1k_input_tokens=0.0025,
                cost_per_1k_output_tokens=0.01,
                context_window=128000,
                reasoning_score=0.92,
                speed_score=0.88,
                recommended_for=["reconnaissance", "analysis", "exploitation"]
            ),
            LLMModel(
                name="anthropic/claude-3.5-sonnet",
                provider="openrouter",
                display_name="Claude 3.5 Sonnet (OpenRouter)",
                tier=ModelTier.PREMIUM,
                capabilities=[ModelCapability.REASONING, ModelCapability.ANALYTICAL,
                            ModelCapability.VISION],
                cost_per_1k_input_tokens=0.003,
                cost_per_1k_output_tokens=0.015,
                context_window=200000,
                reasoning_score=0.96,
                speed_score=0.85,
                recommended_for=["exploitation", "analysis", "defense"]
            ),
            LLMModel(
                name="google/gemini-1.5-flash",
                provider="openrouter",
                display_name="Gemini 1.5 Flash (OpenRouter)",
                tier=ModelTier.STANDARD,
                capabilities=[ModelCapability.SPEED, ModelCapability.COST_EFFICIENT],
                cost_per_1k_input_tokens=0.000075,
                cost_per_1k_output_tokens=0.0003,
                context_window=1000000,
                reasoning_score=0.80,
                speed_score=0.98,
                recommended_for=["reconnaissance", "social_engineering"]
            ),
            
            # Mistral Models
            LLMModel(
                name="mistral-large",
                provider="mistral",
                display_name="Mistral Large",
                tier=ModelTier.ADVANCED,
                capabilities=[ModelCapability.REASONING, ModelCapability.FUNCTION_CALLING],
                cost_per_1k_input_tokens=0.002,
                cost_per_1k_output_tokens=0.006,
                context_window=128000,
                reasoning_score=0.88,
                speed_score=0.87,
                recommended_for=["analysis", "exploitation"]
            ),
            
            # Local Models (via Ollama)
            LLMModel(
                name="llama3.1:8b",
                provider="ollama",
                display_name="Llama 3.1 8B (Local)",
                tier=ModelTier.ENTRY,
                capabilities=[ModelCapability.COST_EFFICIENT, ModelCapability.SPEED],
                cost_per_1k_input_tokens=0.0,
                cost_per_1k_output_tokens=0.0,
                context_window=8000,
                reasoning_score=0.70,
                speed_score=0.85,
                recommended_for=["reconnaissance", "social_engineering"]
            ),
        ]
        
        for model in default_models:
            self.register_model(model)
        
        self.logger.info(f"Loaded {len(default_models)} default models")
    
    def register_model(self, model: LLMModel) -> None:
        """
        Register a new model in the registry.
        
        Args:
            model: Model to register
        """
        with self.lock:
            full_name = model.get_full_name()
            self.models[full_name] = model
            self.logger.debug(f"Registered model: {full_name}")
    
    def unregister_model(self, provider: str, name: str) -> bool:
        """
        Unregister a model from the registry.
        
        Args:
            provider: Model provider
            name: Model name
            
        Returns:
            True if model was unregistered, False if not found
        """
        with self.lock:
            full_name = f"{provider}/{name}"
            if full_name in self.models:
                del self.models[full_name]
                self.logger.debug(f"Unregistered model: {full_name}")
                return True
            return False
    
    def get_model(self, provider: str, name: str) -> Optional[LLMModel]:
        """
        Get a specific model by provider and name.
        
        Args:
            provider: Model provider
            name: Model name
            
        Returns:
            Model instance or None if not found
        """
        with self.lock:
            full_name = f"{provider}/{name}"
            return self.models.get(full_name)
    
    def list_models(self,
                   provider: Optional[str] = None,
                   tier: Optional[ModelTier] = None,
                   capability: Optional[ModelCapability] = None,
                   max_cost_per_1k: Optional[float] = None) -> List[LLMModel]:
        """
        List models with optional filtering.
        
        Args:
            provider: Filter by provider
            tier: Filter by tier
            capability: Filter by capability
            max_cost_per_1k: Maximum cost per 1k input tokens
            
        Returns:
            List of matching models
        """
        with self.lock:
            models = list(self.models.values())
            
            if provider:
                models = [m for m in models if m.provider == provider]
            
            if tier:
                models = [m for m in models if m.tier == tier]
            
            if capability:
                models = [m for m in models if capability in m.capabilities]
            
            if max_cost_per_1k is not None:
                models = [m for m in models if m.cost_per_1k_input_tokens <= max_cost_per_1k]
            
            return models
    
    def get_recommended_models(self,
                              task_type: str,
                              tier: Optional[ModelTier] = None,
                              max_cost_per_request: Optional[float] = None) -> List[LLMModel]:
        """
        Get models recommended for a specific task type.
        
        Args:
            task_type: Type of task (reconnaissance, exploitation, etc.)
            tier: Optional tier filter
            max_cost_per_request: Maximum cost per request
            
        Returns:
            List of recommended models sorted by suitability
        """
        with self.lock:
            models = [
                m for m in self.models.values()
                if task_type in m.recommended_for
            ]
            
            if tier:
                models = [m for m in models if m.tier == tier]
            
            if max_cost_per_request is not None:
                # Estimate tokens (rough approximation)
                est_input_tokens = 2000
                est_output_tokens = 500
                models = [
                    m for m in models
                    if m.calculate_cost(est_input_tokens, est_output_tokens) <= max_cost_per_request
                ]
            
            # Sort by reasoning score (higher is better)
            models.sort(key=lambda m: m.reasoning_score, reverse=True)
            
            return models
    
    def get_cheapest_model(self, capability: Optional[ModelCapability] = None) -> Optional[LLMModel]:
        """
        Get the cheapest available model.
        
        Args:
            capability: Optional capability requirement
            
        Returns:
            Cheapest model or None
        """
        with self.lock:
            models = list(self.models.values())
            
            if capability:
                models = [m for m in models if capability in m.capabilities]
            
            if not models:
                return None
            
            return min(models, key=lambda m: m.cost_per_1k_input_tokens)
    
    def get_fastest_model(self, tier: Optional[ModelTier] = None) -> Optional[LLMModel]:
        """
        Get the fastest available model.
        
        Args:
            tier: Optional tier filter
            
        Returns:
            Fastest model or None
        """
        with self.lock:
            models = list(self.models.values())
            
            if tier:
                models = [m for m in models if m.tier == tier]
            
            if not models:
                return None
            
            return max(models, key=lambda m: m.speed_score)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get registry statistics.
        
        Returns:
            Dictionary with statistics
        """
        with self.lock:
            models_by_provider = {}
            models_by_tier = {}
            
            for model in self.models.values():
                # Count by provider
                models_by_provider[model.provider] = models_by_provider.get(model.provider, 0) + 1
                
                # Count by tier
                tier_name = model.tier.value
                models_by_tier[tier_name] = models_by_tier.get(tier_name, 0) + 1
            
            return {
                'total_models': len(self.models),
                'models_by_provider': models_by_provider,
                'models_by_tier': models_by_tier,
                'providers': list(models_by_provider.keys())
            }


class ModelSelector:
    """
    Intelligent model selection based on task requirements.
    
    Selects optimal models based on task type, cost constraints,
    performance requirements, and profile preferences.
    """
    
    def __init__(self, registry: ModelRegistry):
        """
        Initialize the model selector.
        
        Args:
            registry: Model registry instance
        """
        self.registry = registry
        self.logger = logging.getLogger("model_selector")
    
    def select_model(self,
                    task_type: str,
                    profile_config: Optional[Dict[str, Any]] = None,
                    max_cost_per_request: Optional[float] = None,
                    preferred_tier: Optional[ModelTier] = None,
                    required_capabilities: Optional[List[ModelCapability]] = None) -> Optional[LLMModel]:
        """
        Select the optimal model for a task.
        
        Args:
            task_type: Type of task (reconnaissance, exploitation, etc.)
            profile_config: Profile LLM configuration
            max_cost_per_request: Maximum cost per request
            preferred_tier: Preferred model tier
            required_capabilities: Required capabilities
            
        Returns:
            Selected model or None if no suitable model found
        """
        # Check for profile-specific configuration
        if profile_config:
            primary_model = profile_config.get('primary_model')
            if primary_model:
                model = self.registry.get_model(
                    primary_model.get('provider'),
                    primary_model.get('model')
                )
                if model:
                    self.logger.debug(f"Using profile-configured model: {model.get_full_name()}")
                    return model
        
        # Get recommended models for task
        candidates = self.registry.get_recommended_models(
            task_type=task_type,
            tier=preferred_tier,
            max_cost_per_request=max_cost_per_request
        )
        
        # Filter by required capabilities
        if required_capabilities:
            candidates = [
                m for m in candidates
                if all(cap in m.capabilities for cap in required_capabilities)
            ]
        
        if not candidates:
            self.logger.warning(f"No suitable model found for task: {task_type}")
            return None
        
        # Return best match (already sorted by reasoning score)
        selected = candidates[0]
        self.logger.info(f"Selected model {selected.get_full_name()} for task {task_type}")
        return selected
    
    def select_fallback_model(self,
                             current_model: LLMModel,
                             reason: str = "error") -> Optional[LLMModel]:
        """
        Select a fallback model when current model fails.
        
        Args:
            current_model: The model that failed
            reason: Reason for fallback (error, rate_limit, etc.)
            
        Returns:
            Fallback model or None
        """
        # Get models of same tier or lower
        candidates = self.registry.list_models(tier=current_model.tier)
        
        # Remove the current model
        candidates = [m for m in candidates if m.get_full_name() != current_model.get_full_name()]
        
        if not candidates:
            # Try cheaper tier
            if current_model.tier == ModelTier.PREMIUM:
                candidates = self.registry.list_models(tier=ModelTier.ADVANCED)
            elif current_model.tier == ModelTier.ADVANCED:
                candidates = self.registry.list_models(tier=ModelTier.STANDARD)
            elif current_model.tier == ModelTier.STANDARD:
                candidates = self.registry.list_models(tier=ModelTier.ENTRY)
        
        if not candidates:
            return None
        
        # Select cheapest option
        fallback = min(candidates, key=lambda m: m.cost_per_1k_input_tokens)
        self.logger.info(f"Selected fallback model: {fallback.get_full_name()} (reason: {reason})")
        return fallback


class ModelLoadBalancer:
    """
    Load balancer for distributing requests across multiple models.
    
    Supports round-robin, weighted, and least-cost distribution strategies.
    """
    
    def __init__(self, models: List[LLMModel], strategy: str = "round_robin"):
        """
        Initialize the load balancer.
        
        Args:
            models: List of models to balance across
            strategy: Load balancing strategy (round_robin, weighted, least_cost)
        """
        self.models = models
        self.strategy = strategy
        self.current_index = 0
        self.request_counts: Dict[str, int] = {m.get_full_name(): 0 for m in models}
        self.lock = threading.Lock()
        self.logger = logging.getLogger("model_load_balancer")
    
    def select_next_model(self) -> Optional[LLMModel]:
        """
        Select the next model based on load balancing strategy.
        
        Returns:
            Next model to use or None if no models available
        """
        with self.lock:
            if not self.models:
                return None
            
            if self.strategy == "round_robin":
                model = self.models[self.current_index]
                self.current_index = (self.current_index + 1) % len(self.models)
                
            elif self.strategy == "weighted":
                # Weight by inverse cost (cheaper models get more requests)
                weights = [1.0 / (m.cost_per_1k_input_tokens + 0.001) for m in self.models]
                model = random.choices(self.models, weights=weights)[0]
                
            elif self.strategy == "least_cost":
                model = min(self.models, key=lambda m: m.cost_per_1k_input_tokens)
                
            else:
                model = self.models[0]
            
            # Track request
            self.request_counts[model.get_full_name()] += 1
            
            return model
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get load balancer statistics.
        
        Returns:
            Dictionary with statistics
        """
        with self.lock:
            total_requests = sum(self.request_counts.values())
            
            return {
                'strategy': self.strategy,
                'total_models': len(self.models),
                'total_requests': total_requests,
                'requests_per_model': self.request_counts.copy()
            }