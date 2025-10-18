"""
ATS MAFIA Framework CLI Analytics Commands

This module provides command-line interface commands for accessing analytics
functionality including performance metrics, cost analysis, and reporting.
"""

import click
import json
from typing import Optional
from datetime import timedelta
from tabulate import tabulate
from pathlib import Path

from ..core.performance_metrics import PerformanceMetricsEngine
from ..core.training_effectiveness import TrainingEffectivenessTracker
from ..core.advanced_cost_analytics import AdvancedCostAnalytics, CostCategory
from ..core.progress_tracker import ProgressTracker
from ..core.reporting_engine import ReportingEngine, ReportType, ReportFormat
from ..core.analytics_aggregator import AnalyticsAggregator


def format_table(data: list, headers: list) -> str:
    """Format data as a table."""
    return tabulate(data, headers=headers, tablefmt='grid')


def print_json(data: dict) -> None:
    """Print data as formatted JSON."""
    click.echo(json.dumps(data, indent=2))


@click.group(name='analytics')
def analytics_cli():
    """Analytics and reporting commands."""
    pass


@analytics_cli.command(name='operator-stats')
@click.argument('operator_id')
@click.option('--time-range', '-t', type=int, help='Time range in days')
@click.option('--format', '-f', type=click.Choice(['table', 'json']), default='table')
@click.pass_context
def operator_stats(ctx, operator_id: str, time_range: Optional[int], format: str):
    """Display operator performance summary."""
    # Get components from context (would be initialized in main CLI)
    performance_engine = ctx.obj.get('performance_engine')
    progress_tracker = ctx.obj.get('progress_tracker')
    
    if not performance_engine or not progress_tracker:
        click.echo("Error: Analytics system not initialized", err=True)
        return
    
    # Get operator profile
    profile = performance_engine.get_operator_profile(operator_id)
    if not profile:
        click.echo(f"Error: Operator not found: {operator_id}", err=True)
        return
    
    # Get analysis
    analysis = performance_engine.analyze_operator_performance(operator_id)
    
    # Get progress
    operator_data = {
        'total_sessions': profile.total_sessions,
        'total_hours': profile.total_hours,
        'skills': {k: v.to_dict() for k, v in profile.skills.items()},
        'certifications': profile.certifications,
        'total_xp': progress_tracker.get_operator_xp(operator_id)
    }
    summary = progress_tracker.get_operator_summary(operator_id, operator_data)
    
    if format == 'json':
        print_json({
            'profile': profile.to_dict(),
            'analysis': analysis,
            'summary': summary
        })
    else:
        click.echo(f"\n{'='*60}")
        click.echo(f"Operator Performance Summary: {profile.name}")
        click.echo(f"{'='*60}\n")
        
        # Basic stats
        click.echo("Overview:")
        click.echo(f"  Level: {summary['level']}")
        click.echo(f"  Total XP: {summary['total_xp']}")
        click.echo(f"  Total Sessions: {profile.total_sessions}")
        click.echo(f"  Total Hours: {profile.total_hours:.1f}")
        click.echo(f"  Skill Level: {profile.skill_level.value}")
        click.echo(f"  Achievements: {summary['achievements_count']}")
        click.echo(f"  Certifications: {len(profile.certifications)}\n")
        
        # Skills
        if profile.skills:
            click.echo("Top Skills:")
            skill_data = []
            for name, skill in sorted(
                profile.skills.items(),
                key=lambda x: x[1].proficiency.to_numeric(),
                reverse=True
            )[:5]:
                skill_data.append([
                    name,
                    skill.proficiency.value,
                    f"{skill.success_rate*100:.1f}%",
                    skill.practice_count
                ])
            
            click.echo(format_table(
                skill_data,
                ['Skill', 'Proficiency', 'Success Rate', 'Practice Count']
            ))
        
        # Strengths and weaknesses
        if analysis.get('strengths'):
            click.echo(f"\nStrengths: {', '.join(analysis['strengths'][:5])}")
        
        if analysis.get('weaknesses'):
            click.echo(f"\nWeaknesses:")
            for weakness in analysis['weaknesses'][:3]:
                click.echo(f"  - {weakness['skill']}: {weakness['proficiency']}")


