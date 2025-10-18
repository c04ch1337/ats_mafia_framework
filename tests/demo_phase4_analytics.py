"""
ATS MAFIA Framework - Phase 4 Analytics System Demonstration

This script demonstrates the complete Phase 4 analytics system with sample data
and showcases all major features.
"""

import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
import uuid

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ats_mafia_framework.core.performance_metrics import (
    PerformanceMetricsEngine, MetricType, SkillLevel, SessionPerformance
)
from ats_mafia_framework.core.training_effectiveness import (
    TrainingEffectivenessTracker
)
from ats_mafia_framework.core.advanced_cost_analytics import (
    AdvancedCostAnalytics, CostCategory
)
from ats_mafia_framework.core.progress_tracker import ProgressTracker
from ats_mafia_framework.core.reporting_engine import (
    ReportingEngine, ReportType, ReportFormat
)
from ats_mafia_framework.core.analytics_aggregator import (
    AnalyticsAggregator, AlertType, AlertPriority
)
from ats_mafia_framework.core.cost_tracker import CostTracker
from ats_mafia_framework.core.llm_models import ModelRegistry


def print_section(title: str):
    """Print a section header."""
    print("\n" + "="*70)
    print(f" {title}")
    print("="*70 + "\n")


def generate_sample_data(perf_engine, cost_tracker, progress_tracker):
    """Generate sample training data for demonstration."""
    print("Generating sample training data...")
    
    # Create 3 sample operators
    operators = []
    for i in range(3):
        operator_id = f"demo_operator_{i+1}"
        profile = perf_engine.create_operator_profile(
            operator_id=operator_id,
            name=f"Operator {i+1}",
            metadata={'team': 'alpha', 'role': 'red_team'}
        )
        operators.append(operator_id)
        
        # Simulate training sessions with progression
        for j in range(10):
            session_id = f"session_{operator_id}_{j}"
            
            # Create session with improving scores
            base_score = 0.5 + (i * 0.1)  # Different starting levels
            session_score = min(1.0, base_score + (j * 0.04))  # Improve over time
            
            session = SessionPerformance(
                session_id=session_id,
                operator_id=operator_id,
                scenario_id=f"scenario_{j % 3}",
                start_time=datetime.now(timezone.utc) - timedelta(days=10-j, hours=2),
                end_time=datetime.now(timezone.utc) - timedelta(days=10-j, hours=1),
                duration_seconds=3600 + (j * 300),  # Varying durations
                success=(j > 2),  # First few sessions might fail
                score=session_score,
                cost=1.0 + (j * 0.1),
                skills_practiced=["reconnaissance", "exploitation", "post_exploitation"][:(j % 3) + 1],
                objectives_completed=min(10, 5 + j),
                objectives_total=10
            )
            
            perf_engine.record_session_performance(session)
            
            # Record cost data
            cost_tracker.record_usage(
                usage_id=f"usage_{session_id}",
                model="openai/gpt-4" if j % 2 == 0 else "anthropic/claude-3-sonnet",
                profile_id=operator_id,
                session_id=session_id,
                task_type=["reconnaissance", "exploitation", "post_exploitation"][j % 3],
                input_tokens=1000 + (j * 100),
                output_tokens=500 + (j * 50),
                latency_ms=1000,
                success=session.success
            )
        
        # Award some certifications for top performer
        if i == 0:
            profile.certifications.append("cert_red_team_foundation")
    
    print(f"✓ Created {len(operators)} operators with 10 sessions each")
    return operators


def demo_performance_metrics(perf_engine, operator_ids):
    """Demonstrate performance metrics features."""
    print_section("1. Performance Metrics Engine")
    
    operator_id = operator_ids[0]
    
    # Get performance analysis
    analysis = perf_engine.analyze_operator_performance(operator_id)
    
    print(f"Operator: {operator_id}")
    print(f"Total Sessions: {analysis['total_sessions']}")
    print(f"Learning Velocity: {analysis['learning_velocity']:.3f}")
    print(f"Plateau Detected: {analysis['plateau_detected']}")
    
    if analysis.get('strengths'):
        print(f"\nStrengths: {', '.join(analysis['strengths'])}")
    
    if analysis.get('weaknesses'):
        print(f"\nTop Weaknesses:")
        for weakness in analysis['weaknesses'][:3]:
            print(f"  - {weakness['skill']}: {weakness['proficiency']}")
    
    # Show trends
    if analysis.get('trends'):
        print(f"\nPerformance Trends:")
        for metric_type, trend in list(analysis['trends'].items())[:3]:
            print(f"  {metric_type}: {trend.get('direction', 'unknown')}")


