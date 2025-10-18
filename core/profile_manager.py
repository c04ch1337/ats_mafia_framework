"""
ATS MAFIA Framework Profile Management System

This module provides the profile management infrastructure for the ATS MAFIA framework.
It handles agent profile creation, loading, validation, caching, and lifecycle management.
"""

import os
import json
import yaml
import uuid
import time
import threading
from typing import Dict, Any, Optional, List, Union, Type
from dataclasses import dataclass, asdict, field
from enum import Enum
from pathlib import Path
from abc import ABC, abstractmethod
import logging
import hashlib
import pickle
from datetime import datetime, timezone

from ..config.settings import FrameworkConfig
from .logging import AuditLogger, AuditEventType, SecurityLevel


class ProfileType(Enum):
    """Types of agent profiles."""
    RED_TEAM = "red_team"
    BLUE_TEAM = "blue_team"
    SOCIAL_ENGINEER = "social_engineer"
    PENETRATION_TESTER = "penetration_tester"
    SECURITY_ANALYST = "security_analyst"
    INCIDENT_RESPONDER = "incident_responder"
    THREAT_HUNTER = "threat_hunter"
    MALWARE_ANALYST = "malware_analyst"
    CUSTOM = "custom"


class ProfileStatus(Enum):
    """Status of profiles in the system."""
    LOADING = "loading"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    UNLOADED = "unloaded"


class SkillLevel(Enum):
    """Skill levels for agent capabilities."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"
    MASTER = "master"


@dataclass
class Capability:
    """Agent capability definition."""
    name: str
    description: str
    skill_level: SkillLevel
    tools_required: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert capability to dictionary."""
        data = asdict(self)
        data['skill_level'] = self.skill_level.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Capability':
        """Create capability from dictionary."""
        data['skill_level'] = SkillLevel(data['skill_level'])
        return cls(**data)


@dataclass
class PersonalityTrait:
    """Personality trait for agent profiles."""
    trait: str
    value: float  # 0.0 to 1.0
    description: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert trait to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PersonalityTrait':
        """Create trait from dictionary."""
        return cls(**data)


