"""Container Pool Configuration Manager"""

from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class ContainerConfig:
    """Configuration for individual container."""
    name: str
    priority: int = 5
    required: bool = False
    estimated_startup_time: int = 10
    pool_strategy: str = "cold"
    auto_restart: bool = False

@dataclass
class PoolConfig:
    """Configuration for container pool."""
    name: str
    description: str
    containers: List[ContainerConfig]
    auto_start: bool = False
    auto_restart: bool = False
    ttl_seconds: Optional[int] = None
    health_check_interval: int = 60
    auto_stop_idle: bool = False
    max_startup_time: Optional[int] = None
    auto_stop_after_seconds: Optional[int] = None

@dataclass
class ProfileMapping:
    """Profile to container mapping."""
    profile_id: str
    primary: str
    secondary: List[str]
    pool_strategy: str

class ContainerPoolConfig:
    """Load and manage container pool configuration."""
    
    def __init__(self, config_path: Optional[Path] = None):
        if config_path is None:
            config_path = Path(__file__).parent / "container_pools.yaml"
        self.config_path = config_path
        self.config_data: Dict[str, Any] = {}
        self.pools: Dict[str, PoolConfig] = {}
        self.profile_mappings: Dict[str, ProfileMapping] = {}
        self.orchestration_config: Dict[str, Any] = {}
        
    def load(self) -> None:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                self.config_data = yaml.safe_load(f)
            
            # Parse pools
            for pool_name, pool_data in self.config_data.get('pools', {}).items():
                containers = [
                    ContainerConfig(**c) if isinstance(c, dict) else ContainerConfig(name=c)
                    for c in pool_data.get('containers', [])
                ]
                self.pools[pool_name] = PoolConfig(
                    name=pool_name,
                    description=pool_data.get('description', ''),
                    containers=containers,
                    **{k: v for k, v in pool_data.items() if k not in ['containers', 'description', 'name']}
                )
            
            # Parse profile mappings
            for profile_id, mapping in self.config_data.get('profile_mappings', {}).items():
                self.profile_mappings[profile_id] = ProfileMapping(
                    profile_id=profile_id,
                    primary=mapping['primary'],
                    secondary=mapping.get('secondary', []),
                    pool_strategy=mapping.get('pool_strategy', 'cold')
                )
            
            # Parse orchestration config
            self.orchestration_config = self.config_data.get('orchestration', {})
            
            logger.info(f"Loaded container pool configuration: {len(self.pools)} pools, {len(self.profile_mappings)} profiles")
            
        except Exception as e:
            logger.error(f"Failed to load container pool config: {e}")
            raise
    
    def get_pool(self, pool_name: str) -> Optional[PoolConfig]:
        """Get pool configuration by name."""
        return self.pools.get(pool_name)
    
    def get_hot_pool(self) -> Optional[PoolConfig]:
        """Get hot pool configuration."""
        return self.get_pool('hot')
    
    def get_warm_pool(self) -> Optional[PoolConfig]:
        """Get warm pool configuration."""
        return self.get_pool('warm')
    
    def get_cold_pool(self) -> Optional[PoolConfig]:
        """Get cold pool configuration."""
        return self.get_pool('cold')
    
    def get_profile_mapping(self, profile_id: str) -> Optional[ProfileMapping]:
        """Get container mapping for profile."""
        return self.profile_mappings.get(profile_id)
    
    def get_containers_for_profile(self, profile_id: str) -> List[str]:
        """Get list of containers needed for profile."""
        mapping = self.get_profile_mapping(profile_id)
        if not mapping:
            return []
        return [mapping.primary] + mapping.secondary
    
    def get_orchestration_setting(self, key: str, default: Any = None) -> Any:
        """Get orchestration configuration setting."""
        return self.orchestration_config.get(key, default)


# Global instance
_pool_config: Optional[ContainerPoolConfig] = None

def get_pool_config() -> ContainerPoolConfig:
    """Get global pool configuration instance."""
    global _pool_config
    if _pool_config is None:
        _pool_config = ContainerPoolConfig()
        _pool_config.load()
    return _pool_config

def reload_pool_config() -> None:
    """Reload pool configuration from disk."""
    global _pool_config
    _pool_config = None
    get_pool_config()