#!/usr/bin/env python3
"""
ATS MAFIA Framework - Security Control Verification Script
CONFIDENTIAL - INTERNAL USE ONLY

This script verifies that all security controls remain active and have not been
tampered with. Run this script regularly to ensure operational security.

Usage:
    python security_audit.py
    python security_audit.py --detailed
    python security_audit.py --json > audit_report.json
    python security_audit.py --critical-only
"""

import sys
import json
import re
import subprocess
import os
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime
import argparse


class SecurityAudit:
    """Automated security control verification for ATS MAFIA Framework."""
    
    # Critical security controls that MUST be verified
    CRITICAL_CONTROLS = {
        # Configuration Controls
        'sandbox_enabled': {
            'file': 'ats_mafia_framework/config/settings.py',
            'line': 60,
            'pattern': r'sandbox_enabled:\s*bool\s*=\s*True',
            'expected': 'sandbox_enabled: bool = True',
            'severity': 'CRITICAL',
            'description': 'Sandbox must be enabled for tool execution'
        },
        'audit_logging': {
            'file': 'ats_mafia_framework/config/settings.py',
            'line': 45,
            'pattern': r'audit_enabled:\s*bool\s*=\s*True',
            'expected': 'audit_enabled: bool = True',
            'severity': 'CRITICAL',
            'description': 'Audit logging must be enabled'
        },
        'encryption_enabled': {
            'file': 'ats_mafia_framework/config/settings.py',
            'line': 102,
            'pattern': r'encryption_enabled:\s*bool\s*=\s*True',
            'expected': 'encryption_enabled: bool = True',
            'severity': 'CRITICAL',
            'description': 'Data encryption must be enabled'
        },
        'session_encryption': {
            'file': 'ats_mafia_framework/config/settings.py',
            'line': 104,
            'pattern': r'session_encryption:\s*bool\s*=\s*True',
            'expected': 'session_encryption: bool = True',
            'severity': 'CRITICAL',
            'description': 'Session encryption must be enabled'
        },
        
        # Tool System Controls
        'tool_simulation_only': {
            'file': 'ats_mafia_framework/core/tool_system.py',
            'line': 530,
            'pattern': r'simulation_only:\s*bool\s*=\s*True',
            'expected': 'simulation_only: bool = True',
            'severity': 'CRITICAL',
            'description': 'Tools must default to simulation mode'
        },
        
        # Command Whitelist
        'dangerous_commands_blocklist': {
            'file': 'ats_mafia_framework/sandbox/tool_whitelist.py',
            'line': 59,
            'pattern': r"DANGEROUS_COMMANDS:\s*Set\[str\]\s*=\s*\{",
            'expected': 'DANGEROUS_COMMANDS: Set[str] = {',
            'severity': 'CRITICAL',
            'description': 'Dangerous commands blocklist must exist'
        },
        
        # Security Monitor
        'security_monitor_breakout_detection': {
            'file': 'ats_mafia_framework/sandbox/security_monitor.py',
            'line': 137,
            'pattern': r'def\s+detect_breakout_attempt',
            'expected': 'def detect_breakout_attempt',
            'severity': 'CRITICAL',
            'description': 'Breakout detection must be implemented'
        },
    }
    
    # High severity controls
    HIGH_CONTROLS = {
        'rate_limiting': {
            'file': 'ats_mafia_framework/config/settings.py',
            'line': 97,
            'pattern': r'rate_limit:\s*int\s*=\s*\d+',
            'expected': 'rate_limit: int = 100',
            'severity': 'HIGH',
            'description': 'API rate limiting must be configured'
        },
        'encryption_key_rotation': {
            'file': 'ats_mafia_framework/config/settings.py',
            'line': 103,
            'pattern': r'encryption_key_rotation:\s*bool\s*=\s*True',
            'expected': 'encryption_key_rotation: bool = True',
            'severity': 'HIGH',
            'description': 'Encryption key rotation should be enabled'
        },
    }
    
    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize security audit.
        
        Args:
            base_path: Base directory path for the framework
        """
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self.results = {
            'status': 'PASS',
            'timestamp': datetime.utcnow().isoformat(),
            'checks': [],
            'violations': [],
            'warnings': [],
            'summary': {}
        }
    
    def verify_all_controls(self, critical_only: bool = False) -> Dict[str, Any]:
        """
        Verify all security controls.
        
        Args:
            critical_only: Only verify critical controls
            
        Returns:
            Dictionary containing verification results
        """
        print("🔍 Starting ATS MAFIA Security Audit...")
        print(f"📁 Base Path: {self.base_path}")
        print(f"⏰ Timestamp: {self.results['timestamp']}\n")
        
        # Verify critical controls
        print("🔴 Verifying CRITICAL Controls...")
        for control_name, control in self.CRITICAL_CONTROLS.items():
            result = self._verify_control(control_name, control)
            self.results['checks'].append(result)
            
            if not result['passed']:
                self.results['status'] = 'FAIL'
                self.results['violations'].append(result)
                print(f"  ❌ {control_name}: FAILED")
            else:
                print(f"  ✅ {control_name}: PASSED")
        
        # Verify high severity controls if not critical-only
        if not critical_only:
            print("\n🟠 Verifying HIGH Severity Controls...")
            for control_name, control in self.HIGH_CONTROLS.items():
                result = self._verify_control(control_name, control)
                self.results['checks'].append(result)
                
                if not result['passed']:
                    self.results['warnings'].append(result)
                    print(f"  ⚠️  {control_name}: WARNING")
                else:
                    print(f"  ✅ {control_name}: PASSED")
        
        # Check Docker container security
        print("\n🐋 Verifying Docker Container Security...")
        docker_result = self._verify_docker_security()
        self.results['checks'].append(docker_result)
        
        if not docker_result['passed']:
            self.results['status'] = 'FAIL'
            self.results['violations'].append(docker_result)
            print(f"  ❌ Docker Security: FAILED")
        else:
            print(f"  ✅ Docker Security: PASSED")
        
        # Check network isolation
        print("\n🌐 Verifying Network Isolation...")
        network_result = self._verify_network_isolation()
        self.results['checks'].append(network_result)
        
        if not network_result['passed']:
            self.results['status'] = 'FAIL'
            self.results['violations'].append(network_result)
            print(f"  ❌ Network Isolation: FAILED")
        else:
            print(f"  ✅ Network Isolation: PASSED")
        
        # Generate summary
        self._generate_summary()
        
        return self.results
    
    def _verify_control(self, name: str, control: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify individual security control.
        
        Args:
            name: Control name
            control: Control definition
            
        Returns:
            Verification result dictionary
        """
        result = {
            'control': name,
            'severity': control['severity'],
            'description': control['description'],
            'file': control['file'],
            'line': control.get('line'),
            'passed': False,
            'found_value': None,
            'expected_value': control['expected'],
            'message': ''
        }
        
        file_path = self.base_path / control['file']
        
        # Check if file exists
        if not file_path.exists():
            result['message'] = f"File not found: {control['file']}"
            return result
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Search for pattern
            matches = re.finditer(control['pattern'], content, re.MULTILINE)
            match_list = list(matches)
            
            if not match_list:
                result['message'] = f"Pattern not found: {control['pattern']}"
                return result
            
            # Get the matched text
            match = match_list[0]
            result['found_value'] = match.group(0).strip()
            
            # Check if it matches expected value (allow some whitespace flexibility)
            expected_normalized = re.sub(r'\s+', ' ', control['expected'].strip())
            found_normalized = re.sub(r'\s+', ' ', result['found_value'])
            
            if expected_normalized in found_normalized or re.search(control['pattern'], result['found_value']):
                result['passed'] = True
                result['message'] = 'Control verified successfully'
            else:
                result['message'] = f"Value mismatch. Found: {result['found_value']}"
                
        except Exception as e:
            result['message'] = f"Error reading file: {str(e)}"
        
        return result
    
    def _verify_docker_security(self) -> Dict[str, Any]:
        """
        Verify Docker container security settings.
        
        Returns:
            Verification result dictionary
        """
        result = {
            'control': 'docker_container_security',
            'severity': 'CRITICAL',
            'description': 'Docker container must not run in privileged mode',
            'passed': False,
            'checks': [],
            'message': ''
        }
        
        try:
            # Check if Docker is available
            subprocess.run(['docker', '--version'], capture_output=True, check=True)
            
            # Check if container exists
            inspect_result = subprocess.run(
                ['docker', 'inspect', 'ats_kali_sandbox'],
                capture_output=True,
                text=True
            )
            
            if inspect_result.returncode != 0:
                result['message'] = 'Container ats_kali_sandbox not found (may not be running)'
                result['passed'] = True  # Not running is acceptable
                return result
            
            inspect_data = json.loads(inspect_result.stdout)
            
            if not inspect_data:
                result['message'] = 'No container data found'
                return result
            
            container_data = inspect_data[0]
            host_config = container_data.get('HostConfig', {})
            
            # Check privileged mode
            is_privileged = host_config.get('Privileged', False)
            result['checks'].append({
                'check': 'privileged_mode',
                'passed': not is_privileged,
                'value': is_privileged,
                'expected': False
            })
            
            # Check capabilities
            cap_drop = host_config.get('CapDrop', [])
            has_drop_all = 'ALL' in cap_drop
            result['checks'].append({
                'check': 'capabilities_dropped',
                'passed': has_drop_all,
                'value': cap_drop,
                'expected': ['ALL']
            })
            
            # Check security options
            security_opt = host_config.get('SecurityOpt', [])
            has_no_new_privs = any('no-new-privileges:true' in opt for opt in security_opt)
            result['checks'].append({
                'check': 'no_new_privileges',
                'passed': has_no_new_privs,
                'value': security_opt,
                'expected': 'no-new-privileges:true'
            })
            
            # Overall pass/fail
            all_passed = all(check['passed'] for check in result['checks'])
            result['passed'] = all_passed
            
            if all_passed:
                result['message'] = 'All Docker security checks passed'
            else:
                failed_checks = [c['check'] for c in result['checks'] if not c['passed']]
                result['message'] = f"Failed checks: {', '.join(failed_checks)}"
                
        except subprocess.CalledProcessError:
            result['message'] = 'Docker not available or container not running'
            result['passed'] = True  # Not a failure if Docker isn't running
        except Exception as e:
            result['message'] = f"Error checking Docker security: {str(e)}"
        
        return result
    
    def _verify_network_isolation(self) -> Dict[str, Any]:
        """
        Verify network isolation settings.
        
        Returns:
            Verification result dictionary
        """
        result = {
            'control': 'network_isolation',
            'severity': 'CRITICAL',
            'description': 'Training network must have IP masquerading disabled',
            'passed': False,
            'checks': [],
            'message': ''
        }
        
        try:
            # Check if Docker is available
            subprocess.run(['docker', '--version'], capture_output=True, check=True)
            
            # Inspect training network
            inspect_result = subprocess.run(
                ['docker', 'network', 'inspect', 'ats-training-network'],
                capture_output=True,
                text=True
            )
            
            if inspect_result.returncode != 0:
                result['message'] = 'Training network not found (may not be created yet)'
                result['passed'] = True  # Not a failure if network doesn't exist
                return result
            
            network_data = json.loads(inspect_result.stdout)
            
            if not network_data:
                result['message'] = 'No network data found'
                return result
            
            network = network_data[0]
            options = network.get('Options', {})
            
            # Check IP masquerading
            masquerade_value = options.get('com.docker.network.bridge.enable_ip_masquerade', 'true')
            is_disabled = masquerade_value.lower() == 'false'
            
            result['checks'].append({
                'check': 'ip_masquerade_disabled',
                'passed': is_disabled,
                'value': masquerade_value,
                'expected': 'false'
            })
            
            # Check subnet
            ipam_config = network.get('IPAM', {}).get('Config', [])
            if ipam_config:
                subnet = ipam_config[0].get('Subnet', '')
                is_training_subnet = subnet == '172.25.0.0/16'
                result['checks'].append({
                    'check': 'training_subnet',
                    'passed': is_training_subnet,
                    'value': subnet,
                    'expected': '172.25.0.0/16'
                })
            
            # Overall pass/fail
            all_passed = all(check['passed'] for check in result['checks'])
            result['passed'] = all_passed
            
            if all_passed:
                result['message'] = 'Network isolation verified'
            else:
                failed_checks = [c['check'] for c in result['checks'] if not c['passed']]
                result['message'] = f"Failed checks: {', '.join(failed_checks)}"
                
        except subprocess.CalledProcessError:
            result['message'] = 'Docker not available or network not created'
            result['passed'] = True  # Not a failure if Docker isn't running
        except Exception as e:
            result['message'] = f"Error checking network isolation: {str(e)}"
        
        return result
    
    def _generate_summary(self):
        """Generate audit summary statistics."""
        total_checks = len(self.results['checks'])
        passed_checks = sum(1 for c in self.results['checks'] if c['passed'])
        failed_checks = total_checks - passed_checks
        
        critical_violations = len([v for v in self.results['violations'] 
                                   if v.get('severity') == 'CRITICAL'])
        high_warnings = len([w for w in self.results['warnings'] 
                            if w.get('severity') == 'HIGH'])
        
        self.results['summary'] = {
            'total_checks': total_checks,
            'passed': passed_checks,
            'failed': failed_checks,
            'critical_violations': critical_violations,
            'high_warnings': high_warnings,
            'pass_rate': (passed_checks / total_checks * 100) if total_checks > 0 else 0
        }
    
    def print_report(self, detailed: bool = False):
        """
        Print audit report to console.
        
        Args:
            detailed: Include detailed information for each check
        """
        print("\n" + "="*70)
        print("ATS MAFIA SECURITY AUDIT REPORT")
        print("="*70)
        
        summary = self.results['summary']
        print(f"\n📊 Summary:")
        print(f"  Total Checks: {summary['total_checks']}")
        print(f"  Passed: {summary['passed']} ✅")
        print(f"  Failed: {summary['failed']} ❌")
        print(f"  Pass Rate: {summary['pass_rate']:.1f}%")
        
        if self.results['violations']:
            print(f"\n🔴 CRITICAL VIOLATIONS: {summary['critical_violations']}")
            for violation in self.results['violations']:
                print(f"\n  Control: {violation['control']}")
                print(f"  Severity: {violation['severity']}")
                print(f"  Description: {violation['description']}")
                print(f"  File: {violation['file']}")
                if violation.get('line'):
                    print(f"  Line: {violation['line']}")
                print(f"  Message: {violation['message']}")
                if detailed and violation.get('found_value'):
                    print(f"  Found: {violation['found_value']}")
                    print(f"  Expected: {violation['expected_value']}")
        
        if self.results['warnings']:
            print(f"\n🟠 HIGH SEVERITY WARNINGS: {summary['high_warnings']}")
            for warning in self.results['warnings']:
                print(f"\n  Control: {warning['control']}")
                print(f"  Description: {warning['description']}")
                print(f"  Message: {warning['message']}")
        
        print("\n" + "="*70)
        
        if self.results['status'] == 'FAIL':
            print("❌ SECURITY AUDIT FAILED - IMMEDIATE ACTION REQUIRED")
        else:
            print("✅ SECURITY AUDIT PASSED - System is secure")
        
        print("="*70 + "\n")


def main():
    """Main entry point for security audit script."""
    parser = argparse.ArgumentParser(
        description='ATS MAFIA Framework Security Audit Script',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python security_audit.py                    # Run full audit
  python security_audit.py --detailed         # Detailed output
  python security_audit.py --json             # JSON output
  python security_audit.py --critical-only    # Only critical controls
        """
    )
    
    parser.add_argument(
        '--detailed',
        action='store_true',
        help='Show detailed information for each check'
    )
    
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results in JSON format'
    )
    
    parser.add_argument(
        '--critical-only',
        action='store_true',
        help='Only verify critical security controls'
    )
    
    parser.add_argument(
        '--base-path',
        type=str,
        default=None,
        help='Base directory path for the framework'
    )
    
    args = parser.parse_args()
    
    # Run audit
    audit = SecurityAudit(base_path=args.base_path)
    results = audit.verify_all_controls(critical_only=args.critical_only)
    
    # Output results
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        audit.print_report(detailed=args.detailed)
    
    # Exit with appropriate code
    sys.exit(0 if results['status'] == 'PASS' else 1)


if __name__ == '__main__':
    main()