@dataclass
class ProfileMetadata:
    """Metadata for agent profiles."""
    id: str
    name: str
    description: str
    version: str
    author: str
    profile_type: ProfileType
    category: str
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    file_path: Optional[str] = None
    checksum: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    compatibility: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary."""
        data = asdict(self)
        data['profile_type'] = self.profile_type.value
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProfileMetadata':
        """Create metadata from dictionary."""
        data['profile_type'] = ProfileType(data['profile_type'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**data)


@dataclass
class AgentProfile:
    """Complete agent profile definition."""
    metadata: ProfileMetadata
    capabilities: List[Capability] = field(default_factory=list)
    personality: List[PersonalityTrait] = field(default_factory=list)
    knowledge_base: Dict[str, Any] = field(default_factory=dict)
    behavior_settings: Dict[str, Any] = field(default_factory=dict)
    communication_style: Dict[str, Any] = field(default_factory=dict)
    learning_parameters: Dict[str, Any] = field(default_factory=dict)
    security_settings: Dict[str, Any] = field(default_factory=dict)
    custom_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary."""
        return {
            'metadata': self.metadata.to_dict(),
            'capabilities': [cap.to_dict() for cap in self.capabilities],
            'personality': [trait.to_dict() for trait in self.personality],
            'knowledge_base': self.knowledge_base,
            'behavior_settings': self.behavior_settings,
            'communication_style': self.communication_style,
            'learning_parameters': self.learning_parameters,
            'security_settings': self.security_settings,
            'custom_data': self.custom_data
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentProfile':
        """Create profile from dictionary."""
        return cls(
            metadata=ProfileMetadata.from_dict(data['metadata']),
            capabilities=[Capability.from_dict(cap) for cap in data.get('capabilities', [])],
            personality=[PersonalityTrait.from_dict(trait) for trait in data.get('personality', [])],
            knowledge_base=data.get('knowledge_base', {}),
            behavior_settings=data.get('behavior_settings', {}),
            communication_style=data.get('communication_style', {}),
            learning_parameters=data.get('learning_parameters', {}),
            security_settings=data.get('security_settings', {}),
            custom_data=data.get('custom_data', {})
        )
    
    def calculate_checksum(self) -> str:
        """Calculate checksum for the profile."""
        profile_data = self.to_dict()
        profile_json = json.dumps(profile_data, sort_keys=True)
        return hashlib.sha256(profile_json.encode()).hexdigest()


class ProfileValidator:
    """Validator for agent profiles."""
    
    def __init__(self):
        """Initialize the profile validator."""
        self.logger = logging.getLogger("profile_validator")
    
    def validate(self, profile: AgentProfile) -> List[str]:
        """
        Validate an agent profile.
        
        Args:
            profile: Profile to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Validate metadata
        errors.extend(self._validate_metadata(profile.metadata))
        
        # Validate capabilities
        errors.extend(self._validate_capabilities(profile.capabilities))
        
        # Validate personality traits
        errors.extend(self._validate_personality(profile.personality))
        
        # Validate other sections
        errors.extend(self._validate_knowledge_base(profile.knowledge_base))
        errors.extend(self._validate_behavior_settings(profile.behavior_settings))
        errors.extend(self._validate_learning_parameters(profile.learning_parameters))
        errors.extend(self._validate_security_settings(profile.security_settings))
        
        return errors
    
    def _validate_metadata(self, metadata: ProfileMetadata) -> List[str]:
        """Validate profile metadata."""
        errors = []
        
        if not metadata.id or not metadata.id.strip():
            errors.append("Profile ID is required")
        
        if not metadata.name or not metadata.name.strip():
            errors.append("Profile name is required")
        
        if not metadata.description or not metadata.description.strip():
            errors.append("Profile description is required")
        
        if not metadata.version or not metadata.version.strip():
            errors.append("Profile version is required")
        
        if not metadata.author or not metadata.author.strip():
            errors.append("Profile author is required")
        
        if not isinstance(metadata.profile_type, ProfileType):
            errors.append("Invalid profile type")
        
        if not isinstance(metadata.tags, list):
            errors.append("Tags must be a list")
        
        return errors
    
    def _validate_capabilities(self, capabilities: List[Capability]) -> List[str]:
        """Validate capabilities."""
        errors = []
        
        capability_names = set()
        
        for i, cap in enumerate(capabilities):
            if not cap.name or not cap.name.strip():
                errors.append(f"Capability {i}: Name is required")
                continue
            
            if cap.name in capability_names:
                errors.append(f"Duplicate capability name: {cap.name}")
            else:
                capability_names.add(cap.name)
            
            if not cap.description or not cap.description.strip():
                errors.append(f"Capability {cap.name}: Description is required")
            
            if not isinstance(cap.skill_level, SkillLevel):
                errors.append(f"Capability {cap.name}: Invalid skill level")
            
            if not isinstance(cap.tools_required, list):
                errors.append(f"Capability {cap.name}: Tools required must be a list")
            
            if not isinstance(cap.prerequisites, list):
                errors.append(f"Capability {cap.name}: Prerequisites must be a list")
        
        return errors
    
    def _validate_personality(self, personality: List[PersonalityTrait]) -> List[str]:
        """Validate personality traits."""
        errors = []
        
        trait_names = set()
        
        for i, trait in enumerate(personality):
            if not trait.trait or not trait.trait.strip():
                errors.append(f"Personality trait {i}: Trait name is required")
                continue
            
            if trait.trait in trait_names:
                errors.append(f"Duplicate personality trait: {trait.trait}")
            else:
                trait_names.add(trait.trait)
            
            if not isinstance(trait.value, (int, float)) or not (0.0 <= trait.value <= 1.0):
                errors.append(f"Personality trait {trait.trait}: Value must be between 0.0 and 1.0")
            
            if not trait.description or not trait.description.strip():
                errors.append(f"Personality trait {trait.trait}: Description is required")
        
        return errors
    
    def _validate_knowledge_base(self, knowledge_base: Dict[str, Any]) -> List[str]:
        """Validate knowledge base."""
        errors = []
        
        if not isinstance(knowledge_base, dict):
            errors.append("Knowledge base must be a dictionary")
        
        return errors
    
    def _validate_behavior_settings(self, behavior_settings: Dict[str, Any]) -> List[str]:
        """Validate behavior settings."""
        errors = []
        
        if not isinstance(behavior_settings, dict):
            errors.append("Behavior settings must be a dictionary")
        
        return errors
    
    def _validate_learning_parameters(self, learning_parameters: Dict[str, Any]) -> List[str]:
        """Validate learning parameters."""
        errors = []
        
        if not isinstance(learning_parameters, dict):
            errors.append("Learning parameters must be a dictionary")
        
        return errors
    
    def _validate_security_settings(self, security_settings: Dict[str, Any]) -> List[str]:
        """Validate security settings."""
        errors = []
        
        if not isinstance(security_settings, dict):
            errors.append("Security settings must be a dictionary")
        
        return errors


class ProfileCache:
    """Cache for agent profiles."""
    
    def __init__(self, max_size: int = 100, ttl: int = 3600):
        """
        Initialize the profile cache.
        
        Args:
            max_size: Maximum number of profiles to cache
            ttl: Time to live for cached profiles (seconds)
        """
        self.max_size = max_size
        self.ttl = ttl
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.access_times: Dict[str, float] = {}
        self.lock = threading.RLock()
    
    def get(self, profile_id: str) -> Optional[AgentProfile]:
        """
        Get a profile from cache.
        
        Args:
            profile_id: ID of the profile
            
        Returns:
            Cached profile or None if not found/expired
        """
        with self.lock:
            if profile_id not in self.cache:
                return None
            
            cache_entry = self.cache[profile_id]
            current_time = time.time()
            
            # Check if expired
            if current_time - cache_entry['timestamp'] > self.ttl:
                del self.cache[profile_id]
                del self.access_times[profile_id]
                return None
            
            # Update access time
            self.access_times[profile_id] = current_time
            return cache_entry['profile']
    
    def put(self, profile: AgentProfile) -> None:
        """
        Put a profile in cache.
        
        Args:
            profile: Profile to cache
        """
        with self.lock:
            profile_id = profile.metadata.id
            current_time = time.time()
            
            # Remove oldest entry if cache is full
            if len(self.cache) >= self.max_size and profile_id not in self.cache:
                oldest_id = min(self.access_times.keys(), key=lambda k: self.access_times[k])
                del self.cache[oldest_id]
                del self.access_times[oldest_id]
            
            # Add to cache
            self.cache[profile_id] = {
                'profile': profile,
                'timestamp': current_time
            }
            self.access_times[profile_id] = current_time
    
    def invalidate(self, profile_id: str) -> None:
        """
        Invalidate a cached profile.
        
        Args:
            profile_id: ID of the profile to invalidate
        """
        with self.lock:
            self.cache.pop(profile_id, None)
            self.access_times.pop(profile_id, None)
    
    def clear(self) -> None:
        """Clear all cached profiles."""
        with self.lock:
            self.cache.clear()
            self.access_times.clear()
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary containing cache statistics
        """
        with self.lock:
            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'ttl': self.ttl,
                'hit_rate': getattr(self, '_hit_rate', 0.0)
            }


