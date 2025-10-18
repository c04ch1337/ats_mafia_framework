"""
Network Isolation
Manage sandbox network isolation and segmentation.
"""

import docker
import logging
from typing import Dict, List, Optional
from ipaddress import IPv4Network, IPv4Address
import json

logger = logging.getLogger(__name__)


class NetworkIsolation:
    """Manage network isolation for sandbox containers."""
    
    def __init__(self):
        """Initialize network isolation manager."""
        try:
            self.docker_client = docker.from_env()
            self.docker_client.ping()
            self.training_network_name = 'ats-training-network'
            self.isolated_network_name = 'ats-isolated-network'
            logger.info("NetworkIsolation initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize NetworkIsolation: {e}")
            raise RuntimeError(f"Docker not available: {e}")
    
    def create_training_network(self, subnet: str = '172.25.0.0/16') -> str:
        """
        Create isolated Docker network for training.
        
        Args:
            subnet: Network subnet (CIDR notation)
            
        Returns:
            Network ID
        """
        try:
            # Check if network already exists
            try:
                existing_net = self.docker_client.networks.get(self.training_network_name)
                logger.info(f"Training network already exists: {existing_net.id[:12]}")
                return existing_net.id
            except docker.errors.NotFound:
                pass
            
            # Create network
            logger.info(f"Creating training network: {self.training_network_name}")
            
            ipam_pool = docker.types.IPAMPool(subnet=subnet)
            ipam_config = docker.types.IPAMConfig(pool_configs=[ipam_pool])
            
            network = self.docker_client.networks.create(
                name=self.training_network_name,
                driver='bridge',
                ipam=ipam_config,
                options={
                    'com.docker.network.bridge.enable_ip_masquerade': 'false',
                    'com.docker.network.bridge.enable_icc': 'true'
                },
                labels={
                    'ats.mafia.network': 'training',
                    'ats.mafia.isolated': 'true'
                },
                internal=False,  # Allow internet access if needed
                enable_ipv6=False
            )
            
            logger.info(f"Training network created: {network.id[:12]}")
            return network.id
            
        except Exception as e:
            logger.error(f"Failed to create training network: {e}")
            raise RuntimeError(f"Network creation failed: {e}")
    
    def create_isolated_network(self, subnet: str = '172.26.0.0/16') -> str:
        """
        Create fully isolated network (no internet access).
        
        Args:
            subnet: Network subnet (CIDR notation)
            
        Returns:
            Network ID
        """
        try:
            # Check if network already exists
            try:
                existing_net = self.docker_client.networks.get(self.isolated_network_name)
                logger.info(f"Isolated network already exists: {existing_net.id[:12]}")
                return existing_net.id
            except docker.errors.NotFound:
                pass
            
            logger.info(f"Creating isolated network: {self.isolated_network_name}")
            
            ipam_pool = docker.types.IPAMPool(subnet=subnet)
            ipam_config = docker.types.IPAMConfig(pool_configs=[ipam_pool])
            
            network = self.docker_client.networks.create(
                name=self.isolated_network_name,
                driver='bridge',
                ipam=ipam_config,
                internal=True,  # No external access
                labels={
                    'ats.mafia.network': 'isolated',
                    'ats.mafia.isolated': 'true'
                },
                enable_ipv6=False
            )
            
            logger.info(f"Isolated network created: {network.id[:12]}")
            return network.id
            
        except Exception as e:
            logger.error(f"Failed to create isolated network: {e}")
            raise RuntimeError(f"Network creation failed: {e}")
    
    def add_target_machines(
        self,
        network_id: str,
        targets: List[Dict[str, str]]
    ) -> List[str]:
        """
        Add vulnerable VMs/containers as training targets.
        
        Args:
            network_id: Network to add targets to
            targets: List of target configurations
            
        Returns:
            List of container IDs created
        """
        created_containers = []
        
        try:
            network = self.docker_client.networks.get(network_id)
            
            for target in targets:
                name = target.get('name', f"target_{len(created_containers)}")
                image = target.get('image', 'vulnerables/web-dvwa')
                
                logger.info(f"Creating target machine: {name}")
                
                container = self.docker_client.containers.run(
                    image=image,
                    name=f"ats_target_{name}",
                    detach=True,
                    network=network.name,
                    labels={
                        'ats.mafia.type': 'target_machine',
                        'ats.mafia.network': network.name
                    }
                )
                
                created_containers.append(container.id)
                logger.info(f"Target created: {name} ({container.id[:12]})")
            
            return created_containers
            
        except Exception as e:
            logger.error(f"Failed to add target machines: {e}")
            # Clean up any created containers
            for container_id in created_containers:
                try:
                    container = self.docker_client.containers.get(container_id)
                    container.remove(force=True)
                except Exception:
                    pass
            raise RuntimeError(f"Target creation failed: {e}")
    
    def enforce_firewall_rules(self, container_id: str, rules: Optional[List[str]] = None) -> bool:
        """
        Apply iptables firewall rules to container.
        
        Args:
            container_id: Container to apply rules to
            rules: List of iptables rules (optional)
            
        Returns:
            True if rules applied successfully
        """
        try:
            container = self.docker_client.containers.get(container_id)
            
            if rules is None:
                # Default rules: block external network, allow training network
                rules = [
                    # Flush existing rules
                    'iptables -F',
                    # Allow established connections
                    'iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT',
                    # Allow loopback
                    'iptables -A INPUT -i lo -j ACCEPT',
                    # Allow training network (172.25.0.0/16)
                    'iptables -A INPUT -s 172.25.0.0/16 -j ACCEPT',
                    'iptables -A OUTPUT -d 172.25.0.0/16 -j ACCEPT',
                    # Block everything else
                    'iptables -A INPUT -j DROP',
                    'iptables -P FORWARD DROP'
                ]
            
            logger.info(f"Applying firewall rules to container: {container_id[:12]}")
            
            for rule in rules:
                result = container.exec_run(
                    cmd=['bash', '-c', rule],
                    privileged=True
                )
                
                if result.exit_code != 0:
                    logger.error(f"Failed to apply rule: {rule}")
                    logger.error(f"Error: {result.output.decode()}")
                    return False
            
            logger.info("Firewall rules applied successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to enforce firewall rules: {e}")
            return False
    
    def get_network_info(self, network_name: str) -> Dict[str, any]:
        """
        Get information about a network.
        
        Args:
            network_name: Name of network
            
        Returns:
            Dict with network information
        """
        try:
            network = self.docker_client.networks.get(network_name)
            
            # Get connected containers
            containers = []
            for container_id, config in network.attrs.get('Containers', {}).items():
                containers.append({
                    'id': container_id[:12],
                    'name': config.get('Name'),
                    'ipv4': config.get('IPv4Address'),
                    'ipv6': config.get('IPv6Address')
                })
            
            return {
                'id': network.id[:12],
                'name': network.name,
                'driver': network.attrs.get('Driver'),
                'scope': network.attrs.get('Scope'),
                'subnet': network.attrs.get('IPAM', {}).get('Config', [{}])[0].get('Subnet'),
                'gateway': network.attrs.get('IPAM', {}).get('Config', [{}])[0].get('Gateway'),
                'internal': network.attrs.get('Internal', False),
                'containers': containers,
                'labels': network.attrs.get('Labels', {})
            }
            
        except docker.errors.NotFound:
            return {
                'error': 'Network not found',
                'name': network_name
            }
        except Exception as e:
            logger.error(f"Failed to get network info: {e}")
            return {
                'error': str(e),
                'name': network_name
            }
    
    def list_networks(self) -> List[Dict[str, any]]:
        """
        List all ATS MAFIA networks.
        
        Returns:
            List of network information
        """
        try:
            filters = {'label': 'ats.mafia.network'}
            networks = self.docker_client.networks.list(filters=filters)
            
            network_list = []
            for network in networks:
                network_list.append({
                    'id': network.id[:12],
                    'name': network.name,
                    'driver': network.attrs.get('Driver'),
                    'internal': network.attrs.get('Internal', False),
                    'subnet': network.attrs.get('IPAM', {}).get('Config', [{}])[0].get('Subnet'),
                    'container_count': len(network.attrs.get('Containers', {}))
                })
            
            return network_list
            
        except Exception as e:
            logger.error(f"Failed to list networks: {e}")
            return []
    
    def remove_network(self, network_name: str, force: bool = False) -> bool:
        """
        Remove a network.
        
        Args:
            network_name: Name of network to remove
            force: Force removal even if containers attached
            
        Returns:
            True if removed successfully
        """
        try:
            network = self.docker_client.networks.get(network_name)
            
            if force:
                # Disconnect all containers first
                for container_id in network.attrs.get('Containers', {}).keys():
                    try:
                        container = self.docker_client.containers.get(container_id)
                        network.disconnect(container, force=True)
                    except Exception as e:
                        logger.warning(f"Failed to disconnect container: {e}")
            
            network.remove()
            logger.info(f"Network removed: {network_name}")
            return True
            
        except docker.errors.NotFound:
            logger.warning(f"Network not found: {network_name}")
            return False
        except Exception as e:
            logger.error(f"Failed to remove network: {e}")
            return False
    
    def test_connectivity(self, source_container: str, target_ip: str) -> Dict[str, any]:
        """
        Test network connectivity between containers.
        
        Args:
            source_container: Source container ID
            target_ip: Target IP address
            
        Returns:
            Dict with connectivity test results
        """
        try:
            container = self.docker_client.containers.get(source_container)
            
            # Try ping
            result = container.exec_run(
                cmd=['ping', '-c', '3', '-W', '2', target_ip],
                stdout=True,
                stderr=True
            )
            
            success = result.exit_code == 0
            
            return {
                'success': success,
                'source': source_container[:12],
                'target': target_ip,
                'output': result.output.decode(),
                'reachable': success
            }
            
        except Exception as e:
            logger.error(f"Connectivity test failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'source': source_container[:12],
                'target': target_ip,
                'reachable': False
            }
    
    def close(self):
        """Close Docker client connection."""
        if self.docker_client:
            self.docker_client.close()
            logger.info("NetworkIsolation connection closed")


__all__ = ['NetworkIsolation']