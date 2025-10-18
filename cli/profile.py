#!/usr/bin/env python3
"""
ATS MAFIA Framework Profile CLI

Provides command-line interface for profile management functionality.
"""

import argparse
import asyncio
import json
import sys
from typing import Optional, List
from pathlib import Path

from ..core.profile_manager import ProfileManager, initialize_profile_manager
from ..core.logging import initialize_audit_logger
from ..config.settings import load_config, FrameworkConfig


async def list_profiles(config_file: Optional[str] = None, 
                       profile_type: Optional[str] = None,
                       output_format: str = "table") -> None:
    """
    List available profiles.
    
    Args:
        config_file: Path to configuration file
        profile_type: Filter by profile type
        output_format: Output format (table, json)
    """
    try:
        # Load configuration
        if config_file:
            config = load_config(Path(config_file))
        else:
            config = FrameworkConfig()
        
        # Initialize components
        audit_logger = initialize_audit_logger(config)
        profile_manager = initialize_profile_manager(config, audit_logger)
        
        # Get profiles
        profiles = profile_manager.list_profiles()
        
        if profile_type:
            profiles = [p for p in profiles if p.get('profile_type') == profile_type]
        
        if not profiles:
            print("No profiles found")
            return
        
        if output_format == "json":
            print(json.dumps(profiles, indent=2))
        else:
            print(f"\n📋 Available Profiles ({len(profiles)}):")
            print("-" * 80)
            
            for profile in profiles:
                print(f"🏷️  {profile.get('name', 'Unknown')} ({profile.get('id', 'N/A')})")
                print(f"   Type: {profile.get('profile_type', 'N/A')}")
                print(f"   Category: {profile.get('category', 'N/A')}")
                description = profile.get('description', 'No description')
                print(f"   Description: {description[:80]}{'...' if len(description) > 80 else ''}")
                print(f"   Version: {profile.get('version', 'N/A')}")
                print(f"   Author: {profile.get('author', 'N/A')}")
                tags = profile.get('tags', [])
                print(f"   Tags: {', '.join(tags) if tags else 'None'}")
                print()
                
    except Exception as e:
        print(f"❌ Error listing profiles: {e}")
        sys.exit(1)


async def validate_profile(config_file: Optional[str] = None,
                          profile_path: Optional[str] = None) -> None:
    """
    Validate a profile file.
    
    Args:
        config_file: Path to configuration file
        profile_path: Path to profile file to validate
    """
    if not profile_path:
        print("❌ Profile path is required for validation")
        sys.exit(1)
    
    try:
        # Load configuration
        if config_file:
            config = load_config(Path(config_file))
        else:
            config = FrameworkConfig()
        
        # Initialize components
        audit_logger = initialize_audit_logger(config)
        profile_manager = initialize_profile_manager(config, audit_logger)
        
        # Validate profile
        profile_file = Path(profile_path)
        if not profile_file.exists():
            print(f"❌ Profile file not found: {profile_path}")
            sys.exit(1)
        
        # Load and validate profile
        with open(profile_file, 'r', encoding='utf-8') as f:
            profile_data = json.load(f)
        
        # Basic validation
        required_fields = ['id', 'name', 'profile_type', 'version', 'author']
        missing_fields = [field for field in required_fields if field not in profile_data]
        
        if missing_fields:
            print(f"❌ Profile validation failed. Missing required fields: {', '.join(missing_fields)}")
            sys.exit(1)
        
        print(f"✅ Profile {profile_data.get('name')} is valid")
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in profile file: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error validating profile: {e}")
        sys.exit(1)


async def create_profile(config_file: Optional[str] = None,
                        profile_data: Optional[str] = None,
                        output_path: Optional[str] = None) -> None:
    """
    Create a new profile from JSON data.
    
    Args:
        config_file: Path to configuration file
        profile_data: JSON string containing profile data
        output_path: Path to save the profile
    """
    if not profile_data:
        print("❌ Profile data is required for creation")
        sys.exit(1)
    
    if not output_path:
        print("❌ Output path is required for profile creation")
        sys.exit(1)
    
    try:
        # Parse profile data
        data = json.loads(profile_data)
        
        # Load configuration
        if config_file:
            config = load_config(Path(config_file))
        else:
            config = FrameworkConfig()
        
        # Initialize components
        audit_logger = initialize_audit_logger(config)
        profile_manager = initialize_profile_manager(config, audit_logger)
        
        # Validate required fields
        required_fields = ['id', 'name', 'profile_type', 'version', 'author']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            print(f"❌ Profile creation failed. Missing required fields: {', '.join(missing_fields)}")
            sys.exit(1)
        
        # Save profile
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        print(f"✅ Profile created successfully: {output_path}")
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in profile data: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error creating profile: {e}")
        sys.exit(1)


def main() -> None:
    """Main entry point for profile CLI."""
    parser = argparse.ArgumentParser(
        description="ATS MAFIA Framework Profile Management"
    )
    
    parser.add_argument(
        '--config', '-c',
        type=str,
        help='Path to configuration file'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List profiles')
    list_parser.add_argument(
        '--type',
        type=str,
        help='Filter by profile type'
    )
    list_parser.add_argument(
        '--format', '-f',
        type=str,
        choices=['table', 'json'],
        default='table',
        help='Output format (default: table)'
    )
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate a profile')
    validate_parser.add_argument(
        'profile_path',
        type=str,
        help='Path to profile file to validate'
    )
    
    # Create command
    create_parser = subparsers.add_parser('create', help='Create a new profile')
    create_parser.add_argument(
        '--data', '-d',
        type=str,
        required=True,
        help='JSON string containing profile data'
    )
    create_parser.add_argument(
        '--output', '-o',
        type=str,
        required=True,
        help='Path to save the profile'
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        if args.command == 'list':
            asyncio.run(list_profiles(args.config, args.type, args.format))
        elif args.command == 'validate':
            asyncio.run(validate_profile(args.config, args.profile_path))
        elif args.command == 'create':
            asyncio.run(create_profile(args.config, args.data, args.output))
        else:
            print(f"❌ Unknown command: {args.command}")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()