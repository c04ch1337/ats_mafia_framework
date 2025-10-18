# Phase 4: Performance Analytics & Cost Tracking System

## Overview

The Phase 4 Analytics System provides comprehensive performance measurement, cost optimization, and training effectiveness tracking for the ATS MAFIA Framework. This enterprise-grade analytics platform enables data-driven decision making and continuous improvement of operator training.

## Quick Start

### Initialization

```python
from ats_mafia_framework.core.performance_metrics import PerformanceMetricsEngine
from ats_mafia_framework.core.training_effectiveness import TrainingEffectivenessTracker
from ats_mafia_framework.core.advanced_cost_analytics import AdvancedCostAnalytics
from ats_mafia_framework.core.progress_tracker import ProgressTracker
from ats_mafia_framework.core.reporting_engine import ReportingEngine
from ats_mafia_framework.core.analytics_aggregator import AnalyticsAggregator
from ats_mafia_framework.core.cost_tracker import CostTracker
from ats_mafia_framework.core.llm_models import ModelRegistry

# Initialize core components
registry = ModelRegistry()
cost_tracker = CostTracker(registry, storage_path="data/llm_usage.json")
perf_engine = PerformanceMetricsEngine(storage_path="data/performance.json")
effectiveness_tracker = TrainingEffectivenessTracker()
cost_analytics = AdvancedCostAnalytics(cost_tracker)
progress_tracker = ProgressTracker()

# Initialize reporting and aggregation
reporting_engine = ReportingEngine(
    perf_engine, effectiveness_tracker, cost_analytics, progress_tracker
)
analytics_aggregator = AnalyticsAggregator(
    perf_engine, effectiveness_tracker, cost_tracker, progress_tracker
)
```

### Running the Demo

```bash
cd ats_mafia_framework/tests
python demo_phase4_analytics.py
```

### Running Tests

```bash
cd ats_mafia_framework/tests
python test_phase4_analytics.py
```

## Core Components

### 1. Performance Metrics Engine

**Purpose:** Track and analyze operator performance across multiple dimensions.

**Key Classes:**
- `PerformanceMetricsEngine` - Main metrics tracking system
- `OperatorProfile` - Comprehensive operator data
- `SessionPerformance` - Detailed session analysis
- `PerformanceAnalyzer` - Trend analysis and insights
- `BenchmarkEngine` - Comparative analysis

**Example Usage:**

```python
# Create operator profile
profile = perf_engine.create_operator_profile(
    operator_id="op_001",
    name="John Doe",
    metadata={'team': 'red_team'}
)

# Record session performance
session = SessionPerformance(
    session_id="session_001",
    operator_id="op_001",
    scenario_id="pentest_001",
    start_time=datetime.now(timezone.utc) - timedelta(hours=2),
    end_time=datetime.now(timezone.utc),
    duration_seconds=7200,
    success=True,
    score=0.85,
    cost=2.50,
    skills_practiced=["reconnaissance", "exploitation"],
    objectives_completed=8,
    objectives_total=10
)
perf_engine.record_session_performance(session)

# Analyze performance
analysis = perf_engine.analyze_operator_performance("op_001")
print(f"Learning velocity: {analysis['learning_velocity']}")
print(f"Strengths: {analysis['strengths']}")
```

### 2. Training Effectiveness Tracker

**Purpose:** Measure actual learning outcomes and skill retention.

**Key Classes:**
- `TrainingEffectivenessTracker` - Main effectiveness tracking
- `LearningCurve` - Track improvement over time
- `RetentionAnalysis` - Measure knowledge retention
- `SkillGapAnalyzer` - Identify weak areas
- `TrainingRecommendation` - AI-driven suggestions

**Example Usage:**

```python
# Track learning progress
curve = effectiveness_tracker.track_learning_progress(
    operator_id="op_001",
    skill_name="exploitation",
    timestamp=datetime.now(timezone.utc),
    score=0.75
)

# Get skill gaps
gaps = effectiveness_tracker.get_skill_gaps(
    operator_profile=profile,
    target_role="red_team_expert"
)

# Generate recommendations
recommendations = effectiveness_tracker.generate_recommendations(
    operator_id="op_001",
    operator_profile=profile,
    recent_sessions=sessions,
    target_role="red_team_expert"
)

for rec in recommendations:
    print(f"{rec.title}: {rec.description}")
```

