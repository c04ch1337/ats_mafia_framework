# MITRE ATT&CK Framework Integration

This module provides seamless integration with the MITRE ATT&CK framework for the ATS MAFIA training platform.

## Quick Start

```python
from ats_mafia_framework.knowledge import ATTACKFramework

# Initialize framework (downloads data on first run)
attack = ATTACKFramework()

# Get a specific technique
technique = attack.get_technique('T1055')  # Process Injection
print(f"{technique['id']}: {technique['name']}")
print(f"Tactics: {', '.join(technique['tactics'])}")

# Search for techniques
results = attack.search_techniques('phishing')
for tech in results:
    print(f"{tech['id']}: {tech['name']}")

# Get techniques by tactic
recon_techniques = attack.get_techniques_by_tactic('reconnaissance')
print(f"Found {len(recon_techniques)} reconnaissance techniques")

# Validate coverage
my_techniques = ['T1055', 'T1059', 'T1566']
coverage = attack.validate_technique_coverage(my_techniques)
print(f"Coverage: {coverage['overall_coverage']:.1f}%")
```

## Features

### 1. Data Loading
- **Automatic Download**: Fetches latest ATT&CK data from MITRE CTI on first run
- **Local Caching**: Stores data locally for fast subsequent loads
- **Version Tracking**: Maintains version information for compatibility

### 2. Technique Management
- Get techniques by ID (including sub-techniques)
- Search techniques by name or description
- Filter by tactic, platform, or data source
- Access complete technique metadata

### 3. Coverage Analysis
- Calculate ATT&CK coverage percentage
- Break down coverage by tactic
- Identify gaps in technique coverage
- Export coverage reports

### 4. Tactic Organization
- Retrieve all techniques for a specific tactic
- Generate technique trees organized by tactics
- Access tactic metadata and relationships

## Data Structure

### Technique Object
```python
{
    'id': 'T1055',
    'name': 'Process Injection',
    'description': 'Adversaries may inject code...',
    'tactics': ['defense-evasion', 'privilege-escalation'],
    'platforms': ['Windows', 'macOS', 'Linux'],
    'data_sources': ['Process: Process Access', ...],
    'detection': 'Monitoring Windows API calls...',
    'is_subtechnique': False,
    'url': 'https://attack.mitre.org/techniques/T1055/',
    'deprecated': False,
    'revoked': False
}
```

### Coverage Report
```python
{
    'overall_coverage': 15.2,
    'total_techniques': 200,
    'covered_techniques': 30,
    'coverage_by_tactic': {
        'Reconnaissance': {
            'total': 18,
            'covered': 12,
            'percentage': 66.7,
            'shortname': 'reconnaissance'
        },
        ...
    },
    'gaps': ['T1001', 'T1003', ...],
    'version': '15.1',
    'last_updated': '2025-10-18T04:30:00'
}
```

## API Reference

### ATTACKFramework Class

#### `__init__(data_path=None, use_online=True)`
Initialize the framework.
- `data_path`: Optional path to cached ATT&CK data
- `use_online`: Whether to fetch from online if local not found

#### `get_technique(technique_id: str) -> Dict`
Retrieve a technique by ID.
- Supports both techniques (T1055) and sub-techniques (T1055.001)
- Returns None if not found

#### `search_techniques(query: str, include_subtechniques=True) -> List[Dict]`
Search techniques by name or description.
- Case-insensitive search
- Optionally include sub-techniques

#### `get_techniques_by_tactic(tactic_name: str) -> List[Dict]`
Get all techniques for a specific tactic.
- Accepts tactic name or shortname
- Case-insensitive

#### `validate_technique_coverage(technique_ids: List[str]) -> Dict`
Analyze coverage of a technique set.
- Returns overall and per-tactic coverage
- Identifies gaps

#### `get_statistics() -> Dict`
Get framework statistics.
- Version and update information
- Object counts (techniques, tactics, groups, software)

## Testing

Run the test suite to validate installation:

```bash
python ats_mafia_framework/knowledge/test_attack_framework.py
```

Expected output:
```
✅ Framework loaded successfully
   Version: 15.1
   Techniques: 200+
   Sub-techniques: 400+
   Tactics: 14
```

## Integration with Profiles

Enhance agent profiles with ATT&CK knowledge:

```json
{
  "metadata": {
    "id": "phantom_stealth_specialist",
    "name": "Phantom - Stealth Specialist"
  },
  "attack_knowledge": {
    "mastered_techniques": [
      {
        "id": "T1055",
        "name": "Process Injection",
        "proficiency": "expert",
        "variations": ["T1055.001", "T1055.002"]
      }
    ],
    "tactic_expertise": {
      "defense-evasion": {
        "proficiency": "master",
        "techniques": ["T1055", "T1070", "T1027"],
        "coverage": 0.85
      }
    }
  }
}
```

## Performance

- **Data Loading**: ~2 seconds (first run with download)
- **Cached Loading**: ~200ms
- **Technique Lookup**: <5ms
- **Search Query**: <50ms
- **Coverage Calculation**: <100ms

## Data Source

ATT&CK data is sourced from the official MITRE CTI repository:
- **Repository**: https://github.com/mitre/cti
- **Data File**: enterprise-attack.json
- **Update Frequency**: Check MITRE repository for latest releases
- **Current Version**: ATT&CK v15 (2024)

## Troubleshooting

### "No ATT&CK data available"
- Ensure internet connectivity for first-time download
- Or manually download enterprise-attack.json to `ats_mafia_framework/knowledge/attack/`

### "Technique not found"
- Verify technique ID format (e.g., 'T1055' not 't1055')
- Check if technique is deprecated/revoked
- Ensure ATT&CK data is loaded

### Slow performance
- Check if data is cached locally
- Clear cache and re-download if corrupted
- Ensure sufficient disk space for cache

## Future Enhancements

- [ ] Mobile and ICS ATT&CK matrices
- [ ] Relationship mapping between techniques
- [ ] Mitigation recommendations
- [ ] Detection analytics integration
- [ ] Custom technique definitions

## License

This integration uses data from MITRE ATT&CK®, which is provided under the Apache 2.0 license.

MITRE ATT&CK® is a registered trademark of The MITRE Corporation.

## Resources

- [MITRE ATT&CK Website](https://attack.mitre.org/)
- [ATT&CK Navigator](https://mitre-attack.github.io/attack-navigator/)
- [MITRE CTI Repository](https://github.com/mitre/cti)
- [ATT&CK Documentation](https://attack.mitre.org/docs/)