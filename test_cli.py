#!/usr/bin/env python3
"""
Test script to verify the CLI module can be imported and executed correctly.
"""

import sys
import importlib

def test_import():
    """Test that the CLI module can be imported."""
    try:
        # Test importing the CLI module
        import ats_mafia_framework.cli
        print("✅ Successfully imported ats_mafia_framework.cli")
        
        # Test importing the main function
        from ats_mafia_framework.cli.main import cli_main
        print("✅ Successfully imported cli_main from ats_mafia_framework.cli.main")
        
        # Test importing from the backward compatibility file
        from ats_mafia_framework.cli import ATSMAFIACLI
        print("✅ Successfully imported ATSMAFIACLI from ats_mafia_framework.cli")
        
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_module_execution():
    """Test that the module can be executed as a module."""
    try:
        # Test that the module can be executed
        spec = importlib.util.spec_from_file_location(
            "ats_mafia_framework.cli.__main__",
            "ats_mafia_framework/cli/__main__.py"
        )
        module = importlib.util.module_from_spec(spec)
        print("✅ Successfully loaded ats_mafia_framework.cli.__main__")
        return True
    except Exception as e:
        print(f"❌ Module execution test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing ATS MAFIA Framework CLI Module Structure")
    print("=" * 60)
    
    success = True
    success &= test_import()
    success &= test_module_execution()
    
    print("=" * 60)
    if success:
        print("✅ All tests passed! The CLI module structure is working correctly.")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Please check the errors above.")
        sys.exit(1)