### 3. Advanced Cost Analytics

**Purpose:** Enhanced cost optimization and ROI analysis.

**Key Classes:**
- `AdvancedCostAnalytics` - Main analytics system
- `CostOptimizer` - Identify savings opportunities
- `ROICalculator` - Calculate training ROI
- `BudgetPlanner` - Predictive budget planning
- `CostAnomalyDetector` - Detect unusual spending

**Example Usage:**

```python
# Get cost breakdown
breakdown = cost_analytics.get_detailed_breakdown(
    CostCategory.MODEL_USAGE,
    time_range=timedelta(days=30)
)
print(f"Total cost: ${breakdown.total_cost:.2f}")

# Find optimization opportunities
opportunities = cost_analytics.optimizer.identify_opportunities(
    time_range=timedelta(days=7)
)
for opp in opportunities:
    print(f"{opp.title}: ${opp.potential_savings:.2f} savings")

# Calculate ROI
roi = cost_analytics.roi_calculator.calculate_training_roi(
    total_cost=500.0,
    initial_skill_level=1.0,
    final_skill_level=4.0,
    training_hours=40.0,
    certifications=2
)
print(f"ROI: {roi.overall_roi:.2f}")
```

### 4. Progress Tracking System

**Purpose:** Track achievements, milestones, and certifications.

**Key Classes:**
- `ProgressTracker` - Main progress tracking
- `Milestone` - Achievement milestones
- `Achievement` - Unlockable achievements
- `GoalTracker` - Goal management
- `CertificationManager` - Certification tracking

**Example Usage:**

```python
# Check and award milestones
operator_data = {
    'total_sessions': profile.total_sessions,
    'total_hours': profile.total_hours,
    'skills': {k: v.to_dict() for k, v in profile.skills.items()},
    'certifications': profile.certifications,
    'total_xp': progress_tracker.get_operator_xp("op_001")
}

achievements = progress_tracker.check_and_award_milestones(
    "op_001",
    operator_data
)

# Create goal
goal = progress_tracker.goal_tracker.create_goal(
    operator_id="op_001",
    name="Complete 20 sessions",
    description="Training milestone",
    target_value=20.0,
    unit="sessions"
)

# Get operator summary
summary = progress_tracker.get_operator_summary("op_001", operator_data)
print(f"Level: {summary['level']}, XP: {summary['total_xp']}")
```

### 5. Reporting Engine

**Purpose:** Generate comprehensive reports in multiple formats.

**Report Types:**
- Operator Progress Report
- Team Performance Report
- Cost Analysis Report
- Trend Analysis Report
- Compliance Report

**Example Usage:**

```python
# Generate operator progress report
report = reporting_engine.generate_report(
    ReportType.OPERATOR_PROGRESS,
    operator_id="op_001",
    time_range=timedelta(days=30)
)

# Export in different formats
json_export = reporting_engine.export_report(report.id, ReportFormat.JSON)
html_export = reporting_engine.export_report(report.id, ReportFormat.HTML)
md_export = reporting_engine.export_report(report.id, ReportFormat.MARKDOWN)

# Save to file
with open('report.html', 'w') as f:
    f.write(html_export)
```

### 6. Analytics Aggregator

**Purpose:** Pre-computed metrics for fast dashboard loading.

**Example Usage:**

```python
# Get complete dashboard data
dashboard = analytics_aggregator.get_dashboard_data()

# Access summary metrics
summary = dashboard['summary']
print(f"Active sessions: {summary['active_sessions']}")
print(f"Week cost: ${summary['week_cost']:.2f}")

# Access leaderboards
for entry in dashboard['xp_leaderboard']:
    print(f"#{entry['rank']} - {entry['name']}: {entry['xp']} XP")

# Check alerts
for alert in dashboard['active_alerts']:
    print(f"[{alert['priority']}] {alert['title']}")
```

