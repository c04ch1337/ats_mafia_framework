"""
ATS MAFIA Framework Reporting Engine

This module provides comprehensive report generation capabilities including
operator progress, cost analysis, training effectiveness, and system health reports.
"""

import logging
import json
import csv
from io import StringIO
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from abc import ABC, abstractmethod

from .performance_metrics import PerformanceMetricsEngine, OperatorProfile
from .training_effectiveness import TrainingEffectivenessTracker
from .advanced_cost_analytics import AdvancedCostAnalytics
from .progress_tracker import ProgressTracker
from .cost_tracker import CostTracker


class ReportType(Enum):
    """Types of reports that can be generated."""
    OPERATOR_PROGRESS = "operator_progress"
    SESSION_ANALYSIS = "session_analysis"
    COST_SUMMARY = "cost_summary"
    TRAINING_EFFECTIVENESS = "training_effectiveness"
    SYSTEM_HEALTH = "system_health"
    TEAM_PERFORMANCE = "team_performance"
    TREND_ANALYSIS = "trend_analysis"
    COMPLIANCE = "compliance"


class ReportFormat(Enum):
    """Export formats for reports."""
    JSON = "json"
    CSV = "csv"
    HTML = "html"
    PDF = "pdf"
    MARKDOWN = "markdown"


