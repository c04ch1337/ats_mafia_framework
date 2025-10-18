#!/usr/bin/env python3
"""
ATS MAFIA Framework - File Integrity Monitoring
CONFIDENTIAL - INTERNAL USE ONLY

This script uses SHA-256 hashes to detect unauthorized modifications to 
security-critical files. It creates a baseline and verifies against it.

Usage:
    python tamper_detection.py --create-baseline    # Create initial baseline
    python tamper_detection.py                      # Verify against baseline
    python tamper_detection.py --json               # JSON output
    python tamper_detection.py --update-baseline    # Update baseline
"""

import sys
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Set, Optional, Any
from datetime import datetime
import argparse


class TamperDetection:
    """File integrity monitoring for ATS MAFIA Framework security-critical files."""
    
    # Security-critical files that must be monitored
    SECURITY_CRITICAL_FILES = [
        # Configuration
        'ats_mafia_framework/config/settings.py',
        'ats_mafia_framework/config/__init__.py',
        'ats_mafia_framework/config/loader.py',
        'ats_mafia_framework/config/validator.py',
        
        # Core Security
        'ats_mafia_framework/core/tool_system.py',
        'ats_mafia_framework/core/logging.py',
        
        # Sandbox Security
        'ats_mafia_framework/sandbox/tool_whitelist.py',
        'ats_mafia_framework/sandbox/security_monitor.py',
        'ats_mafia_framework/sandbox/sandbox_manager.py',
        'ats_mafia_framework/sandbox/network_isolation.py',
        'ats_mafia_framework/sandbox/kali_connector.py',
        
        # Docker Configuration
        'docker-compose.yml',
        
        # Security Scripts
        'ats_mafia_framework/scripts/security_audit.py',
        'ats_mafia_framework/scripts/tamper_detection.py',
        
        # Security Documentation
        'ATS_MAFIA_SECURITY_CONTROL_MATRIX.md',
    ]
    
    def __init__(self, baseline_file: str = 'security_baseline.json', base_path: Optional[str] = None):
        """
        Initialize tamper detection.
        
        Args:
            baseline_file: Path to baseline file
            base_path: Base directory path for the framework
        """
        self.baseline_file = baseline_file
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self.baseline = {}
        self.current_hashes = {}
    
    def calculate_file_hash(self, file_path: Path) -> Optional[str]:
        """
        Calculate SHA-256 hash of a file.
        
        Args:
            file_path: Path to file
            
        Returns:
            Hex digest of SHA-256 hash or None if file doesn't exist
        """
        if not file_path.exists():
            return None
        
        try:
            sha256_hash = hashlib.sha256()
            
            with open(file_path, 'rb') as f:
                # Read file in chunks for memory efficiency
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            
            return sha256_hash.hexdigest()
            
        except Exception as e:
            print(f"Error calculating hash for {file_path}: {e}", file=sys.stderr)
            return None
    
    def create_baseline(self) -> Dict[str, Any]:
        """
        Create security baseline with file hashes.
        
        Returns:
            Dictionary containing baseline information
        """
        print("🔐 Creating security baseline...")
        
        baseline = {
            'created': datetime.utcnow().isoformat(),
            'files': {},
            'total_files': 0,
            'missing_files': []
        }
        
        for file_path_str in self.SECURITY_CRITICAL_FILES:
            file_path = self.base_path / file_path_str
            
            print(f"  Hashing: {file_path_str}...", end='')
            
            file_hash = self.calculate_file_hash(file_path)
            
            if file_hash:
                baseline['files'][file_path_str] = {
                    'hash': file_hash,
                    'size': file_path.stat().st_size,
                    'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                }
                baseline['total_files'] += 1
                print(" ✅")
            else:
                baseline['missing_files'].append(file_path_str)
                print(" ⚠️  (not found)")
        
        # Save baseline
        baseline_path = self.base_path / self.baseline_file
        with open(baseline_path, 'w') as f:
            json.dump(baseline, f, indent=2)
        
        print(f"\n✅ Baseline created: {baseline_path}")
        print(f"   Files monitored: {baseline['total_files']}")
        if baseline['missing_files']:
            print(f"   Missing files: {len(baseline['missing_files'])}")
        
        return baseline
    
    def load_baseline(self) -> bool:
        """
        Load baseline from file.
        
        Returns:
            True if baseline loaded successfully
        """
        baseline_path = self.base_path / self.baseline_file
        
        if not baseline_path.exists():
            print(f"❌ Baseline file not found: {baseline_path}", file=sys.stderr)
            print("   Run with --create-baseline to create initial baseline", file=sys.stderr)
            return False
        
        try:
            with open(baseline_path, 'r') as f:
                self.baseline = json.load(f)
            
            print(f"📁 Loaded baseline from: {baseline_path}")
            print(f"   Created: {self.baseline.get('created', 'Unknown')}")
            print(f"   Files: {self.baseline.get('total_files', 0)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error loading baseline: {e}", file=sys.stderr)
            return False
    
    def verify_integrity(self) -> Dict[str, Any]:
        """
        Verify file integrity against baseline.
        
        Returns:
            Dictionary containing verification results
        """
        if not self.baseline:
            raise ValueError("No baseline loaded. Load baseline first.")
        
        print("\n🔍 Verifying file integrity...")
        
        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'baseline_date': self.baseline.get('created'),
            'status': 'CLEAN',
            'total_files': 0,
            'modified_files': [],
            'missing_files': [],
            'new_files': [],
            'summary': {}
        }
        
        baseline_files = set(self.baseline.get('files', {}).keys())
        current_files = set()
        
        # Check each file in baseline
        for file_path_str, baseline_info in self.baseline.get('files', {}).items():
            file_path = self.base_path / file_path_str
            current_files.add(file_path_str)
            results['total_files'] += 1
            
            print(f"  Checking: {file_path_str}...", end='')
            
            if not file_path.exists():
                results['missing_files'].append({
                    'file': file_path_str,
                    'baseline_hash': baseline_info['hash']
                })
                results['status'] = 'TAMPERED'
                print(" ❌ MISSING")
                continue
            
            current_hash = self.calculate_file_hash(file_path)
            
            if current_hash != baseline_info['hash']:
                current_size = file_path.stat().st_size
                current_modified = datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                
                results['modified_files'].append({
                    'file': file_path_str,
                    'baseline_hash': baseline_info['hash'],
                    'current_hash': current_hash,
                    'baseline_size': baseline_info.get('size'),
                    'current_size': current_size,
                    'baseline_modified': baseline_info.get('modified'),
                    'current_modified': current_modified
                })
                results['status'] = 'TAMPERED'
                print(" ⚠️  MODIFIED")
            else:
                print(" ✅")
        
        # Check for new critical files not in baseline
        for file_path_str in self.SECURITY_CRITICAL_FILES:
            if file_path_str not in baseline_files:
                file_path = self.base_path / file_path_str
                if file_path.exists():
                    current_hash = self.calculate_file_hash(file_path)
                    results['new_files'].append({
                        'file': file_path_str,
                        'current_hash': current_hash,
                        'size': file_path.stat().st_size
                    })
        
        # Generate summary
        results['summary'] = {
            'total_checked': results['total_files'],
            'modified_count': len(results['modified_files']),
            'missing_count': len(results['missing_files']),
            'new_count': len(results['new_files']),
            'integrity_intact': results['status'] == 'CLEAN'
        }
        
        return results
    
    def print_report(self, results: Dict[str, Any], detailed: bool = False):
        """
        Print verification report.
        
        Args:
            results: Verification results
            detailed: Include detailed information
        """
        print("\n" + "="*70)
        print("FILE INTEGRITY VERIFICATION REPORT")
        print("="*70)
        
        summary = results['summary']
        print(f"\n📊 Summary:")
        print(f"  Verification Time: {results['timestamp']}")
        print(f"  Baseline Date: {results['baseline_date']}")
        print(f"  Total Files Checked: {summary['total_checked']}")
        print(f"  Modified Files: {summary['modified_count']}")
        print(f"  Missing Files: {summary['missing_count']}")
        print(f"  New Files: {summary['new_count']}")
        
        if results['modified_files']:
            print(f"\n⚠️  MODIFIED FILES ({len(results['modified_files'])}):")
            for mod_file in results['modified_files']:
                print(f"\n  File: {mod_file['file']}")
                print(f"  Baseline Hash: {mod_file['baseline_hash']}")
                print(f"  Current Hash:  {mod_file['current_hash']}")
                
                if detailed:
                    print(f"  Baseline Size: {mod_file.get('baseline_size', 'N/A')} bytes")
                    print(f"  Current Size:  {mod_file.get('current_size', 'N/A')} bytes")
                    print(f"  Baseline Modified: {mod_file.get('baseline_modified', 'N/A')}")
                    print(f"  Current Modified:  {mod_file.get('current_modified', 'N/A')}")
        
        if results['missing_files']:
            print(f"\n❌ MISSING FILES ({len(results['missing_files'])}):")
            for missing_file in results['missing_files']:
                print(f"  - {missing_file['file']}")
                if detailed:
                    print(f"    Baseline Hash: {missing_file['baseline_hash']}")
        
        if results['new_files']:
            print(f"\n📄 NEW FILES ({len(results['new_files'])}):")
            for new_file in results['new_files']:
                print(f"  - {new_file['file']}")
                if detailed:
                    print(f"    Hash: {new_file['current_hash']}")
                    print(f"    Size: {new_file['size']} bytes")
        
        print("\n" + "="*70)
        
        if results['status'] == 'CLEAN':
            print("✅ FILE INTEGRITY VERIFIED - No tampering detected")
        else:
            print("⚠️  TAMPERING DETECTED - Files have been modified")
            print("   IMMEDIATE ACTION REQUIRED:")
            print("   1. Review modified files with: git diff")
            print("   2. Check audit logs for unauthorized changes")
            print("   3. Restore from backup if necessary")
            print("   4. Update baseline if changes are authorized")
        
        print("="*70 + "\n")
    
    def update_baseline(self) -> bool:
        """
        Update baseline with current file hashes.
        
        Returns:
            True if baseline updated successfully
        """
        print("🔄 Updating security baseline...")
        
        # Verify first
        if self.baseline:
            results = self.verify_integrity()
            
            if results['modified_files'] or results['missing_files']:
                print("\n⚠️  WARNING: Files have been modified or are missing!")
                print("   Review changes before updating baseline.")
                
                response = input("\nAre you sure you want to update the baseline? (yes/no): ")
                if response.lower() != 'yes':
                    print("Baseline update cancelled.")
                    return False
        
        # Create new baseline
        self.create_baseline()
        print("✅ Baseline updated successfully")
        return True


