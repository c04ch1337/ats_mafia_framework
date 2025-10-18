"""
Comprehensive tests for Kali Linux Sandbox Integration
Tests all sandbox components including security controls and tool execution.
"""

import pytest
import docker
import time
from unittest.mock import Mock, patch, MagicMock
import json

from ..sandbox.kali_connector import (
    KaliConnector,
    KaliConnectorError,
    ContainerNotFoundError,
    CommandValidationError
)
from ..sandbox.sandbox_manager import SandboxManager
from ..sandbox.security_monitor import SecurityMonitor
from ..sandbox.network_isolation import NetworkIsolation
from ..sandbox.tool_whitelist import (
    validate_command,
    is_tool_approved,
    get_all_approved_tools,
    sanitize_command,
    build_safe_command
)


class TestToolWhitelist:
    """Test tool whitelist and command validation."""
    
    def test_approved_tool_check(self):
        """Test if tools are correctly identified as approved."""
        assert is_tool_approved('nmap') == True
        assert is_tool_approved('metasploit') == False  # msfconsole is approved
        assert is_tool_approved('msfconsole') == True
        assert is_tool_approved('fake_tool') == False
    
    def test_get_all_approved_tools(self):
        """Test retrieval of all approved tools."""
        tools = get_all_approved_tools()
        assert isinstance(tools, list)
        assert len(tools) > 50  # Should have many tools
        assert 'nmap' in tools
        assert 'sqlmap' in tools
        assert 'hydra' in tools
    
    def test_validate_safe_command(self):
        """Test validation of safe commands."""
        # Safe nmap command
        is_valid, reason = validate_command('nmap -sS 192.168.1.10')
        assert is_valid == True
        
        # Safe sqlmap command
        is_valid, reason = validate_command('sqlmap -u http://test.local --batch')
        assert is_valid == True
    
    def test_validate_dangerous_command(self):
        """Test rejection of dangerous commands."""
        # Destructive command
        is_valid, reason = validate_command('rm -rf /')
        assert is_valid == False
        assert 'dangerous' in reason.lower() or 'rm' in reason.lower()
        
        # Docker socket access
        is_valid, reason = validate_command('ls /var/run/docker.sock')
        assert is_valid == False
        
        # Command injection
        is_valid, reason = validate_command('nmap 192.168.1.1 && cat /etc/passwd')
        assert is_valid == False
    
    def test_validate_unapproved_tool(self):
        """Test rejection of unapproved tools."""
        is_valid, reason = validate_command('fake_tool --exploit')
        assert is_valid == False
        assert 'not in approved whitelist' in reason.lower()
    
    def test_sanitize_command(self):
        """Test command sanitization."""
        # Remove dangerous characters
        sanitized = sanitize_command('nmap; cat /etc/passwd')
        assert ';' not in sanitized
        
        sanitized = sanitize_command('nmap && rm -rf /')
        assert '&&' not in sanitized
    
    def test_build_safe_command(self):
        """Test building safe commands."""
        # Valid command
        cmd, is_safe = build_safe_command(
            tool='nmap',
            target='192.168.1.10',
            options={'-p': '80,443', '-sS': ''}
        )
        assert is_safe == True
        assert 'nmap' in cmd
        assert '192.168.1.10' in cmd
        
        # Invalid tool
        cmd, is_safe = build_safe_command(
            tool='fake_tool',
            target='192.168.1.10'
        )
        assert is_safe == False