@dataclass
class Report:
    """
    Base report with metadata and export capabilities.
    
    Attributes:
        id: Unique identifier
        report_type: Type of report
        title: Report title
        description: Report description
        generated_at: When report was generated
        generated_by: Who generated the report
        data: Report data
        metadata: Additional metadata
    """
    id: str
    report_type: ReportType
    title: str
    description: str
    generated_at: datetime
    generated_by: str
    data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {
            'id': self.id,
            'report_type': self.report_type.value,
            'title': self.title,
            'description': self.description,
            'generated_at': self.generated_at.isoformat(),
            'generated_by': self.generated_by,
            'data': self.data,
            'metadata': self.metadata
        }
    
    def to_json(self) -> str:
        """Export report as JSON."""
        return json.dumps(self.to_dict(), indent=2)
    
    def to_csv(self) -> str:
        """
        Export report as CSV.
        
        Note: This is a simplified CSV export. Complex nested data
        may not be fully represented.
        """
        output = StringIO()
        
        # Extract flat data for CSV
        flat_data = self._flatten_data(self.data)
        
        if not flat_data:
            return ""
        
        # Write CSV
        writer = csv.DictWriter(output, fieldnames=flat_data[0].keys())
        writer.writeheader()
        writer.writerows(flat_data)
        
        return output.getvalue()
    
    def _flatten_data(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Flatten nested data for CSV export."""
        # Simple flattening - override in subclasses for custom behavior
        if isinstance(data, dict):
            return [data]
        elif isinstance(data, list):
            return data
        else:
            return [{'value': str(data)}]
    
    def to_markdown(self) -> str:
        """Export report as Markdown."""
        md = []
        
        # Header
        md.append(f"# {self.title}\n")
        md.append(f"{self.description}\n")
        md.append(f"**Generated:** {self.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
        md.append(f"**Report ID:** {self.id}\n")
        md.append("---\n")
        
        # Data section
        md.append("## Report Data\n")
        md.append(self._dict_to_markdown(self.data))
        
        return "\n".join(md)
    
    def _dict_to_markdown(self, data: Dict[str, Any], level: int = 3) -> str:
        """Convert dictionary to markdown format."""
        md = []
        
        for key, value in data.items():
            heading = "#" * level
            md.append(f"{heading} {key.replace('_', ' ').title()}\n")
            
            if isinstance(value, dict):
                md.append(self._dict_to_markdown(value, level + 1))
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        md.append(self._dict_to_markdown(item, level + 1))
                    else:
                        md.append(f"- {item}\n")
            else:
                md.append(f"{value}\n")
        
        return "\n".join(md)


class ReportGenerator(ABC):
    """Abstract base class for report generators."""
    
    def __init__(self):
        """Initialize report generator."""
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def generate(self, *args, **kwargs) -> Report:
        """
        Generate the report.
        
        Returns:
            Generated report
        """
        pass


class OperatorProgressReport(ReportGenerator):
    """Generate individual operator progress reports."""
    
    def __init__(self,
                 performance_engine: PerformanceMetricsEngine,
                 effectiveness_tracker: TrainingEffectivenessTracker,
                 progress_tracker: ProgressTracker):
        """
        Initialize operator progress report generator.
        
        Args:
            performance_engine: Performance metrics engine
            effectiveness_tracker: Training effectiveness tracker
            progress_tracker: Progress tracker
        """
        super().__init__()
        self.performance_engine = performance_engine
        self.effectiveness_tracker = effectiveness_tracker
        self.progress_tracker = progress_tracker
    
    def generate(self,
                operator_id: str,
                time_range: Optional[timedelta] = None,
                **kwargs) -> Report:
        """
        Generate operator progress report.
        
        Args:
            operator_id: Operator identifier
            time_range: Optional time range for analysis
            
        Returns:
            Operator progress report
        """
        # Get operator profile
        profile = self.performance_engine.get_operator_profile(operator_id)
        if not profile:
            raise ValueError(f"Operator not found: {operator_id}")
        
        # Get performance analysis
        performance_analysis = self.performance_engine.analyze_operator_performance(operator_id)
        
        # Get training effectiveness stats
        effectiveness_stats = self.effectiveness_tracker.get_training_statistics(operator_id)
        
        # Get progress summary
        operator_data = {
            'total_sessions': profile.total_sessions,
            'total_hours': profile.total_hours,
            'skills': {k: v.to_dict() for k, v in profile.skills.items()},
            'certifications': profile.certifications,
            'total_xp': self.progress_tracker.get_operator_xp(operator_id)
        }
        progress_summary = self.progress_tracker.get_operator_summary(operator_id, operator_data)
        
        # Get recent sessions
        recent_sessions = self.performance_engine.get_operator_sessions(operator_id, limit=10)
        
        # Compile report data
        report_data = {
            'operator_id': operator_id,
            'operator_name': profile.name,
            'summary': {
                'level': progress_summary['level'],
                'total_xp': progress_summary['total_xp'],
                'total_sessions': profile.total_sessions,
                'total_hours': profile.total_hours,
                'skill_level': profile.skill_level.value,
                'achievements_count': progress_summary['achievements_count'],
                'certifications_count': len(profile.certifications)
            },
            'performance_analysis': performance_analysis,
            'skills': {
                name: {
                    'proficiency': skill.proficiency.value,
                    'practice_count': skill.practice_count,
                    'success_rate': skill.success_rate,
                    'average_score': skill.average_score
                }
                for name, skill in profile.skills.items()
            },
            'training_effectiveness': effectiveness_stats,
            'recent_sessions': [
                {
                    'session_id': s.session_id,
                    'scenario_id': s.scenario_id,
                    'duration_hours': s.duration_seconds / 3600,
                    'score': s.score,
                    'success': s.success,
                    'completion_rate': s.get_completion_rate()
                }
                for s in recent_sessions
            ],
            'achievements': [
                a.to_dict() 
                for a in self.progress_tracker.get_operator_achievements(operator_id)
            ],
            'certifications': profile.certifications
        }
        
        return Report(
            id=f"report_op_progress_{operator_id}_{int(datetime.now(timezone.utc).timestamp())}",
            report_type=ReportType.OPERATOR_PROGRESS,
            title=f"Operator Progress Report: {profile.name}",
            description=f"Comprehensive progress report for operator {profile.name}",
            generated_at=datetime.now(timezone.utc),
            generated_by="system",
            data=report_data
        )


class TeamPerformanceReport(ReportGenerator):
    """Generate team aggregate performance reports."""
    
    def __init__(self,
                 performance_engine: PerformanceMetricsEngine,
                 progress_tracker: ProgressTracker):
        """
        Initialize team performance report generator.
        
        Args:
            performance_engine: Performance metrics engine
            progress_tracker: Progress tracker
        """
        super().__init__()
        self.performance_engine = performance_engine
        self.progress_tracker = progress_tracker
    
    def generate(self,
                operator_ids: List[str],
                time_range: Optional[timedelta] = None,
                **kwargs) -> Report:
        """
        Generate team performance report.
        
        Args:
            operator_ids: List of operator identifiers
            time_range: Optional time range for analysis
            
        Returns:
            Team performance report
        """
        team_data = {
            'team_size': len(operator_ids),
            'operators': [],
            'aggregate_stats': {
                'total_sessions': 0,
                'total_hours': 0.0,
                'total_xp': 0,
                'average_level': 0.0,
                'total_achievements': 0,
                'total_certifications': 0
            },
            'skill_distribution': {},
            'top_performers': []
        }
        
        operator_scores = []
        
        for operator_id in operator_ids:
            profile = self.performance_engine.get_operator_profile(operator_id)
            if not profile:
                continue
            
            xp = self.progress_tracker.get_operator_xp(operator_id)
            level = self.progress_tracker.get_operator_level(operator_id)
            achievements = len(self.progress_tracker.get_operator_achievements(operator_id))
            
            operator_info = {
                'operator_id': operator_id,
                'name': profile.name,
                'level': level,
                'xp': xp,
                'sessions': profile.total_sessions,
                'hours': profile.total_hours,
                'skill_level': profile.skill_level.value,
                'achievements': achievements,
                'certifications': len(profile.certifications)
            }
            
            team_data['operators'].append(operator_info)
            operator_scores.append((operator_id, xp))
            
            # Update aggregates
            team_data['aggregate_stats']['total_sessions'] += profile.total_sessions
            team_data['aggregate_stats']['total_hours'] += profile.total_hours
            team_data['aggregate_stats']['total_xp'] += xp
            team_data['aggregate_stats']['total_achievements'] += achievements
            team_data['aggregate_stats']['total_certifications'] += len(profile.certifications)
            
            # Track skill distribution
            for skill_name, skill in profile.skills.items():
                if skill_name not in team_data['skill_distribution']:
                    team_data['skill_distribution'][skill_name] = {
                        'count': 0,
                        'levels': []
                    }
                team_data['skill_distribution'][skill_name]['count'] += 1
                team_data['skill_distribution'][skill_name]['levels'].append(
                    skill.proficiency.to_numeric()
                )
        
        # Calculate averages
        if operator_ids:
            team_data['aggregate_stats']['average_level'] = (
                sum(op['level'] for op in team_data['operators']) / len(operator_ids)
            )
        
        # Get top performers
        operator_scores.sort(key=lambda x: x[1], reverse=True)
        team_data['top_performers'] = [
            {'operator_id': op_id, 'xp': xp}
            for op_id, xp in operator_scores[:5]
        ]
        
        return Report(
            id=f"report_team_perf_{int(datetime.now(timezone.utc).timestamp())}",
            report_type=ReportType.TEAM_PERFORMANCE,
            title="Team Performance Report",
            description=f"Aggregate performance metrics for {len(operator_ids)} operators",
            generated_at=datetime.now(timezone.utc),
            generated_by="system",
            data=team_data
        )


class CostAnalysisReport(ReportGenerator):
    """Generate detailed cost analysis reports."""
    
    def __init__(self, cost_analytics: AdvancedCostAnalytics):
        """
        Initialize cost analysis report generator.
        
        Args:
            cost_analytics: Advanced cost analytics
        """
        super().__init__()
        self.cost_analytics = cost_analytics
    
    def generate(self,
                session_id: Optional[str] = None,
                time_range: Optional[timedelta] = None,
                **kwargs) -> Report:
        """
        Generate cost analysis report.
        
        Args:
            session_id: Optional session filter
            time_range: Optional time range filter
            
        Returns:
            Cost analysis report
        """
        # Generate comprehensive cost report
        cost_report = self.cost_analytics.generate_comprehensive_report(
            session_id=session_id,
            time_range=time_range
        )
        
        # Get optimization opportunities
        opportunities = self.cost_analytics.optimizer.identify_opportunities(
            session_id=session_id,
            time_range=time_range
        )
        
        # Calculate optimization impact
        impact = self.cost_analytics.optimizer.calculate_optimization_impact(opportunities)
        
        report_data = {
            'cost_summary': cost_report.get('global_stats', {}),
            'breakdowns': cost_report.get('breakdowns', {}),
            'optimization_opportunities': [o.to_dict() for o in opportunities],
            'optimization_impact': impact,
            'anomalies': cost_report.get('anomalies', [])
        }
        
        title = "Cost Analysis Report"
        if session_id:
            title += f" - Session {session_id}"
        if time_range:
            title += f" - Last {time_range.days} days"
        
        return Report(
            id=f"report_cost_{int(datetime.now(timezone.utc).timestamp())}",
            report_type=ReportType.COST_SUMMARY,
            title=title,
            description="Detailed cost breakdown and optimization recommendations",
            generated_at=datetime.now(timezone.utc),
            generated_by="system",
            data=report_data
        )


class TrendAnalysisReport(ReportGenerator):
    """Generate performance trend analysis reports."""
    
    def __init__(self, performance_engine: PerformanceMetricsEngine):
        """
        Initialize trend analysis report generator.
        
        Args:
            performance_engine: Performance metrics engine
        """
        super().__init__()
        self.performance_engine = performance_engine
    
    def generate(self,
                operator_id: Optional[str] = None,
                time_range: timedelta = timedelta(days=30),
                **kwargs) -> Report:
        """
        Generate trend analysis report.
        
        Args:
            operator_id: Optional operator filter
            time_range: Time range for analysis
            
        Returns:
            Trend analysis report
        """
        if operator_id:
            # Single operator trends
            analysis = self.performance_engine.analyze_operator_performance(operator_id)
            trends = analysis.get('trends', {})
            
            report_data = {
                'operator_id': operator_id,
                'time_range_days': time_range.days,
                'trends': trends
            }
            
            title = f"Trend Analysis - Operator {operator_id}"
        else:
            # System-wide trends
            report_data = {
                'time_range_days': time_range.days,
                'system_trends': {}
            }
            
            title = "System-Wide Trend Analysis"
        
        return Report(
            id=f"report_trends_{int(datetime.now(timezone.utc).timestamp())}",
            report_type=ReportType.TREND_ANALYSIS,
            title=title,
            description=f"Performance trends over the last {time_range.days} days",
            generated_at=datetime.now(timezone.utc),
            generated_by="system",
            data=report_data
        )


class ComplianceReport(ReportGenerator):
    """Generate training compliance reports."""
    
    def __init__(self,
                 performance_engine: PerformanceMetricsEngine,
                 progress_tracker: ProgressTracker):
        """
        Initialize compliance report generator.
        
        Args:
            performance_engine: Performance metrics engine
            progress_tracker: Progress tracker
        """
        super().__init__()
        self.performance_engine = performance_engine
        self.progress_tracker = progress_tracker
    
    def generate(self,
                operator_ids: List[str],
                requirements: Dict[str, Any],
                **kwargs) -> Report:
        """
        Generate compliance report.
        
        Args:
            operator_ids: List of operator identifiers
            requirements: Compliance requirements
            
        Returns:
            Compliance report
        """
        compliance_data = {
            'total_operators': len(operator_ids),
            'compliant_operators': 0,
            'non_compliant_operators': 0,
            'operator_status': []
        }
        
        required_hours = requirements.get('min_hours', 0)
        required_certifications = requirements.get('required_certifications', [])
        
        for operator_id in operator_ids:
            profile = self.performance_engine.get_operator_profile(operator_id)
            if not profile:
                continue
            
            status = {
                'operator_id': operator_id,
                'name': profile.name,
                'hours': profile.total_hours,
                'certifications': profile.certifications,
                'compliant': True,
                'issues': []
            }
            
            # Check hours requirement
            if profile.total_hours < required_hours:
                status['compliant'] = False
                status['issues'].append(
                    f"Insufficient training hours: {profile.total_hours:.1f}/{required_hours}"
                )
            
            # Check certification requirements
            for req_cert in required_certifications:
                if req_cert not in profile.certifications:
                    status['compliant'] = False
                    status['issues'].append(f"Missing certification: {req_cert}")
            
            compliance_data['operator_status'].append(status)
            
            if status['compliant']:
                compliance_data['compliant_operators'] += 1
            else:
                compliance_data['non_compliant_operators'] += 1
        
        # Calculate compliance rate
        if operator_ids:
            compliance_data['compliance_rate'] = (
                compliance_data['compliant_operators'] / len(operator_ids) * 100
            )
        else:
            compliance_data['compliance_rate'] = 0.0
        
        return Report(
            id=f"report_compliance_{int(datetime.now(timezone.utc).timestamp())}",
            report_type=ReportType.COMPLIANCE,
            title="Training Compliance Report",
            description="Organizational training compliance status",
            generated_at=datetime.now(timezone.utc),
            generated_by="system",
            data=compliance_data
        )


class ReportingEngine:
    """
    Main reporting engine.
    
    Coordinates all report generation and provides unified access
    to various report types with multiple export formats.
    """
    
    def __init__(self,
                 performance_engine: PerformanceMetricsEngine,
                 effectiveness_tracker: TrainingEffectivenessTracker,
                 cost_analytics: AdvancedCostAnalytics,
                 progress_tracker: ProgressTracker):
        """
        Initialize reporting engine.
        
        Args:
            performance_engine: Performance metrics engine
            effectiveness_tracker: Training effectiveness tracker
            cost_analytics: Advanced cost analytics
            progress_tracker: Progress tracker
        """
        self.logger = logging.getLogger("reporting_engine")
        
        # Store components
        self.performance_engine = performance_engine
        self.effectiveness_tracker = effectiveness_tracker
        self.cost_analytics = cost_analytics
        self.progress_tracker = progress_tracker
        
        # Initialize report generators
        self.generators: Dict[ReportType, ReportGenerator] = {
            ReportType.OPERATOR_PROGRESS: OperatorProgressReport(
                performance_engine, effectiveness_tracker, progress_tracker
            ),
            ReportType.TEAM_PERFORMANCE: TeamPerformanceReport(
                performance_engine, progress_tracker
            ),
            ReportType.COST_SUMMARY: CostAnalysisReport(cost_analytics),
            ReportType.TREND_ANALYSIS: TrendAnalysisReport(performance_engine),
            ReportType.COMPLIANCE: ComplianceReport(
                performance_engine, progress_tracker
            )
        }
        
        # Report storage
        self.reports: Dict[str, Report] = {}
    
    def generate_report(self,
                       report_type: ReportType,
                       **kwargs) -> Report:
        """
        Generate a report of the specified type.
        
        Args:
            report_type: Type of report to generate
            **kwargs: Report-specific parameters
            
        Returns:
            Generated report
        """
        generator = self.generators.get(report_type)
        if not generator:
            raise ValueError(f"No generator for report type: {report_type.value}")
        
        try:
            report = generator.generate(**kwargs)
            self.reports[report.id] = report
            
            self.logger.info(f"Generated report: {report.id} ({report_type.value})")
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating report: {e}")
            raise
    
    def get_report(self, report_id: str) -> Optional[Report]:
        """
        Get a previously generated report.
        
        Args:
            report_id: Report identifier
            
        Returns:
            Report or None if not found
        """
        return self.reports.get(report_id)
    
    def export_report(self,
                     report_id: str,
                     format: ReportFormat) -> str:
        """
        Export a report in the specified format.
        
        Args:
            report_id: Report identifier
            format: Export format
            
        Returns:
            Exported report content
        """
        report = self.get_report(report_id)
        if not report:
            raise ValueError(f"Report not found: {report_id}")
        
        if format == ReportFormat.JSON:
            return report.to_json()
        elif format == ReportFormat.CSV:
            return report.to_csv()
        elif format == ReportFormat.MARKDOWN:
            return report.to_markdown()
        elif format == ReportFormat.HTML:
            return self._export_html(report)
        elif format == ReportFormat.PDF:
            # PDF generation would require additional libraries
            raise NotImplementedError("PDF export not yet implemented")
        else:
            raise ValueError(f"Unsupported format: {format.value}")
    
    def _export_html(self, report: Report) -> str:
        """
        Export report as HTML.
        
        Args:
            report: Report to export
            
        Returns:
            HTML content
        """
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{report.title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        h2 {{ color: #666; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .metadata {{ color: #999; font-size: 0.9em; }}
    </style>
</head>
<body>
    <h1>{report.title}</h1>
    <p>{report.description}</p>
    <p class="metadata">
        Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}<br>
        Report ID: {report.id}
    </p>
    <hr>
    <h2>Report Data</h2>
    <pre>{json.dumps(report.data, indent=2)}</pre>
</body>
</html>
"""
        return html
    
    def list_reports(self,
                    report_type: Optional[ReportType] = None) -> List[Dict[str, Any]]:
        """
        List generated reports.
        
        Args:
            report_type: Optional filter by report type
            
        Returns:
            List of report metadata
        """
        reports = []
        
        for report in self.reports.values():
            if report_type and report.report_type != report_type:
                continue
            
            reports.append({
                'id': report.id,
                'type': report.report_type.value,
                'title': report.title,
                'generated_at': report.generated_at.isoformat()
            })
        
        # Sort by generation time (newest first)
        reports.sort(key=lambda r: r['generated_at'], reverse=True)
        
        return reports
    
    def delete_report(self, report_id: str) -> bool:
        """
        Delete a report.
        
        Args:
            report_id: Report identifier
            
        Returns:
            True if deleted, False if not found
        """
        if report_id in self.reports:
            del self.reports[report_id]
            self.logger.info(f"Deleted report: {report_id}")
            return True
        return False