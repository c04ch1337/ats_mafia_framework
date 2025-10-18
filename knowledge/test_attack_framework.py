"""
Test script for MITRE ATT&CK Framework Integration
Run this to validate the framework is working correctly
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ats_mafia_framework.knowledge.attack_framework import ATTACKFramework


def test_framework_loading():
    """Test basic framework loading"""
    print("=" * 80)
    print("TEST 1: Framework Loading")
    print("=" * 80)
    
    try:
        attack = ATTACKFramework()
        print(f"✅ Framework loaded successfully")
        print(f"   Version: {attack.version}")
        print(f"   Techniques: {len(attack.techniques)}")
        print(f"   Sub-techniques: {len(attack.subtechniques)}")
        print(f"   Tactics: {len(attack.tactics)}")
        print(f"   Groups: {len(attack.groups)}")
        print(f"   Software: {len(attack.software)}")
        return attack
    except Exception as e:
        print(f"❌ Framework loading failed: {e}")
        return None


def test_technique_lookup(attack):
    """Test technique retrieval"""
    print("\n" + "=" * 80)
    print("TEST 2: Technique Lookup")
    print("=" * 80)
    
    test_techniques = ['T1055', 'T1059', 'T1566', 'T1598.001']
    
    for tech_id in test_techniques:
        technique = attack.get_technique(tech_id)
        if technique:
            print(f"✅ {tech_id}: {technique['name']}")
            print(f"   Tactics: {', '.join(technique['tactics'])}")
            print(f"   Platforms: {', '.join(technique['platforms'][:3])}...")
        else:
            print(f"❌ {tech_id}: Not found")


def test_search(attack):
    """Test technique search"""
    print("\n" + "=" * 80)
    print("TEST 3: Technique Search")
    print("=" * 80)
    
    queries = ['phishing', 'powershell', 'injection']
    
    for query in queries:
        results = attack.search_techniques(query)
        print(f"Query '{query}': Found {len(results)} techniques")
        if results:
            for i, tech in enumerate(results[:3], 1):
                print(f"  {i}. {tech['id']}: {tech['name']}")
        if len(results) > 3:
            print(f"  ... and {len(results) - 3} more")


def test_tactic_techniques(attack):
    """Test getting techniques by tactic"""
    print("\n" + "=" * 80)
    print("TEST 4: Techniques by Tactic")
    print("=" * 80)
    
    tactics = ['reconnaissance', 'initial-access', 'defense-evasion']
    
    for tactic in tactics:
        techniques = attack.get_techniques_by_tactic(tactic)
        print(f"Tactic '{tactic}': {len(techniques)} techniques")
        if techniques:
            for i, tech in enumerate(techniques[:3], 1):
                print(f"  {i}. {tech['id']}: {tech['name']}")
            if len(techniques) > 3:
                print(f"  ... and {len(techniques) - 3} more")


def test_coverage_analysis(attack):
    """Test coverage analysis"""
    print("\n" + "=" * 80)
    print("TEST 5: Coverage Analysis")
    print("=" * 80)
    
    # Simulate a profile with some techniques
    simulated_techniques = [
        'T1055', 'T1059', 'T1566', 'T1598.001', 'T1589',
        'T1070', 'T1027', 'T1053', 'T1547', 'T1003'
    ]
    
    coverage = attack.validate_technique_coverage(simulated_techniques)
    
    print(f"Overall Coverage: {coverage['overall_coverage']:.1f}%")
    print(f"Covered: {coverage['covered_techniques']} / {coverage['total_techniques']}")
    print("\nCoverage by Tactic:")
    
    for tactic_name, stats in sorted(
        coverage['coverage_by_tactic'].items(),
        key=lambda x: x[1]['percentage'],
        reverse=True
    )[:5]:
        print(f"  {tactic_name}: {stats['covered']}/{stats['total']} ({stats['percentage']:.1f}%)")


def test_statistics(attack):
    """Test statistics retrieval"""
    print("\n" + "=" * 80)
    print("TEST 6: Framework Statistics")
    print("=" * 80)
    
    stats = attack.get_statistics()
    
    print(f"Version: {stats['version']}")
    print(f"Last Updated: {stats['last_updated']}")
    print(f"Data Source: {stats['data_source']}")
    print(f"\nObject Counts:")
    print(f"  Tactics: {stats['total_tactics']}")
    print(f"  Techniques: {stats['total_techniques']}")
    print(f"  Sub-techniques: {stats['total_subtechniques']}")
    print(f"  Groups: {stats['total_groups']}")
    print(f"  Software: {stats['total_software']}")
    print(f"\nTactics: {', '.join(stats['tactics'][:5])}...")


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("MITRE ATT&CK Framework - Test Suite")
    print("=" * 80)
    print("\nThis will test the ATT&CK framework integration.")
    print("On first run, it will download ~15MB of data from MITRE.")
    print()
    
    # Test 1: Load framework
    attack = test_framework_loading()
    if not attack:
        print("\n❌ Framework loading failed. Cannot continue tests.")
        return 1
    
    # Test 2: Technique lookup
    test_technique_lookup(attack)
    
    # Test 3: Search
    test_search(attack)
    
    # Test 4: Techniques by tactic
    test_tactic_techniques(attack)
    
    # Test 5: Coverage analysis
    test_coverage_analysis(attack)
    
    # Test 6: Statistics
    test_statistics(attack)
    
    print("\n" + "=" * 80)
    print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
    print("=" * 80)
    print("\nThe ATT&CK framework is ready for use!")
    print(f"Data cached at: {attack.data_path}")
    print()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())