class TestSecurityMonitor:
    """Test security monitoring functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.monitor = SecurityMonitor()
    
    def test_monitor_safe_command(self):
        """Test monitoring of safe commands."""
        result = self.monitor.monitor_command(
            user_id='test_user',
            command='nmap -sS 192.168.1.10',
            container_id='test_container'
        )
        assert result['allowed'] == True
        assert result['threat_level'] in ['LOW', 'MEDIUM']
    
    def test_monitor_breakout_attempt(self):
        """Test detection of container breakout attempts."""
        # Docker socket access
        result = self.monitor.monitor_command(
            user_id='test_user',
            command='ls /var/run/docker.sock',
            container_id='test_container'
        )
        assert result['allowed'] == False
        assert result['threat_level'] == 'CRITICAL'
        
        # Namespace manipulation
        result = self.monitor.monitor_command(
            user_id='test_user',
            command='nsenter --target 1 --mount',
            container_id='test_container'
        )
        assert result['allowed'] == False
    
    def test_detect_breakout_indicators(self):
        """Test breakout indicator detection."""
        assert self.monitor.detect_breakout_attempt('docker ps') == True
        assert self.monitor.detect_breakout_attempt('nsenter -t 1') == True
        assert self.monitor.detect_breakout_attempt('/proc/1/root') == True
        assert self.monitor.detect_breakout_attempt('nmap -sS 192.168.1.10') == False
    
    def test_rate_limiting(self):
        """Test rate limiting functionality."""
        user_id = 'rate_test_user'
        
        # First 100 commands should succeed
        for i in range(100):
            result = self.monitor.rate_limit_check(user_id)
            assert result['allowed'] == True
        
        # 101st command should be rate limited
        result = self.monitor.rate_limit_check(user_id)
        assert result['allowed'] == False
        assert 'rate limit exceeded' in result['reason'].lower()
    
    def test_user_blocking(self):
        """Test user blocking after violations."""
        user_id = 'blocked_test_user'
        
        # Trigger breakout attempt
        self.monitor.monitor_command(
            user_id=user_id,
            command='docker ps',
            container_id='test'
        )
        
        # User should be blocked
        assert user_id in self.monitor.blocked_users
        
        # Subsequent commands should be blocked
        result = self.monitor.monitor_command(
            user_id=user_id,
            command='nmap -sS 192.168.1.10',
            container_id='test'
        )
        assert result['allowed'] == False
        assert 'blocked' in result['reason'].lower()
    
    def test_user_unblocking(self):
        """Test user unblocking functionality."""
        user_id = 'unblock_test_user'
        
        # Block user
        self.monitor.blocked_users.add(user_id)
        assert user_id in self.monitor.blocked_users
        
        # Unblock user
        success = self.monitor.unblock_user(user_id)
        assert success == True
        assert user_id not in self.monitor.blocked_users
    
    def test_audit_logging(self):
        """Test audit log functionality."""
        user_id = 'audit_test_user'
        
        # Execute some commands
        self.monitor.monitor_command(
            user_id=user_id,
            command='nmap -sS 192.168.1.10',
            container_id='test'
        )
        
        # Retrieve audit log
        logs = self.monitor.get_audit_log(user_id=user_id, limit=10)
        assert len(logs) > 0
        assert any(log.get('user_id') == user_id for log in logs)
    
    def test_security_report(self):
        """Test security report generation."""
        report = self.monitor.get_security_report()
        
        assert 'total_events' in report
        assert 'threats_by_type' in report
        assert 'blocked_users_count' in report
        assert isinstance(report['threats_by_type'], dict)


@pytest.mark.skipif(
    not pytest.importorskip("docker"),
    reason="Docker not available"
)
class TestKaliConnector:
    """Test Kali connector functionality."""
    
    @pytest.fixture
    def mock_docker_client(self):
        """Mock Docker client for testing."""
        with patch('docker.from_env') as mock:
            client = MagicMock()
            client.ping.return_value = True
            
            container = MagicMock()
            container.status = 'running'
            container.id = 'test_container_id'
            container.exec_run.return_value = MagicMock(
                exit_code=0,
                output=(b'test output', b'')
            )
            
            client.containers.get.return_value = container
            mock.return_value = client
            
            yield mock
    
    def test_connector_initialization(self, mock_docker_client):
        """Test connector initialization."""
        connector = KaliConnector()
        assert connector.container_name == 'ats_kali_sandbox'
        assert connector.docker_client is not None
    
    def test_command_execution(self, mock_docker_client):
        """Test command execution."""
        connector = KaliConnector()
        
        result = connector.execute_command('echo test', timeout=10)
        
        assert 'success' in result
        assert 'stdout' in result
        assert 'stderr' in result
        assert 'exit_code' in result
        assert 'execution_time' in result
    
    def test_command_validation_rejection(self, mock_docker_client):
        """Test command validation rejection."""
        connector = KaliConnector()
        
        with pytest.raises(CommandValidationError):
            connector.execute_command('rm -rf /', timeout=10)
    
    def test_container_status(self, mock_docker_client):
        """Test getting container status."""
        connector = KaliConnector()
        
        status = connector.get_container_status()
        
        assert 'available' in status
        assert 'status' in status or 'error' in status


@pytest.mark.skipif(
    not pytest.importorskip("docker"),
    reason="Docker not available"
)
class TestSandboxManager:
    """Test sandbox manager functionality."""
    
    @pytest.fixture
    def mock_docker_client(self):
        """Mock Docker client for testing."""
        with patch('docker.from_env') as mock:
            client = MagicMock()
            client.ping.return_value = True
            
            container = MagicMock()
            container.id = 'test_container_id'
            container.status = 'running'
            container.name = 'test_container'
            
            client.containers.create.return_value = container
            client.containers.get.return_value = container
            client.containers.list.return_value = [container]
            
            mock.return_value = client
            
            yield mock
    
    def test_manager_initialization(self, mock_docker_client):
        """Test manager initialization."""
        manager = SandboxManager()
        assert manager.base_image == 'kalilinux/kali-rolling:latest'
        assert manager.docker_client is not None
    
    def test_list_sandboxes(self, mock_docker_client):
        """Test listing sandboxes."""
        manager = SandboxManager()
        
        sandboxes = manager.list_sandboxes()
        
        assert isinstance(sandboxes, list)


@pytest.mark.skipif(
    not pytest.importorskip("docker"),
    reason="Docker not available"
)
class TestNetworkIsolation:
    """Test network isolation functionality."""
    
    @pytest.fixture
    def mock_docker_client(self):
        """Mock Docker client for testing."""
        with patch('docker.from_env') as mock:
            client = MagicMock()
            client.ping.return_value = True
            
            network = MagicMock()
            network.id = 'test_network_id'
            network.name = 'test_network'
            
            client.networks.create.return_value = network
            client.networks.get.return_value = network
            client.networks.list.return_value = [network]
            
            mock.return_value = client
            
            yield mock
    
    def test_network_initialization(self, mock_docker_client):
        """Test network isolation initialization."""
        isolation = NetworkIsolation()
        assert isolation.training_network_name == 'ats-training-network'
        assert isolation.docker_client is not None
    
    def test_list_networks(self, mock_docker_client):
        """Test listing networks."""
        isolation = NetworkIsolation()
        
        networks = isolation.list_networks()
        
        assert isinstance(networks, list)


class TestRemoteTools:
    """Test remote tool adapters."""
    
    def test_nmap_tool_initialization(self):
        """Test nmap tool initialization."""
        from ..tools.remote.nmap_remote import NmapRemoteTool
        
        tool = NmapRemoteTool()
        assert tool.name == 'nmap_remote'
        assert tool.requires_sandbox == True
    
    def test_sqlmap_tool_initialization(self):
        """Test sqlmap tool initialization."""
        from ..tools.remote.sqlmap_remote import SqlmapRemoteTool
        
        tool = SqlmapRemoteTool()
        assert tool.name == 'sqlmap_remote'
        assert tool.requires_sandbox == True
    
    def test_hydra_tool_initialization(self):
        """Test hydra tool initialization."""
        from ..tools.remote.hydra_remote import HydraRemoteTool
        
        tool = HydraRemoteTool()
        assert tool.name == 'hydra_remote'
        assert tool.requires_sandbox == True


class TestIntegration:
    """Integration tests for complete sandbox workflow."""
    
    def test_complete_workflow_mock(self):
        """Test complete workflow with mocked components."""
        # Initialize components
        monitor = SecurityMonitor()
        
        # Step 1: Validate command
        is_valid, reason = validate_command('nmap -sS 192.168.1.10')
        assert is_valid == True
        
        # Step 2: Security monitoring
        result = monitor.monitor_command(
            user_id='integration_test',
            command='nmap -sS 192.168.1.10',
            container_id='test_container'
        )
        assert result['allowed'] == True
        
        # Step 3: Check audit log
        logs = monitor.get_audit_log(user_id='integration_test')
        assert len(logs) > 0
    
    def test_security_violation_workflow(self):
        """Test workflow when security violation occurs."""
        monitor = SecurityMonitor()
        
        # Attempt dangerous command
        result = monitor.monitor_command(
            user_id='violation_test',
            command='docker ps',
            container_id='test'
        )
        
        # Should be blocked
        assert result['allowed'] == False
        assert result['threat_level'] == 'CRITICAL'
        
        # User should be blocked
        assert 'violation_test' in monitor.blocked_users
        
        # Subsequent commands should fail
        result = monitor.monitor_command(
            user_id='violation_test',
            command='nmap -sS 192.168.1.10',
            container_id='test'
        )
        assert result['allowed'] == False


# Performance tests
class TestPerformance:
    """Performance and load tests."""
    
    def test_command_validation_performance(self):
        """Test command validation performance."""
        start_time = time.time()
        
        for i in range(1000):
            validate_command(f'nmap -sS 192.168.1.{i % 255}')
        
        elapsed = time.time() - start_time
        
        # Should validate 1000 commands in under 1 second
        assert elapsed < 1.0
    
    def test_rate_limiter_performance(self):
        """Test rate limiter performance."""
        monitor = SecurityMonitor()
        
        start_time = time.time()
        
        for i in range(100):
            monitor.rate_limit_check(f'perf_test_user_{i}')
        
        elapsed = time.time() - start_time
        
        # Should handle 100 rate limit checks quickly
        assert elapsed < 1.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])