def demo_training_effectiveness(effectiveness_tracker, perf_engine, operator_ids):
    """Demonstrate training effectiveness features."""
    print_section("2. Training Effectiveness Tracker")
    
    operator_id = operator_ids[0]
    profile = perf_engine.get_operator_profile(operator_id)
    sessions = perf_engine.get_operator_sessions(operator_id)
    
    # Generate recommendations
    recommendations = effectiveness_tracker.generate_recommendations(
        operator_id,
        profile,
        sessions,
        target_role="red_team_expert"
    )
    
    print(f"Training Recommendations for {profile.name}:")
    print(f"Total Recommendations: {len(recommendations)}\n")
    
    for idx, rec in enumerate(recommendations[:3], 1):
        print(f"{idx}. {rec.title} (Priority: {rec.priority})")
        print(f"   Type: {rec.recommendation_type.value}")
        print(f"   {rec.description}")
        print(f"   Estimated Time: {rec.estimated_time.total_seconds()/3600:.1f} hours\n")


def demo_cost_analytics(cost_analytics):
    """Demonstrate advanced cost analytics."""
    print_section("3. Advanced Cost Analytics")
    
    # Get cost breakdown
    breakdown = cost_analytics.get_detailed_breakdown(
        CostCategory.MODEL_USAGE,
        time_range=timedelta(days=30)
    )
    
    print(f"Cost Breakdown by Model:")
    print(f"Total Cost: ${breakdown.total_cost:.2f}")
    print(f"Percentage of Total: {breakdown.percentage_of_total:.1f}%\n")
    
    print("Top Cost Items:")
    for item, cost in breakdown.get_top_items(3):
        print(f"  {item}: ${cost:.2f}")
    
    # Get optimization opportunities
    opportunities = cost_analytics.optimizer.identify_opportunities(
        time_range=timedelta(days=7)
    )
    
    print(f"\nCost Optimization Opportunities: {len(opportunities)}")
    for opp in opportunities[:2]:
        print(f"\n• {opp.title}")
        print(f"  Potential Savings: ${opp.potential_savings:.2f}")
        print(f"  Difficulty: {opp.implementation_difficulty}/5")
        if opp.recommendations:
            print(f"  Recommendation: {opp.recommendations[0]}")


def demo_progress_tracking(progress_tracker, perf_engine, operator_ids):
    """Demonstrate progress tracking features."""
    print_section("4. Progress Tracking System")
    
    operator_id = operator_ids[0]
    profile = perf_engine.get_operator_profile(operator_id)
    
    # Get operator data
    operator_data = {
        'total_sessions': profile.total_sessions,
        'total_hours': profile.total_hours,
        'skills': {k: v.to_dict() for k, v in profile.skills.items()},
        'certifications': profile.certifications,
        'total_xp': progress_tracker.get_operator_xp(operator_id)
    }
    
    # Check milestones
    achievements = progress_tracker.check_and_award_milestones(
        operator_id,
        operator_data
    )
    
    # Get summary
    summary = progress_tracker.get_operator_summary(operator_id, operator_data)
    
    print(f"Progress Summary for {profile.name}:")
    print(f"  Level: {summary['level']}")
    print(f"  Total XP: {summary['total_xp']}")
    print(f"  Achievements: {summary['achievements_count']}")
    print(f"  Certifications: {len(profile.certifications)}")
    
    if achievements:
        print(f"\nRecent Achievements:")
        for achievement in achievements[:3]:
            print(f"  🏆 {achievement.name} (+{achievement.xp_earned} XP)")