@analytics_cli.command(name='session-analysis')
@click.argument('session_id')
@click.option('--format', '-f', type=click.Choice(['table', 'json']), default='table')
@click.pass_context
def session_analysis(ctx, session_id: str, format: str):
    """Detailed session analysis."""
    performance_engine = ctx.obj.get('performance_engine')
    
    if not performance_engine:
        click.echo("Error: Analytics system not initialized", err=True)
        return
    
    session = performance_engine.session_performances.get(session_id)
    if not session:
        click.echo(f"Error: Session not found: {session_id}", err=True)
        return
    
    if format == 'json':
        print_json(session.to_dict())
    else:
        click.echo(f"\n{'='*60}")
        click.echo(f"Session Analysis: {session_id}")
        click.echo(f"{'='*60}\n")
        
        click.echo(f"Operator: {session.operator_id}")
        click.echo(f"Scenario: {session.scenario_id}")
        click.echo(f"Duration: {session.duration_seconds/3600:.2f} hours")
        click.echo(f"Score: {session.score:.2f}")
        click.echo(f"Success: {'Yes' if session.success else 'No'}")
        click.echo(f"Cost: ${session.cost:.2f}")
        
        click.echo(f"\nMetrics:")
        click.echo(f"  Completion Rate: {session.get_completion_rate()*100:.1f}%")
        click.echo(f"  Time Efficiency: {session.get_time_efficiency():.2f}")
        click.echo(f"  Cost Efficiency: {session.get_cost_efficiency():.2f}")
        
        if session.skills_practiced:
            click.echo(f"\nSkills Practiced: {', '.join(session.skills_practiced)}")


@analytics_cli.command(name='cost-report')
@click.option('--timeframe', '-t', type=int, default=7, help='Timeframe in days')
@click.option('--category', '-c', type=click.Choice(['model', 'profile', 'scenario', 'phase']), default='model')
@click.option('--format', '-f', type=click.Choice(['table', 'json']), default='table')
@click.pass_context
def cost_report(ctx, timeframe: int, category: str, format: str):
    """Cost summary for timeframe."""
    cost_analytics = ctx.obj.get('cost_analytics')
    
    if not cost_analytics:
        click.echo("Error: Cost analytics not initialized", err=True)
        return
    
    # Map CLI category to CostCategory enum
    category_map = {
        'model': CostCategory.MODEL_USAGE,
        'profile': CostCategory.PROFILE,
        'scenario': CostCategory.SCENARIO,
        'phase': CostCategory.PHASE
    }
    
    time_range = timedelta(days=timeframe)
    breakdown = cost_analytics.get_detailed_breakdown(category_map[category], time_range)
    
    if format == 'json':
        print_json(breakdown.to_dict())
    else:
        click.echo(f"\n{'='*60}")
        click.echo(f"Cost Report - Last {timeframe} Days")
        click.echo(f"Category: {category}")
        click.echo(f"{'='*60}\n")
        
        click.echo(f"Total Cost: ${breakdown.total_cost:.2f}")
        click.echo(f"Percentage of Total: {breakdown.percentage_of_total:.1f}%\n")
        
        # Top items
        top_items = breakdown.get_top_items(10)
        if top_items:
            click.echo("Top Cost Items:")
            table_data = [[item, f"${cost:.2f}"] for item, cost in top_items]
            click.echo(format_table(table_data, ['Item', 'Cost']))


@analytics_cli.command(name='leaderboard')
@click.option('--category', '-c', type=click.Choice(['xp', 'activity', 'skill']), default='xp')
@click.option('--skill', '-s', help='Skill name (required for skill leaderboard)')
@click.option('--limit', '-l', type=int, default=10, help='Number of entries to show')
@click.pass_context
def leaderboard(ctx, category: str, skill: Optional[str], limit: int):
    """Show rankings."""
    analytics_aggregator = ctx.obj.get('analytics_aggregator')
    
    if not analytics_aggregator:
        click.echo("Error: Analytics aggregator not initialized", err=True)
        return
    
    # Initialize defaults
    headers = []
    table_data = []
    
    if category == 'xp':
        entries = analytics_aggregator.leaderboard_manager.get_xp_leaderboard(limit)
        headers = ['Rank', 'Operator', 'XP', 'Level']
        table_data = [[e['rank'], e['name'], e['xp'], e['level']] for e in entries]
    elif category == 'activity':
        entries = analytics_aggregator.leaderboard_manager.get_activity_leaderboard(limit)
        headers = ['Rank', 'Operator', 'Sessions', 'Hours']
        table_data = [[e['rank'], e['name'], e['total_sessions'], e['total_hours']] for e in entries]
    elif category == 'skill':
        if not skill:
            click.echo("Error: --skill required for skill leaderboard", err=True)
            return
        entries = analytics_aggregator.leaderboard_manager.get_skill_leaderboard(skill, limit)
        headers = ['Rank', 'Operator', 'Proficiency', 'Avg Score', 'Success Rate']
        table_data = [
            [e['rank'], e['name'], e['proficiency'], f"{e['average_score']:.2f}", f"{e['success_rate']*100:.1f}%"]
            for e in entries
        ]
    
    click.echo(f"\n{'='*60}")
    click.echo(f"Leaderboard - {category.upper()}")
    if skill:
        click.echo(f"Skill: {skill}")
    click.echo(f"{'='*60}\n")
    
    click.echo(format_table(table_data, headers))