class ProfileManager:
    """
    Profile management system for ATS MAFIA framework.
    
    Handles profile loading, caching, validation, and lifecycle management.
    """
    
    def __init__(self, 
                 config: FrameworkConfig,
                 audit_logger: Optional[AuditLogger] = None):
        """
        Initialize the profile manager.
        
        Args:
            config: Framework configuration
            audit_logger: Audit logger instance
        """
        self.config = config
        self.audit_logger = audit_logger
        self.logger = logging.getLogger("profile_manager")
        
        # Profile storage
        self.profiles: Dict[str, AgentProfile] = {}
        self.profile_metadata: Dict[str, ProfileMetadata] = {}
        
        # Components
        self.validator = ProfileValidator()
        self.cache = ProfileCache(
            max_size=self.config.cache_size,
            ttl=3600  # 1 hour
        ) if self.config.cache_enabled else None
        
        # Thread safety
        self.lock = threading.RLock()
        
        # Statistics
        self.stats = {
            'profiles_loaded': 0,
            'profiles_validated': 0,
            'validation_errors': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
        
        # Load profiles from default path
        self._load_profiles_from_directory(self.config.default_profile_path)
    
    def _load_profiles_from_directory(self, directory: str) -> None:
        """
        Load profiles from a directory.
        
        Args:
            directory: Directory to load profiles from
        """
        profile_dir = Path(directory)
        
        if not profile_dir.exists():
            self.logger.warning(f"Profile directory does not exist: {directory}")
            return
        
        # Look for profile files
        for profile_file in profile_dir.glob("**/*.json"):
            try:
                self.load_profile_from_file(str(profile_file))
            except Exception as e:
                self.logger.error(f"Error loading profile from {profile_file}: {e}")
        
        # Also look for YAML files
        for profile_file in profile_dir.glob("**/*.yaml"):
            try:
                self.load_profile_from_file(str(profile_file))
            except Exception as e:
                self.logger.error(f"Error loading profile from {profile_file}: {e}")
    
    def load_profile_from_file(self, file_path: str) -> bool:
        """
        Load a profile from a file.
        
        Args:
            file_path: Path to the profile file
            
        Returns:
            True if profile loaded successfully, False otherwise
        """
        try:
            profile_path = Path(file_path)
            
            if not profile_path.exists():
                self.logger.error(f"Profile file not found: {file_path}")
                return False
            
            # Load profile data
            with open(profile_path, 'r', encoding='utf-8') as f:
                if profile_path.suffix.lower() == '.json':
                    profile_data = json.load(f)
                elif profile_path.suffix.lower() in ['.yaml', '.yml']:
                    profile_data = yaml.safe_load(f)
                else:
                    self.logger.error(f"Unsupported profile file format: {profile_path.suffix}")
                    return False
            
            # Create profile
            profile = AgentProfile.from_dict(profile_data)
            
            # Set file path and calculate checksum
            profile.metadata.file_path = file_path
            profile.metadata.checksum = profile.calculate_checksum()
            
            # Validate profile
            if self.config.validation_enabled:
                errors = self.validator.validate(profile)
                if errors:
                    self.logger.error(f"Profile validation failed for {profile.metadata.id}: {errors}")
                    self.stats['validation_errors'] += 1
                    
                    if self.audit_logger:
                        self.audit_logger.audit(
                            event_type=AuditEventType.SYSTEM_EVENT,
                            action="profile_validation_failed",
                            details={
                                'profile_id': profile.metadata.id,
                                'file_path': file_path,
                                'errors': errors
                            },
                            security_level=SecurityLevel.MEDIUM
                        )
                    
                    return False
                else:
                    self.stats['profiles_validated'] += 1
            
            # Register profile
            self.register_profile(profile)
            
            self.stats['profiles_loaded'] += 1
            
            if self.audit_logger:
                self.audit_logger.audit(
                    event_type=AuditEventType.SYSTEM_EVENT,
                    action="profile_loaded",
                    details={
                        'profile_id': profile.metadata.id,
                        'file_path': file_path,
                        'profile_type': profile.metadata.profile_type.value
                    },
                    security_level=SecurityLevel.LOW
                )
            
            self.logger.info(f"Loaded profile: {profile.metadata.id} from {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading profile from {file_path}: {e}")
            return False
    
    def register_profile(self, profile: AgentProfile) -> None:
        """
        Register a profile in the manager.
        
        Args:
            profile: Profile to register
        """
        with self.lock:
            self.profiles[profile.metadata.id] = profile
            self.profile_metadata[profile.metadata.id] = profile.metadata
            
            # Cache the profile if caching is enabled
            if self.cache:
                self.cache.put(profile)
    
    def unregister_profile(self, profile_id: str) -> bool:
        """
        Unregister a profile.
        
        Args:
            profile_id: ID of the profile to unregister
            
        Returns:
            True if profile was unregistered, False if not found
        """
        with self.lock:
            if profile_id in self.profiles:
                profile = self.profiles[profile_id]
                
                del self.profiles[profile_id]
                del self.profile_metadata[profile_id]
                
                # Remove from cache
                if self.cache:
                    self.cache.invalidate(profile_id)
                
                if self.audit_logger:
                    self.audit_logger.audit(
                        event_type=AuditEventType.SYSTEM_EVENT,
                        action="profile_unregistered",
                        details={'profile_id': profile_id},
                        security_level=SecurityLevel.LOW
                    )
                
                self.logger.info(f"Unregistered profile: {profile_id}")
                return True
            
            return False
    
    def get_profile(self, profile_id: str) -> Optional[AgentProfile]:
        """
        Get a profile by ID.
        
        Args:
            profile_id: ID of the profile
            
        Returns:
            Profile instance or None if not found
        """
        with self.lock:
            # Try cache first
            if self.cache:
                cached_profile = self.cache.get(profile_id)
                if cached_profile:
                    self.stats['cache_hits'] += 1
                    return cached_profile
                else:
                    self.stats['cache_misses'] += 1
            
            # Get from storage
            return self.profiles.get(profile_id)
    
    def get_profile_metadata(self, profile_id: str) -> Optional[ProfileMetadata]:
        """
        Get profile metadata by ID.
        
        Args:
            profile_id: ID of the profile
            
        Returns:
            Profile metadata or None if not found
        """
        with self.lock:
            return self.profile_metadata.get(profile_id)
    
    def list_profiles(self,
                     profile_type: Optional[ProfileType] = None,
                     category: Optional[str] = None,
                     tags: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        List profiles with optional filtering.
        
        Args:
            profile_type: Filter by profile type
            category: Filter by category
            tags: Filter by tags (profile must have at least one of these tags)
            
        Returns:
            List of profile metadata dictionaries
        """
        with self.lock:
            profiles = []
            
            for metadata in self.profile_metadata.values():
                # Apply filters
                if profile_type and metadata.profile_type != profile_type:
                    continue
                
                if category and metadata.category != category:
                    continue
                
                if tags and not any(tag in metadata.tags for tag in tags):
                    continue
                
                profiles.append(metadata.to_dict())
            
            return profiles
    
    def search_profiles(self, query: str) -> List[Dict[str, Any]]:
        """
        Search profiles by query string.
        
        Args:
            query: Search query
            
        Returns:
            List of matching profile metadata dictionaries
        """
        with self.lock:
            profiles = []
            query_lower = query.lower()
            
            for metadata in self.profile_metadata.values():
                # Search in name, description, and tags
                searchable_text = [
                    metadata.name.lower(),
                    metadata.description.lower(),
                    metadata.category.lower(),
                    *[tag.lower() for tag in metadata.tags]
                ]
                
                if any(query_lower in text for text in searchable_text):
                    profiles.append(metadata.to_dict())
            
            return profiles
    
    def validate_profile(self, profile: AgentProfile) -> List[str]:
        """
        Validate a profile.
        
        Args:
            profile: Profile to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        return self.validator.validate(profile)
    
    def save_profile(self, profile: AgentProfile, file_path: Optional[str] = None) -> bool:
        """
        Save a profile to a file.
        
        Args:
            profile: Profile to save
            file_path: Path to save to (default: profile's file path)
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            save_path = file_path or profile.metadata.file_path
            
            if not save_path:
                self.logger.error("No file path specified for saving profile")
                return False
            
            # Update metadata
            profile.metadata.updated_at = datetime.now(timezone.utc)
            profile.metadata.checksum = profile.calculate_checksum()
            
            # Save to file
            profile_path = Path(save_path)
            profile_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(profile_path, 'w', encoding='utf-8') as f:
                if profile_path.suffix.lower() == '.json':
                    json.dump(profile.to_dict(), f, indent=2)
                elif profile_path.suffix.lower() in ['.yaml', '.yml']:
                    yaml.dump(profile.to_dict(), f, default_flow_style=False)
                else:
                    self.logger.error(f"Unsupported file format: {profile_path.suffix}")
                    return False
            
            # Update profile metadata
            profile.metadata.file_path = save_path
            
            # Re-register profile
            self.register_profile(profile)
            
            if self.audit_logger:
                self.audit_logger.audit(
                    event_type=AuditEventType.SYSTEM_EVENT,
                    action="profile_saved",
                    details={
                        'profile_id': profile.metadata.id,
                        'file_path': save_path
                    },
                    security_level=SecurityLevel.LOW
                )
            
            self.logger.info(f"Saved profile: {profile.metadata.id} to {save_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving profile {profile.metadata.id}: {e}")
            return False
    
    def create_profile(self,
                      name: str,
                      description: str,
                      profile_type: ProfileType,
                      author: str,
                      category: str = "general",
                      **kwargs) -> AgentProfile:
        """
        Create a new profile.
        
        Args:
            name: Profile name
            description: Profile description
            profile_type: Type of profile
            author: Profile author
            category: Profile category
            **kwargs: Additional metadata fields
            
        Returns:
            Created profile
        """
        # Create metadata
        metadata = ProfileMetadata(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            version="1.0.0",
            author=author,
            profile_type=profile_type,
            category=category,
            tags=kwargs.get('tags', []),
            dependencies=kwargs.get('dependencies', []),
            compatibility=kwargs.get('compatibility', [])
        )
        
        # Create profile
        profile = AgentProfile(
            metadata=metadata,
            capabilities=kwargs.get('capabilities', []),
            personality=kwargs.get('personality', []),
            knowledge_base=kwargs.get('knowledge_base', {}),
            behavior_settings=kwargs.get('behavior_settings', {}),
            communication_style=kwargs.get('communication_style', {}),
            learning_parameters=kwargs.get('learning_parameters', {}),
            security_settings=kwargs.get('security_settings', {}),
            custom_data=kwargs.get('custom_data', {})
        )
        
        # Register profile
        self.register_profile(profile)
        
        if self.audit_logger:
            self.audit_logger.audit(
                event_type=AuditEventType.SYSTEM_EVENT,
                action="profile_created",
                details={
                    'profile_id': profile.metadata.id,
                    'name': name,
                    'type': profile_type.value
                },
                security_level=SecurityLevel.LOW
            )
        
        self.logger.info(f"Created new profile: {profile.metadata.id}")
        return profile
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get profile manager statistics.
        
        Returns:
            Dictionary containing statistics
        """
        with self.lock:
            profiles_by_type = {}
            profiles_by_category = {}
            
            for metadata in self.profile_metadata.values():
                # Count by type
                profile_type = metadata.profile_type.value
                profiles_by_type[profile_type] = profiles_by_type.get(profile_type, 0) + 1
                
                # Count by category
                category = metadata.category
                profiles_by_category[category] = profiles_by_category.get(category, 0) + 1
            
            stats = {
                'total_profiles': len(self.profiles),
                'profiles_by_type': profiles_by_type,
                'profiles_by_category': profiles_by_category,
                **self.stats
            }
            
            # Add cache statistics if caching is enabled
            if self.cache:
                stats['cache'] = self.cache.get_statistics()
            
            return stats
    
    def shutdown(self) -> None:
        """Shutdown the profile manager and clean up resources."""
        with self.lock:
            # Clear cache
            if self.cache:
                self.cache.clear()
            
            # Clear profiles
            self.profiles.clear()
            self.profile_metadata.clear()
            
            self.logger.info("Profile manager shutdown complete")


# Global profile manager instance
_global_profile_manager: Optional[ProfileManager] = None


def get_profile_manager() -> Optional[ProfileManager]:
    """
    Get the global profile manager instance.
    
    Returns:
        Global ProfileManager instance or None if not initialized
    """
    return _global_profile_manager


def initialize_profile_manager(config: FrameworkConfig,
                              audit_logger: Optional[AuditLogger] = None) -> ProfileManager:
    """
    Initialize the global profile manager.
    
    Args:
        config: Framework configuration
        audit_logger: Audit logger instance
        
    Returns:
        Initialized ProfileManager instance
    """
    global _global_profile_manager
    _global_profile_manager = ProfileManager(config, audit_logger)
    return _global_profile_manager


def shutdown_profile_manager() -> None:
    """Shutdown the global profile manager."""
    global _global_profile_manager
    if _global_profile_manager:
        _global_profile_manager.shutdown()
        _global_profile_manager = None