def demo_reporting(reporting_engine, perf_engine, operator_ids):
    """Demonstrate reporting engine features."""
    print_section("5. Reporting Engine")
    
    operator_id = operator_ids[0]
    
    # Generate operator progress report
    report = reporting_engine.generate_report(
        ReportType.OPERATOR_PROGRESS,
        operator_id=operator_id
    )
    
    print(f"Generated Report:")
    print(f"  ID: {report.id}")
    print(f"  Type: {report.report_type.value}")
    print(f"  Title: {report.title}")
    print(f"  Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Export to different formats
    print(f"\nExporting to formats:")
    
    # JSON
    json_export = reporting_engine.export_report(report.id, ReportFormat.JSON)
    print(f"  ✓ JSON ({len(json_export)} bytes)")
    
    # Markdown
    md_export = reporting_engine.export_report(report.id, ReportFormat.MARKDOWN)
    print(f"  ✓ Markdown ({len(md_export)} bytes)")
    
    # HTML
    html_export = reporting_engine.export_report(report.id, ReportFormat.HTML)
    print(f"  ✓ HTML ({len(html_export)} bytes)")
    
    # List reports
    reports = reporting_engine.list_reports()
    print(f"\nTotal Reports Generated: {len(reports)}")


def demo_analytics_aggregator(aggregator):
    """Demonstrate analytics aggregator features."""
    print_section("6. Analytics Aggregator & Dashboard")
    
    # Get dashboard data
    dashboard = aggregator.get_dashboard_data()
    summary = dashboard['summary']
    
    print("Dashboard Summary:")
    print(f"  Total Operators: {summary['total_operators']}")
    print(f"  Today's Training Hours: {summary['today_training_hours']}")
    print(f"  Week Cost: ${summary['week_cost']:.2f}")
    print(f"  Average Level: {summary['average_operator_level']}")
    print(f"  7-Day Success Rate: {summary['success_rate_7d']}%")
    
    # Show leaderboard
    print(f"\n📊 XP Leaderboard:")
    for entry in dashboard['xp_leaderboard'][:5]:
        print(f"  {entry['rank']}. {entry['name']} - {entry['xp']} XP (Level {entry['level']})")
    
    # Create and show alerts
    alert = aggregator.alert_manager.create_alert(
        alert_type=AlertType.BUDGET_WARNING,
        priority=AlertPriority.HIGH,
        title="Budget Threshold Reached",
        message="Weekly budget at 85%",
        details={'spent': 85, 'budget': 100}
    )
    
    active_alerts = aggregator.alert_manager.get_active_alerts()
    print(f"\n⚠ Active Alerts: {len(active_alerts)}")
    for alert in active_alerts[:3]:
        print(f"  [{alert.priority.value.upper()}] {alert.title}")


def demo_leaderboards(aggregator):
    """Demonstrate leaderboard features."""
    print_section("7. Competitive Leaderboards")
    
    # XP Leaderboard
    xp_board = aggregator.leaderboard_manager.get_xp_leaderboard(limit=5)
    print("🏆 XP Leaderboard:")
    for entry in xp_board:
        print(f"  #{entry['rank']} - {entry['name']}: {entry['xp']} XP (Level {entry['level']})")
    
    # Activity Leaderboard
    activity_board = aggregator.leaderboard_manager.get_activity_leaderboard(limit=5)
    print("\n📈 Activity Leaderboard:")
    for entry in activity_board:
        print(f"  #{entry['rank']} - {entry['name']}: {entry['total_hours']:.1f} hours ({entry['total_sessions']} sessions)")


def demo_trends(aggregator):
    """Demonstrate trend analysis."""
    print_section("8. Trend Analysis")
    
    perf_trend = aggregator.trend_calculator.calculate_performance_trend(period_days=7)
    cost_trend = aggregator.trend_calculator.calculate_cost_trend(period_days=7)
    
    print(f"7-Day Performance Trend: {perf_trend['trend']}")
    print(f"Data Points: {len(perf_trend['data_points'])}")
    
    print(f"\n7-Day Cost Trend: {cost_trend['trend']}")
    print(f"Total Cost: ${cost_trend['total_cost']:.2f}")


def main():
    """Run Phase 4 analytics demonstration."""
    print("\n" + "="*70)
    print(" ATS MAFIA Framework - Phase 4 Analytics System Demo")
    print("="*70)
    
    try:
        # Initialize all components
        print("\nInitializing analytics system...")
        
        perf_engine = PerformanceMetricsEngine(storage_path="demo_performance.json")
        effectiveness_tracker = TrainingEffectivenessTracker()
        registry = ModelRegistry()
        cost_tracker = CostTracker(registry, storage_path="demo_costs.json")
        cost_analytics = AdvancedCostAnalytics(cost_tracker)
        progress_tracker = ProgressTracker()
        reporting_engine = ReportingEngine(
            perf_engine,
            effectiveness_tracker,
            cost_analytics,
            progress_tracker
        )
        aggregator = AnalyticsAggregator(
            perf_engine,
            effectiveness_tracker,
            cost_tracker,
            progress_tracker
        )
        
        print("✓ All components initialized\n")
        
        # Generate sample data
        operator_ids = generate_sample_data(perf_engine, cost_tracker, progress_tracker)
        
        # Run demonstrations
        demo_performance_metrics(perf_engine, operator_ids)
        demo_training_effectiveness(effectiveness_tracker, perf_engine, operator_ids)
        demo_cost_analytics(cost_analytics)
        demo_progress_tracking(progress_tracker, perf_engine, operator_ids)
        demo_reporting(reporting_engine, perf_engine, operator_ids)
        demo_analytics_aggregator(aggregator)
        demo_leaderboards(aggregator)
        demo_trends(aggregator)
        
        # Final summary
        print_section("Demo Complete - System Verification")
        
        print("✅ Performance Metrics Engine: OPERATIONAL")
        print("✅ Training Effectiveness Tracker: OPERATIONAL")
        print("✅ Advanced Cost Analytics: OPERATIONAL")
        print("✅ Progress Tracking System: OPERATIONAL")
        print("✅ Reporting Engine: OPERATIONAL")
        print("✅ Analytics Aggregator: OPERATIONAL")
        
        print(f"\nSystem Statistics:")
        print(f"  Operators Created: {len(operator_ids)}")
        print(f"  Sessions Recorded: {len(perf_engine.session_performances)}")
        print(f"  Metrics Tracked: {len(perf_engine.metrics)}")
        print(f"  Reports Generated: {len(reporting_engine.reports)}")
        print(f"  Achievements Awarded: {sum(len(a) for a in progress_tracker.achievements.values())}")
        
        print("\n" + "="*70)
        print(" Phase 4 Analytics System: FULLY OPERATIONAL ✅")
        print("="*70 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)