## API Endpoints

All analytics functionality is available via REST API:

```bash
# Get operator performance
GET /api/analytics/operator/{id}/performance

# Get training recommendations
GET /api/analytics/operator/{id}/recommendations

# Get cost breakdown
GET /api/analytics/cost/breakdown?category=model&time_range_days=30

# Get leaderboard
GET /api/analytics/leaderboard?type=xp&limit=10

# Generate report
POST /api/analytics/reports/generate
{
  "report_type": "operator_progress",
  "parameters": {"operator_id": "op_001"}
}

# Download report
GET /api/analytics/reports/{id}/download?format=html
```

## CLI Commands

Access analytics via command line:

```bash
# View operator stats
ats-mafia analytics operator-stats op_001

# Generate training plan
ats-mafia analytics training-plan op_001 --target-role red_team_expert

# View cost report
ats-mafia analytics cost-report --timeframe 30 --category model

# Check leaderboard
ats-mafia analytics leaderboard --category xp --limit 10

# Analyze skill gaps
ats-mafia analytics skill-gap op_001 --target-role red_team_expert

# Export report
ats-mafia analytics export-report operator report.html \
  --format html --operator-id op_001 --days 30

# View dashboard
ats-mafia analytics dashboard
```

## Database Schema

Phase 4 includes a comprehensive database schema for persistent storage:

**Tables:**
- `operator_profiles` - Operator information
- `session_performance` - Session details
- `skills` - Skill proficiency data
- `achievements` - Unlocked achievements
- `certifications` - Earned certifications
- `performance_metrics` - Individual metrics
- `cost_history` - Cost tracking
- `goals` - Operator goals
- `reports` - Generated reports

**Initialize Database:**

```python
from ats_mafia_framework.core.database_schema import initialize_database

# SQLite (development)
db_manager = initialize_database("sqlite:///ats_mafia_analytics.db")

# PostgreSQL (production)
db_manager = initialize_database(
    "postgresql://user:pass@localhost/ats_mafia"
)
```

## Key Features

### 📊 Performance Tracking
- Multi-dimensional performance metrics
- Skill progression tracking
- Learning velocity calculation
- Plateau detection
- Benchmark comparisons

### 🎯 Training Effectiveness
- Learning curve analysis
- Knowledge retention measurement
- Skill gap identification
- AI-driven training recommendations
- Time-to-proficiency predictions

### 💰 Cost Optimization
- Detailed cost breakdowns
- Optimization opportunity identification
- ROI calculations
- Budget planning and forecasting
- Anomaly detection

### 🏆 Progress & Achievements
- XP and leveling system
- Achievement/badge system
- Milestone tracking
- Goal management
- Certification tracking
- Competitive leaderboards

### 📈 Reporting
- Multiple report types
- Export formats: JSON, CSV, HTML, Markdown
- Automated report generation
- Custom report templates

### ⚡ Real-Time Analytics
- Pre-computed dashboard metrics
- Metric caching for performance
- Trend calculations
- Alert management
- Fast data aggregation

## Integration

Phase 4 integrates seamlessly with existing framework components:

### With Orchestrator

```python
# The orchestrator automatically records analytics after each session
# via the _record_session_analytics() hook

# Access from orchestrator
orchestrator = get_training_orchestrator()
cost_tracker = orchestrator.get_cost_tracker()
```

### With Cost Tracker

```python
# Advanced analytics extends basic cost tracker
from ats_mafia_framework.core.cost_tracker import CostTracker
from ats_mafia_framework.core.advanced_cost_analytics import AdvancedCostAnalytics

cost_tracker = orchestrator.get_cost_tracker()
advanced_analytics = AdvancedCostAnalytics(cost_tracker)

# Get optimization recommendations
opportunities = advanced_analytics.optimizer.identify_opportunities()
```

## Configuration

Add to your framework configuration:

```yaml
analytics:
  enabled: true
  storage_path: "data/analytics"
  cache_ttl_seconds: 300
  auto_refresh: true
  
  performance_metrics:
    track_all_sessions: true
    retention_days: 365
  
  reporting:
    auto_generate: ["daily_summary", "weekly_cost"]
    formats: ["json", "html", "markdown"]
  
  alerts:
    budget_thresholds: [0.75, 0.90, 1.0]
    performance_threshold: 0.6
  
  database:
    url: "sqlite:///ats_mafia_analytics.db"
    # url: "postgresql://user:pass@localhost/ats_mafia"
```

## Best Practices

### 1. Regular Monitoring
```python
# Check dashboard daily
dashboard = analytics_aggregator.get_dashboard_data()

# Review active alerts
alerts = analytics_aggregator.alert_manager.get_active_alerts()
```

### 2. Weekly Reviews
```python
# Generate weekly reports
weekly_cost = reporting_engine.generate_report(
    ReportType.COST_SUMMARY,
    time_range=timedelta(days=7)
)

weekly_progress = reporting_engine.generate_report(
    ReportType.TEAM_PERFORMANCE,
    operator_ids=all_operator_ids
)
```

### 3. Monthly Analysis
```python
# Analyze trends
trends = analytics_aggregator.trend_calculator.calculate_performance_trend(
    period_days=30
)

# Optimize costs
opportunities = cost_analytics.optimizer.identify_opportunities(
    time_range=timedelta(days=30)
)
```

### 4. Continuous Improvement
```python
# Generate personalized training plans
for operator_id in operator_ids:
    profile = perf_engine.get_operator_profile(operator_id)
    sessions = perf_engine.get_operator_sessions(operator_id)
    
    recommendations = effectiveness_tracker.generate_recommendations(
        operator_id, profile, sessions
    )
    
    # Act on recommendations
    for rec in recommendations:
        if rec.priority >= 4:
            print(f"High priority: {rec.title}")
```

## Performance Optimization

The analytics system is designed for efficiency:

### Caching Strategy
- Dashboard metrics cached for 5 minutes
- Expensive calculations pre-computed
- Incremental updates where possible

### Data Retention
- Keep last 10,000 metrics in memory
- Archive older data to database
- Configurable retention periods

### Batch Operations
- Bulk metric recording
- Batch report generation
- Efficient database queries

## Troubleshooting

### Issue: Slow Dashboard Loading

**Solution:**
```python
# Refresh cache manually
analytics_aggregator.refresh_cache()

# Reduce cache TTL
aggregator.metric_aggregator.cache[key].ttl_seconds = 60
```

### Issue: High Memory Usage

**Solution:**
```python
# Clear old metrics
perf_engine.metrics = perf_engine.metrics[-5000:]

# Clear old reports
for report_id in old_report_ids:
    reporting_engine.delete_report(report_id)
```

### Issue: Missing Recommendations

**Solution:**
```python
# Ensure sufficient session data
sessions = perf_engine.get_operator_sessions(operator_id)
if len(sessions) < 3:
    print("Need more sessions for recommendations")

# Check operator profile data
profile = perf_engine.get_operator_profile(operator_id)
if not profile.skills:
    print("No skills recorded yet")
```

## Advanced Features

### Custom Benchmarks

```python
# Set custom benchmark
perf_engine.benchmark_engine.set_benchmark(
    benchmark_id="custom_recon_time",
    metric_type=MetricType.TIME_EFFICIENCY,
    value=0.85,
    context={'scenario': 'reconnaissance'}
)

# Compare to benchmark
comparison = perf_engine.benchmark_engine.compare_to_benchmark(
    metric, "custom_recon_time"
)
```

### Custom Milestones

```python
# Create custom milestone
from ats_mafia_framework.core.progress_tracker import Milestone, MilestoneType

custom_milestone = Milestone(
    id="milestone_custom_001",
    name="Master Hacker",
    description="Achieve expert level in 5 skills",
    milestone_type=MilestoneType.MASTERY,
    requirements={'skill_count': 5},
    xp_reward=5000,
    badge_icon="master_hacker_badge"
)

progress_tracker.register_milestone(custom_milestone)
```

### Custom Reports

```python
# Create custom report generator
from ats_mafia_framework.core.reporting_engine import ReportGenerator