def main():
    """Main entry point for tamper detection script."""
    parser = argparse.ArgumentParser(
        description='ATS MAFIA Framework File Integrity Monitoring',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tamper_detection.py --create-baseline    # Create initial baseline
  python tamper_detection.py                      # Verify integrity
  python tamper_detection.py --json               # JSON output
  python tamper_detection.py --update-baseline    # Update baseline
        """
    )
    
    parser.add_argument(
        '--create-baseline',
        action='store_true',
        help='Create initial security baseline'
    )
    
    parser.add_argument(
        '--update-baseline',
        action='store_true',
        help='Update existing baseline'
    )
    
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results in JSON format'
    )
    
    parser.add_argument(
        '--detailed',
        action='store_true',
        help='Show detailed information'
    )
    
    parser.add_argument(
        '--baseline-file',
        type=str,
        default='security_baseline.json',
        help='Path to baseline file'
    )
    
    parser.add_argument(
        '--base-path',
        type=str,
        default=None,
        help='Base directory path for the framework'
    )
    
    args = parser.parse_args()
    
    # Initialize tamper detection
    detector = TamperDetection(
        baseline_file=args.baseline_file,
        base_path=args.base_path
    )
    
    try:
        if args.create_baseline:
            # Create new baseline
            baseline = detector.create_baseline()
            
            if args.json:
                print(json.dumps(baseline, indent=2))
            
            sys.exit(0)
        
        elif args.update_baseline:
            # Update existing baseline
            success = detector.update_baseline()
            sys.exit(0 if success else 1)
        
        else:
            # Verify integrity
            if not detector.load_baseline():
                sys.exit(1)
            
            results = detector.verify_integrity()
            
            if args.json:
                print(json.dumps(results, indent=2))
            else:
                detector.print_report(results, detailed=args.detailed)
            
            # Exit with error if tampering detected
            sys.exit(0 if results['status'] == 'CLEAN' else 1)
    
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()