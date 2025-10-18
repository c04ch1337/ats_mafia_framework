# ATS MAFIA Phase 4 - Quick Start Guide

## Initialize the Analytics System

```python
from ats_mafia_framework.core.analytics_integration import initialize_analytics_system

analytics = initialize_analytics_system(storage_path="data/analytics")
```

## Create an Operator

```python
profile = analytics.performance_engine.create_operator_profile(
    operator_id="op_001",
    name="Your Name"
)
```

## Record a Training Session

```python
from ats_mafia_framework.core.performance_metrics import SessionPerformance
from datetime import datetime, timezone, timedelta

session = SessionPerformance(
    session_id="session_001",
    operator_id="op_001",
    scenario_id="basic_pentest",
    start_time=datetime.now(timezone.utc) - timedelta(hours=1),
    end_time=datetime.now(timezone.utc),
    duration_seconds=3600,
    success=True,
    score=0.85,
    cost=1.50,
    skills_practiced=["reconnaissance", "exploitation"],
    objectives_completed=8,
    objectives_total=10
)

analytics.performance_engine.record_session_performance(session)
```

## View Analytics

```python
# Performance analysis
analysis = analytics.performance_engine.analyze_operator_performance("op_001")

# Training recommendations
recommendations = analytics.effectiveness_tracker.generate_recommendations(
    operator_id="op_001",
    operator_profile=profile,
    recent_sessions=[session]
)

# Dashboard data
dashboard = analytics.analytics_aggregator.get_dashboard_data()
```

## Generate Report

```python
from ats_mafia_framework.core.reporting_engine import ReportType, ReportFormat

report = analytics.reporting_engine.generate_report(
    ReportType.OPERATOR_PROGRESS,
    operator_id="op_001"
)

html = analytics.reporting_engine.export_report(report.id, ReportFormat.HTML)
```

## Run Demo

```bash
cd ats_mafia_framework/tests
python demo_phase4_analytics.py
```

## Documentation

- [Implementation Summary](../ATS_MAFIA_PHASE4_IMPLEMENTATION_SUMMARY.md)
- [Full README](docs/PHASE4_ANALYTICS_README.md)
- [API Endpoints](api/analytics_endpoints.py)
- [CLI Commands](cli/analytics_commands.py)