@analytics_cli.command(name='skill-gap')
@click.argument('operator_id')
@click.option('--target-role', '-r', help='Target role (e.g., red_team_expert)')
@click.pass_context
def skill_gap(ctx, operator_id: str, target_role: Optional[str]):
    """Identify skill gaps."""
    performance_engine = ctx.obj.get('performance_engine')
    effectiveness_tracker = ctx.obj.get('effectiveness_tracker')
    
    if not performance_engine or not effectiveness_tracker:
        click.echo("Error: Analytics system not initialized", err=True)
        return
    
    profile = performance_engine.get_operator_profile(operator_id)
    if not profile:
        click.echo(f"Error: Operator not found: {operator_id}", err=True)
        return
    
    gaps = effectiveness_tracker.get_skill_gaps(profile, target_role)
    
    click.echo(f"\n{'='*60}")
    click.echo(f"Skill Gap Analysis: {profile.name}")
    if target_role:
        click.echo(f"Target Role: {target_role}")
    click.echo(f"{'='*60}\n")
    
    if not gaps:
        click.echo("No skill gaps identified!")
        return
    
    table_data = []
    for gap in gaps:
        table_data.append([
            gap.skill_name,
            gap.current_level.value,
            gap.target_level.value,
            gap.gap_size,
            gap.priority
        ])
    
    click.echo(format_table(
        table_data,
        ['Skill', 'Current', 'Target', 'Gap', 'Priority']
    ))
    
    # Show recommendations for top gap
    if gaps[0].recommended_actions:
        click.echo(f"\nTop Priority: {gaps[0].skill_name}")
        click.echo("Recommendations:")
        for action in gaps[0].recommended_actions:
            click.echo(f"  - {action}")


@analytics_cli.command(name='training-plan')
@click.argument('operator_id')
@click.option('--target-role', '-r', help='Target role')
@click.pass_context
def training_plan(ctx, operator_id: str, target_role: Optional[str]):
    """Generate personalized training plan."""
    performance_engine = ctx.obj.get('performance_engine')
    effectiveness_tracker = ctx.obj.get('effectiveness_tracker')
    
    if not performance_engine or not effectiveness_tracker:
        click.echo("Error: Analytics system not initialized", err=True)
        return
    
    profile = performance_engine.get_operator_profile(operator_id)
    if not profile:
        click.echo(f"Error: Operator not found: {operator_id}", err=True)
        return
    
    recent_sessions = performance_engine.get_operator_sessions(operator_id, limit=20)
    recommendations = effectiveness_tracker.generate_recommendations(
        operator_id, profile, recent_sessions, target_role
    )
    
    click.echo(f"\n{'='*60}")
    click.echo(f"Training Plan: {profile.name}")
    click.echo(f"{'='*60}\n")
    
    if not recommendations:
        click.echo("No recommendations at this time.")
        return
    
    for idx, rec in enumerate(recommendations[:5], 1):
        click.echo(f"{idx}. {rec.title} (Priority: {rec.priority})")
        click.echo(f"   Type: {rec.recommendation_type.value}")
        click.echo(f"   {rec.description}")
        click.echo(f"   Estimated Time: {rec.estimated_time.total_seconds()/3600:.1f} hours")
        if rec.suggested_scenarios:
            click.echo(f"   Scenarios: {', '.join(rec.suggested_scenarios[:3])}")
        click.echo()


@analytics_cli.command(name='benchmark')
@click.argument('operator_id')
@click.pass_context
def benchmark(ctx, operator_id: str):
    """Compare against benchmarks."""
    performance_engine = ctx.obj.get('performance_engine')
    progress_tracker = ctx.obj.get('progress_tracker')
    
    if not performance_engine or not progress_tracker:
        click.echo("Error: Analytics system not initialized", err=True)
        return
    
    profile = performance_engine.get_operator_profile(operator_id)
    if not profile:
        click.echo(f"Error: Operator not found: {operator_id}", err=True)
        return
    
    # Get all operators for comparison
    all_operators = list(performance_engine.operator_profiles.values())
    
    if len(all_operators) < 2:
        click.echo("Insufficient data for benchmarking")
        return
    
    # Calculate statistics
    xp_values = [progress_tracker.get_operator_xp(op.operator_id) for op in all_operators]
    session_counts = [op.total_sessions for op in all_operators]
    hours_values = [op.total_hours for op in all_operators]
    
    operator_xp = progress_tracker.get_operator_xp(operator_id)
    operator_rank_xp = sorted(xp_values, reverse=True).index(operator_xp) + 1
    
    click.echo(f"\n{'='*60}")
    click.echo(f"Benchmark Report: {profile.name}")
    click.echo(f"{'='*60}\n")
    
    click.echo(f"XP Ranking: #{operator_rank_xp} of {len(all_operators)}")
    click.echo(f"Your XP: {operator_xp} (Avg: {sum(xp_values)/len(xp_values):.0f})")
    click.echo(f"Your Sessions: {profile.total_sessions} (Avg: {sum(session_counts)/len(session_counts):.0f})")
    click.echo(f"Your Hours: {profile.total_hours:.1f} (Avg: {sum(hours_values)/len(hours_values):.1f})")


