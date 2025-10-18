"""
MITRE ATT&CK Framework Integration
Provides access to ATT&CK tactics, techniques, and procedures for training scenarios
"""

import json
import requests
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
import logging


class ATTACKFramework:
    """
    Interface to MITRE ATT&CK framework data
    
    Loads and provides access to ATT&CK Enterprise tactics, techniques,
    sub-techniques, groups, and software for use in training scenarios.
    
    Supports both local cached data and online fetching from MITRE CTI repository.
    """
    
    def __init__(self, data_path: Optional[str] = None, use_online: bool = True):
        """
        Initialize ATT&CK framework interface
        
        Args:
            data_path: Path to local ATT&CK data (JSON STIX format)
            use_online: Whether to fetch from online if local not found
        """
        self.logger = logging.getLogger("attack_framework")
        self.data_path = data_path or "ats_mafia_framework/knowledge/attack/enterprise-attack.json"
        self.use_online = use_online
        self.base_url = "https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack"
        
        # Storage for ATT&CK objects
        self.tactics: Dict[str, Dict] = {}
        self.techniques: Dict[str, Dict] = {}
        self.subtechniques: Dict[str, Dict] = {}
        self.groups: Dict[str, Dict] = {}
        self.software: Dict[str, Dict] = {}
        
        # Metadata
        self.version: Optional[str] = None
        self.last_updated: Optional[datetime] = None
        
        # Load data
        self._load_attack_data()
    
    def _load_attack_data(self) -> None:
        """Load ATT&CK data from local file or online source"""
        try:
            # Try local file first
            if Path(self.data_path).exists():
                self.logger.info(f"Loading ATT&CK data from {self.data_path}")
                with open(self.data_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self._parse_attack_data(data)
                self.last_updated = datetime.fromtimestamp(
                    Path(self.data_path).stat().st_mtime
                )
                self.logger.info(
                    f"Loaded {len(self.techniques)} techniques, "
                    f"{len(self.tactics)} tactics from local cache"
                )
                
            elif self.use_online:
                # Fetch from MITRE CTI repository
                self.logger.info("Fetching ATT&CK data from online source")
                url = f"{self.base_url}/enterprise-attack.json"
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                data = response.json()
                self._parse_attack_data(data)
                self.last_updated = datetime.now()
                
                # Cache locally for future use
                Path(self.data_path).parent.mkdir(parents=True, exist_ok=True)
                with open(self.data_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
                
                self.logger.info(
                    f"Downloaded and cached ATT&CK data: "
                    f"{len(self.techniques)} techniques, {len(self.tactics)} tactics"
                )
            else:
                self.logger.warning(
                    "No ATT&CK data available (local file not found, online disabled)"
                )
                
        except Exception as e:
            self.logger.error(f"Error loading ATT&CK data: {e}")
            raise
    
    def _parse_attack_data(self, data: Dict) -> None:
        """
        Parse ATT&CK STIX data into usable format
        
        Args:
            data: Raw STIX bundle data from ATT&CK
        """
        objects = data.get('objects', [])
        
        # Extract version if available
        for obj in objects:
            if obj.get('type') == 'x-mitre-collection':
                self.version = obj.get('x_mitre_version', 'unknown')
                break
        
        # Parse all objects
        for obj in objects:
            obj_type = obj.get('type')
            
            if obj_type == 'x-mitre-tactic':
                self._parse_tactic(obj)
            elif obj_type == 'attack-pattern':
                self._parse_technique(obj)
            elif obj_type == 'intrusion-set':
                self._parse_group(obj)
            elif obj_type in ['malware', 'tool']:
                self._parse_software(obj)
    
    def _parse_tactic(self, obj: Dict) -> None:
        """Parse tactic object"""
        external_refs = obj.get('external_references', [{}])
        tactic_id = external_refs[0].get('external_id')
        
        if tactic_id:
            self.tactics[tactic_id] = {
                'id': tactic_id,
                'name': obj.get('name'),
                'description': obj.get('description', ''),
                'shortname': obj.get('x_mitre_shortname', ''),
                'url': external_refs[0].get('url', '')
            }
    
    def _parse_technique(self, obj: Dict) -> None:
        """Parse technique or sub-technique object"""
        external_refs = obj.get('external_references', [{}])
        technique_id = external_refs[0].get('external_id')
        
        if not technique_id:
            return
        
        is_subtechnique = '.' in technique_id
        
        # Extract kill chain phases (tactics)
        tactics = []
        for phase in obj.get('kill_chain_phases', []):
            if phase.get('kill_chain_name') == 'mitre-attack':
                tactics.append(phase.get('phase_name', ''))
        
        technique_data = {
            'id': technique_id,
            'name': obj.get('name', ''),
            'description': obj.get('description', ''),
            'tactics': tactics,
            'platforms': obj.get('x_mitre_platforms', []),
            'data_sources': obj.get('x_mitre_data_sources', []),
            'detection': obj.get('x_mitre_detection', ''),
            'is_subtechnique': is_subtechnique,
            'url': external_refs[0].get('url', ''),
            'deprecated': obj.get('x_mitre_deprecated', False),
            'revoked': obj.get('revoked', False)
        }
        
        # Store in appropriate collection
        if is_subtechnique:
            self.subtechniques[technique_id] = technique_data
        else:
            self.techniques[technique_id] = technique_data
    
    def _parse_group(self, obj: Dict) -> None:
        """Parse threat group object"""
        external_refs = obj.get('external_references', [{}])
        group_id = external_refs[0].get('external_id')
        
        if group_id:
            self.groups[group_id] = {
                'id': group_id,
                'name': obj.get('name', ''),
                'description': obj.get('description', ''),
                'aliases': obj.get('aliases', []),
                'url': external_refs[0].get('url', '')
            }
    
    def _parse_software(self, obj: Dict) -> None:
        """Parse malware/tool object"""
        external_refs = obj.get('external_references', [{}])
        software_id = external_refs[0].get('external_id')
        
        if software_id:
            self.software[software_id] = {
                'id': software_id,
                'name': obj.get('name', ''),
                'description': obj.get('description', ''),
                'type': obj.get('type', ''),
                'platforms': obj.get('x_mitre_platforms', []),
                'url': external_refs[0].get('url', '')
            }
    
    def get_technique(self, technique_id: str) -> Optional[Dict]:
        """
        Get technique by ID (e.g., 'T1059' or 'T1059.001')
        
        Args:
            technique_id: ATT&CK technique ID
            
        Returns:
            Technique data dictionary or None if not found
        """
        if '.' in technique_id:
            return self.subtechniques.get(technique_id)
        return self.techniques.get(technique_id)
    
    def get_tactic(self, tactic_id: str) -> Optional[Dict]:
        """
        Get tactic by ID (e.g., 'TA0001')
        
        Args:
            tactic_id: ATT&CK tactic ID
            
        Returns:
            Tactic data dictionary or None if not found
        """
        return self.tactics.get(tactic_id)
    
    def get_techniques_by_tactic(self, tactic_name: str) -> List[Dict]:
        """
        Get all techniques for a specific tactic
        
        Args:
            tactic_name: Tactic name or shortname (case-insensitive)
            
        Returns:
            List of technique data dictionaries
        """
        results = []
        tactic_lower = tactic_name.lower().replace('-', '_').replace(' ', '-')
        
        # Search both techniques and subtechniques
        all_techniques = list(self.techniques.values()) + list(self.subtechniques.values())
        
        for technique in all_techniques:
            # Skip deprecated/revoked
            if technique.get('deprecated') or technique.get('revoked'):
                continue
            
            # Check if tactic matches
            technique_tactics = [
                t.lower().replace('-', '_').replace(' ', '-') 
                for t in technique.get('tactics', [])
            ]
            
            if tactic_lower in technique_tactics:
                results.append(technique)
        
        return results
    
    def search_techniques(self, query: str, include_subtechniques: bool = True) -> List[Dict]:
        """
        Search techniques by name or description
        
        Args:
            query: Search query string
            include_subtechniques: Include sub-techniques in results
            
        Returns:
            List of matching technique data dictionaries
        """
        query_lower = query.lower()
        results = []
        
        # Determine which collections to search
        collections = [self.techniques]
        if include_subtechniques:
            collections.append(self.subtechniques)
        
        for collection in collections:
            for technique in collection.values():
                # Skip deprecated/revoked
                if technique.get('deprecated') or technique.get('revoked'):
                    continue
                
                # Search in name and description
                if (query_lower in technique['name'].lower() or
                    query_lower in technique.get('description', '').lower()):
                    results.append(technique)
        
        return results
    
    def get_technique_tree(self) -> Dict[str, List[Dict]]:
        """
        Get techniques organized by tactic
        
        Returns:
            Dictionary mapping tactic names to lists of techniques
        """
        tree = {}
        
        for tactic_id, tactic in self.tactics.items():
            tactic_name = tactic['shortname']
            tree[tactic_name] = self.get_techniques_by_tactic(tactic_name)
        
        return tree
    
    def validate_technique_coverage(self, technique_ids: List[str]) -> Dict[str, Any]:
        """
        Validate technique coverage and identify gaps
        
        Args:
            technique_ids: List of technique IDs to validate
            
        Returns:
            Dictionary with coverage statistics and gaps
        """
        # Filter to non-deprecated/revoked techniques
        active_techniques = {
            tid: t for tid, t in self.techniques.items()
            if not t.get('deprecated') and not t.get('revoked')
        }
        
        total_techniques = len(active_techniques)
        covered_techniques = len(set(technique_ids) & set(active_techniques.keys()))
        
        # Calculate coverage by tactic
        coverage_by_tactic = {}
        for tactic_id, tactic in self.tactics.items():
            tactic_techniques = self.get_techniques_by_tactic(tactic['shortname'])
            
            # Filter active only
            tactic_techniques = [
                t for t in tactic_techniques 
                if not t.get('deprecated') and not t.get('revoked')
            ]
            
            tactic_total = len(tactic_techniques)
            tactic_covered = len([
                t for t in tactic_techniques 
                if t['id'] in technique_ids
            ])
            
            coverage_by_tactic[tactic['name']] = {
                'total': tactic_total,
                'covered': tactic_covered,
                'percentage': (tactic_covered / tactic_total * 100) if tactic_total > 0 else 0,
                'shortname': tactic['shortname']
            }
        
        # Identify gaps
        gaps = list(set(active_techniques.keys()) - set(technique_ids))
        
        return {
            'overall_coverage': (covered_techniques / total_techniques * 100) if total_techniques > 0 else 0,
            'total_techniques': total_techniques,
            'covered_techniques': covered_techniques,
            'coverage_by_tactic': coverage_by_tactic,
            'gaps': gaps,
            'version': self.version,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get overall ATT&CK framework statistics
        
        Returns:
            Dictionary with framework statistics
        """
        return {
            'version': self.version,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'total_tactics': len(self.tactics),
            'total_techniques': len(self.techniques),
            'total_subtechniques': len(self.subtechniques),
            'total_groups': len(self.groups),
            'total_software': len(self.software),
            'tactics': list(self.tactics.keys()),
            'data_source': 'local' if Path(self.data_path).exists() else 'online'
        }
    
    def export_technique_list(self, technique_ids: List[str]) -> List[Dict]:
        """
        Export detailed information for a list of techniques
        
        Args:
            technique_ids: List of technique IDs to export
            
        Returns:
            List of detailed technique data
        """
        results = []
        
        for tech_id in technique_ids:
            technique = self.get_technique(tech_id)
            if technique:
                results.append(technique)
        
        return results
    
    def __repr__(self) -> str:
        """String representation"""
        return (
            f"ATTACKFramework(version={self.version}, "
            f"techniques={len(self.techniques)}, "
            f"tactics={len(self.tactics)})"
        )