@analytics_cli.command(name='export-report')
@click.argument('report_type', type=click.Choice(['operator', 'team', 'cost', 'trends']))
@click.argument('output_path', type=click.Path())
@click.option('--format', '-f', type=click.Choice(['json', 'csv', 'html', 'markdown']), default='json')
@click.option('--operator-id', '-o', help='Operator ID (for operator report)')
@click.option('--days', '-d', type=int, default=30, help='Time range in days')
@click.pass_context
def export_report(ctx, report_type: str, output_path: str, format: str, operator_id: Optional[str], days: int):
    """Export reports."""
    reporting_engine = ctx.obj.get('reporting_engine')
    performance_engine = ctx.obj.get('performance_engine')
    
    if not reporting_engine:
        click.echo("Error: Reporting engine not initialized", err=True)
        return
    
    # Map CLI type to ReportType
    type_map = {
        'operator': ReportType.OPERATOR_PROGRESS,
        'team': ReportType.TEAM_PERFORMANCE,
        'cost': ReportType.COST_SUMMARY,
        'trends': ReportType.TREND_ANALYSIS
    }
    
    format_map = {
        'json': ReportFormat.JSON,
        'csv': ReportFormat.CSV,
        'html': ReportFormat.HTML,
        'markdown': ReportFormat.MARKDOWN
    }
    
    # Generate report
    try:
        if report_type == 'operator':
            if not operator_id:
                click.echo("Error: --operator-id required for operator report", err=True)
                return
            report = reporting_engine.generate_report(
                type_map[report_type],
                operator_id=operator_id,
                time_range=timedelta(days=days)
            )
        elif report_type == 'team':
            operator_ids = list(performance_engine.operator_profiles.keys())
            report = reporting_engine.generate_report(
                type_map[report_type],
                operator_ids=operator_ids
            )
        else:
            report = reporting_engine.generate_report(
                type_map[report_type],
                time_range=timedelta(days=days)
            )
        
        # Export
        content = reporting_engine.export_report(report.id, format_map[format])
        
        # Write to file
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(content, encoding='utf-8')
        
        click.echo(f"Report exported to: {output_path}")
        click.echo(f"Report ID: {report.id}")
        
    except Exception as e:
        click.echo(f"Error generating report: {e}", err=True)


@analytics_cli.command(name='dashboard')
@click.pass_context
def dashboard(ctx):
    """Display dashboard summary."""
    analytics_aggregator = ctx.obj.get('analytics_aggregator')
    
    if not analytics_aggregator:
        click.echo("Error: Analytics aggregator not initialized", err=True)
        return
    
    data = analytics_aggregator.get_dashboard_data()
    summary = data['summary']
    
    click.echo(f"\n{'='*60}")
    click.echo("ATS MAFIA Analytics Dashboard")
    click.echo(f"{'='*60}\n")
    
    click.echo("System Overview:")
    click.echo(f"  Active Sessions: {summary['active_sessions']}")
    click.echo(f"  Today's Training Hours: {summary['today_training_hours']}")
    click.echo(f"  This Week's Cost: ${summary['week_cost']:.2f}")
    click.echo(f"  Total Operators: {summary['total_operators']}")
    click.echo(f"  Total Achievements: {summary['total_achievements']}")
    click.echo(f"  Average Operator Level: {summary['average_operator_level']}")
    
    click.echo(f"\nPerformance:")
    click.echo(f"  7-Day Success Rate: {summary['success_rate_7d']}%")
    click.echo(f"  Cost Efficiency Trend: {summary['cost_efficiency_trend']}")
    
    # Show top performers
    if data.get('xp_leaderboard'):
        click.echo(f"\nTop Performers:")
        for entry in data['xp_leaderboard'][:5]:
            click.echo(f"  {entry['rank']}. {entry['name']} - {entry['xp']} XP (Level {entry['level']})")
    
    # Show alerts
    if data.get('critical_alerts'):
        click.echo(f"\n⚠ Critical Alerts: {len(data['critical_alerts'])}")
        for alert in data['critical_alerts'][:3]:
            click.echo(f"  - {alert['title']}")


# Export the CLI group for integration with main CLI
__all__ = ['analytics_cli']