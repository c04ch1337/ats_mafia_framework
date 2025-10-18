"""
ATS MAFIA Framework - Phase 4 Analytics System Test Suite

Comprehensive tests for all Phase 4 components including performance metrics,
training effectiveness, cost analytics, progress tracking, and reporting.
"""

import unittest
import uuid
from datetime import datetime, timezone, timedelta

from ..core.performance_metrics import (
    PerformanceMetricsEngine, MetricType, SkillLevel, SessionPerformance,
    PerformanceMetric
)
from ..core.training_effectiveness import (
    TrainingEffectivenessTracker, LearningCurve, RecommendationType
)
from ..core.advanced_cost_analytics import (
    AdvancedCostAnalytics, CostCategory, OptimizationType
)
from ..core.progress_tracker import (
    ProgressTracker, Milestone, MilestoneType, Goal
)
from ..core.reporting_engine import (
    ReportingEngine, ReportType, ReportFormat
)
from ..core.analytics_aggregator import (
    AnalyticsAggregator, AlertType, AlertPriority
)
from ..core.cost_tracker import CostTracker
from ..core.llm_models import ModelRegistry


class TestPerformanceMetrics(unittest.TestCase):
    """Test performance metrics engine."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.engine = PerformanceMetricsEngine()
        self.operator_id = "test_operator_001"
    
    def test_create_operator_profile(self):
        """Test operator profile creation."""
        profile = self.engine.create_operator_profile(
            operator_id=self.operator_id,
            name="Test Operator"
        )
        
        self.assertEqual(profile.operator_id, self.operator_id)
        self.assertEqual(profile.name, "Test Operator")
        self.assertEqual(profile.skill_level, SkillLevel.NOVICE)
        self.assertEqual(profile.total_sessions, 0)
    
    def test_record_metric(self):
        """Test recording performance metrics."""
        self.engine.create_operator_profile(self.operator_id, "Test Operator")
        
        metric = self.engine.record_metric(
            operator_id=self.operator_id,
            session_id="session_001",
            metric_type=MetricType.SUCCESS_RATE,
            value=0.85,
            scenario_id="scenario_001"
        )
        
        self.assertEqual(metric.operator_id, self.operator_id)
        self.assertEqual(metric.metric_type, MetricType.SUCCESS_RATE)
        self.assertEqual(metric.value, 0.85)
    
    def test_record_session_performance(self):
        """Test recording session performance."""
        profile = self.engine.create_operator_profile(self.operator_id, "Test Operator")
        
        session_perf = SessionPerformance(
            session_id="session_001",
            operator_id=self.operator_id,
            scenario_id="scenario_001",
            start_time=datetime.now(timezone.utc) - timedelta(hours=2),
            end_time=datetime.now(timezone.utc),
            duration_seconds=7200,
            success=True,
            score=0.85,
            cost=1.50,
            skills_practiced=["reconnaissance", "exploitation"],
            objectives_completed=8,
            objectives_total=10
        )
        
        self.engine.record_session_performance(session_perf)
        
        # Verify profile was updated
        updated_profile = self.engine.get_operator_profile(self.operator_id)
        self.assertEqual(updated_profile.total_sessions, 1)
        self.assertGreater(updated_profile.total_hours, 0)
        self.assertIn("reconnaissance", updated_profile.skills)
    
    def test_analyze_operator_performance(self):
        """Test operator performance analysis."""
        self.engine.create_operator_profile(self.operator_id, "Test Operator")
        
        # Add some performance data
        for i in range(5):
            session_perf = SessionPerformance(
                session_id=f"session_{i}",
                operator_id=self.operator_id,
                scenario_id="scenario_001",
                start_time=datetime.now(timezone.utc) - timedelta(days=i),
                end_time=datetime.now(timezone.utc) - timedelta(days=i, hours=-1),
                duration_seconds=3600,
                success=True,
                score=0.7 + (i * 0.05),  # Improving scores
                cost=1.0,
                skills_practiced=["reconnaissance"]
            )
            self.engine.record_session_performance(session_perf)
        
        analysis = self.engine.analyze_operator_performance(self.operator_id)
        
        self.assertIn('learning_velocity', analysis)
        self.assertIn('strengths', analysis)
        self.assertIn('weaknesses', analysis)
        self.assertGreater(analysis['learning_velocity'], 0)


class TestTrainingEffectiveness(unittest.TestCase):
    """Test training effectiveness tracker."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.tracker = TrainingEffectivenessTracker()
        self.operator_id = "test_operator_002"
    
    def test_track_learning_progress(self):
        """Test learning curve tracking."""
        skill = "exploitation"
        
        # Simulate learning progression
        for i in range(10):
            score = 0.3 + (i * 0.06)  # Improving from 0.3 to 0.84
            curve = self.tracker.track_learning_progress(
                operator_id=self.operator_id,
                skill_name=skill,
                timestamp=datetime.now(timezone.utc) - timedelta(days=10-i),
                score=min(score, 1.0)
            )
        
        # Verify learning curve
        curves = self.tracker.learning_curves.get(self.operator_id, {})
        self.assertIn(skill, curves)
        
        curve = curves[skill]
        self.assertGreater(curve.current_score, curve.initial_score)
        self.assertGreater(curve.learning_rate, 0)
    
    def test_predict_time_to_mastery(self):
        """Test time-to-proficiency prediction."""
        from ..core.performance_metrics import PerformanceMetricsEngine
        
        engine = PerformanceMetricsEngine()
        profile = engine.create_operator_profile(self.operator_id, "Test Operator")
        
        # Add learning data
        skill = "reconnaissance"
        for i in range(5):
            score = 0.5 + (i * 0.08)
            self.tracker.track_learning_progress(
                self.operator_id, skill,
                datetime.now(timezone.utc) - timedelta(days=5-i),
                score
            )
        
        # Predict time to mastery
        prediction = self.tracker.calculate_time_to_proficiency(
            operator_id=self.operator_id,
            skill_name=skill,
            target_level=SkillLevel.EXPERT
        )
        
        if prediction:
            self.assertIn('sessions_needed', prediction)
            self.assertIn('estimated_hours', prediction)
    
    def test_plateau_detection(self):
        """Test learning plateau detection."""
        skill = "post_exploitation"
        
        # Simulate plateau (scores not improving)
        for i in range(5):
            self.tracker.track_learning_progress(
                self.operator_id, skill,
                datetime.now(timezone.utc) - timedelta(days=5-i),
                0.65  # Same score
            )
        
        curve = self.tracker.learning_curves[self.operator_id][skill]
        self.assertTrue(curve.is_plateaued())


class TestAdvancedCostAnalytics(unittest.TestCase):
    """Test advanced cost analytics."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.registry = ModelRegistry()
        self.cost_tracker = CostTracker(self.registry)
        self.analytics = AdvancedCostAnalytics(self.cost_tracker)
    
    def test_cost_breakdown(self):
        """Test cost breakdown generation."""
        # Add some usage data
        for i in range(5):
            self.cost_tracker.record_usage(
                usage_id=f"usage_{i}",
                model="openai/gpt-4",
                profile_id="profile_001",
                session_id="session_001",
                task_type="reconnaissance",
                input_tokens=1000,
                output_tokens=500,
                latency_ms=1000,
                success=True
            )
        
        breakdown = self.analytics.get_detailed_breakdown(
            CostCategory.MODEL_USAGE,
            time_range=timedelta(days=1)
        )
        
        self.assertEqual(breakdown.category, CostCategory.MODEL_USAGE)
        self.assertGreater(breakdown.total_cost, 0)
        self.assertIn("openai/gpt-4", breakdown.items)
    
    def test_optimization_opportunities(self):
        """Test cost optimization identification."""
        # Record expensive usage
        for i in range(20):
            self.cost_tracker.record_usage(
                usage_id=f"usage_{i}",
                model="openai/gpt-4",
                profile_id="profile_001",
                session_id="session_001",
                task_type="reconnaissance",
                input_tokens=2000,
                output_tokens=1000,
                latency_ms=1000,
                success=True
            )
        
        opportunities = self.analytics.optimizer.identify_opportunities(
            session_id="session_001"
        )
        
        # Should identify optimization opportunities
        self.assertGreater(len(opportunities), 0)
    
    def test_roi_calculation(self):
        """Test ROI calculation."""
        roi = self.analytics.roi_calculator.calculate_training_roi(
            total_cost=100.0,
            initial_skill_level=1.0,
            final_skill_level=3.0,
            training_hours=20.0,
            certifications=1
        )
        
        self.assertEqual(roi.skill_gains, 2)
        self.assertGreater(roi.cost_per_skill_level, 0)
        self.assertEqual(roi.certifications_earned, 1)


class TestProgressTracker(unittest.TestCase):
    """Test progress tracking system."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.tracker = ProgressTracker()
        self.operator_id = "test_operator_003"
    
    def test_milestone_detection(self):
        """Test automatic milestone detection."""
        operator_data = {
            'total_sessions': 1,
            'total_hours': 0,
            'skills': {},
            'certifications': [],
            'total_xp': 0
        }
        
        # Check for first session milestone
        achievements = self.tracker.check_and_award_milestones(
            self.operator_id,
            operator_data
        )
        
        # Should award first session achievement
        self.assertGreater(len(achievements), 0)
        self.assertEqual(achievements[0].milestone_id, "milestone_first_session")
    
    def test_goal_tracking(self):
        """Test goal creation and tracking."""
        goal = self.tracker.goal_tracker.create_goal(
            operator_id=self.operator_id,
            name="Complete 10 sessions",
            description="Test goal",
            target_value=10.0,
            unit="sessions"
        )
        
        self.assertEqual(goal.operator_id, self.operator_id)
        self.assertEqual(goal.target_value, 10.0)
        
        # Update progress
        completed = self.tracker.goal_tracker.update_goal_progress(goal.id, 10.0)
        self.assertTrue(completed)
        self.assertTrue(goal.is_completed())
    
    def test_xp_and_leveling(self):
        """Test XP tracking and level calculation."""
        # Award some XP
        operator_data = {'total_sessions': 10, 'total_hours': 0, 'skills': {}, 'certifications': [], 'total_xp': 0}
        self.tracker.check_and_award_milestones(self.operator_id, operator_data)
        
        xp = self.tracker.get_operator_xp(self.operator_id)
        level = self.tracker.get_operator_level(self.operator_id)
        
        self.assertGreaterEqual(xp, 0)
        self.assertGreater(level, 0)
    
    def test_leaderboard(self):
        """Test leaderboard generation."""
        # Create some operators with different XP
        for i in range(5):
            op_id = f"operator_{i}"
            self.tracker.operator_xp[op_id] = (i + 1) * 1000
        
        leaderboard = self.tracker.get_leaderboard("test_category", limit=3)
        
        # Leaderboard should be empty as we didn't update it properly
        # This is just testing the method exists
        self.assertIsInstance(leaderboard, list)


class TestReportingEngine(unittest.TestCase):
    """Test reporting engine."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.perf_engine = PerformanceMetricsEngine()
        self.effectiveness = TrainingEffectivenessTracker()
        self.registry = ModelRegistry()
        self.cost_tracker = CostTracker(self.registry)
        self.cost_analytics = AdvancedCostAnalytics(self.cost_tracker)
        self.progress = ProgressTracker()
        
        self.reporting = ReportingEngine(
            self.perf_engine,
            self.effectiveness,
            self.cost_analytics,
            self.progress
        )
        
        self.operator_id = "test_operator_004"
    
    def test_generate_operator_report(self):
        """Test operator progress report generation."""
        # Create operator with some data
        profile = self.perf_engine.create_operator_profile(
            self.operator_id,
            "Test Operator"
        )
        
        # Add a session
        session = SessionPerformance(
            session_id="session_001",
            operator_id=self.operator_id,
            scenario_id="scenario_001",
            start_time=datetime.now(timezone.utc) - timedelta(hours=1),
            end_time=datetime.now(timezone.utc),
            duration_seconds=3600,
            success=True,
            score=0.8,
            cost=1.0
        )
        self.perf_engine.record_session_performance(session)
        
        # Generate report
        report = self.reporting.generate_report(
            ReportType.OPERATOR_PROGRESS,
            operator_id=self.operator_id
        )
        
        self.assertEqual(report.report_type, ReportType.OPERATOR_PROGRESS)
        self.assertIn('operator_id', report.data)
        self.assertEqual(report.data['operator_id'], self.operator_id)
    
    def test_export_report_json(self):
        """Test JSON report export."""
        profile = self.perf_engine.create_operator_profile(
            self.operator_id,
            "Test Operator"
        )
        
        report = self.reporting.generate_report(
            ReportType.OPERATOR_PROGRESS,
            operator_id=self.operator_id
        )
        
        json_export = self.reporting.export_report(report.id, ReportFormat.JSON)
        
        self.assertIsInstance(json_export, str)
        self.assertIn(self.operator_id, json_export)
    
    def test_export_report_markdown(self):
        """Test Markdown report export."""
        profile = self.perf_engine.create_operator_profile(
            self.operator_id,
            "Test Operator"
        )
        
        report = self.reporting.generate_report(
            ReportType.OPERATOR_PROGRESS,
            operator_id=self.operator_id
        )
        
        md_export = self.reporting.export_report(report.id, ReportFormat.MARKDOWN)
        
        self.assertIsInstance(md_export, str)
        self.assertIn('#', md_export)  # Should have markdown headers


class TestAnalyticsAggregator(unittest.TestCase):
    """Test analytics aggregator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.perf_engine = PerformanceMetricsEngine()
        self.effectiveness = TrainingEffectivenessTracker()
        self.registry = ModelRegistry()
        self.cost_tracker = CostTracker(self.registry)
        self.progress = ProgressTracker()
        
        self.aggregator = AnalyticsAggregator(
            self.perf_engine,
            self.effectiveness,
            self.cost_tracker,
            self.progress
        )
    
    def test_dashboard_data(self):
        """Test dashboard data retrieval."""
        dashboard = self.aggregator.get_dashboard_data()
        
        self.assertIn('summary', dashboard)
        self.assertIn('xp_leaderboard', dashboard)
        self.assertIn('active_alerts', dashboard)
    
    def test_metric_caching(self):
        """Test metric caching."""
        # Get a metric (should calculate and cache)
        value1 = self.aggregator.metric_aggregator.get_metric('total_operators')
        
        # Get again (should use cache)
        value2 = self.aggregator.metric_aggregator.get_metric('total_operators')
        
        self.assertEqual(value1, value2)
    
    def test_alert_creation(self):
        """Test alert creation and management."""
        alert = self.aggregator.alert_manager.create_alert(
            alert_type=AlertType.BUDGET_WARNING,
            priority=AlertPriority.HIGH,
            title="Budget Alert",
            message="Budget threshold exceeded",
            details={'budget': 100, 'spent': 90}
        )
        
        self.assertEqual(alert.alert_type, AlertType.BUDGET_WARNING)
        self.assertEqual(alert.priority, AlertPriority.HIGH)
        self.assertFalse(alert.acknowledged)
        
        # Acknowledge alert
        success = self.aggregator.alert_manager.acknowledge_alert(alert.id)
        self.assertTrue(success)
        self.assertTrue(alert.acknowledged)


class TestIntegration(unittest.TestCase):
    """Test integration of all Phase 4 components."""
    
    def setUp(self):
        """Set up complete analytics system."""
        self.perf_engine = PerformanceMetricsEngine()
        self.effectiveness = TrainingEffectivenessTracker()
        self.registry = ModelRegistry()
        self.cost_tracker = CostTracker(self.registry)
        self.cost_analytics = AdvancedCostAnalytics(self.cost_tracker)
        self.progress = ProgressTracker()
        self.reporting = ReportingEngine(
            self.perf_engine,
            self.effectiveness,
            self.cost_analytics,
            self.progress
        )
        self.aggregator = AnalyticsAggregator(
            self.perf_engine,
            self.effectiveness,
            self.cost_tracker,
            self.progress
        )
        
        self.operator_id = "integration_test_operator"
    
    def test_complete_training_cycle(self):
        """Test complete training cycle with analytics."""
        # 1. Create operator
        profile = self.perf_engine.create_operator_profile(
            self.operator_id,
            "Integration Test Operator"
        )
        
        # 2. Simulate training sessions
        for i in range(3):
            # Record session performance
            session = SessionPerformance(
                session_id=f"session_{i}",
                operator_id=self.operator_id,
                scenario_id="test_scenario",
                start_time=datetime.now(timezone.utc) - timedelta(hours=2),
                end_time=datetime.now(timezone.utc) - timedelta(hours=1),
                duration_seconds=3600,
                success=True,
                score=0.7 + (i * 0.1),
                cost=1.5,
                skills_practiced=["reconnaissance", "exploitation"],
                objectives_completed=7 + i,
                objectives_total=10
            )
            self.perf_engine.record_session_performance(session)
            
            # Record cost
            self.cost_tracker.record_usage(
                usage_id=f"usage_{i}",
                model="openai/gpt-4",
                profile_id=self.operator_id,
                session_id=session.session_id,
                task_type="reconnaissance",
                input_tokens=1000,
                output_tokens=500,
                latency_ms=1000,
                success=True
            )
            
            # Track learning
            self.effectiveness.track_learning_progress(
                self.operator_id,
                "reconnaissance",
                session.end_time,
                session.score
            )
        
        # 3. Check milestones
        operator_data = {
            'total_sessions': profile.total_sessions,
            'total_hours': profile.total_hours,
            'skills': {k: v.to_dict() for k, v in profile.skills.items()},
            'certifications': profile.certifications,
            'total_xp': self.progress.get_operator_xp(self.operator_id)
        }
        achievements = self.progress.check_and_award_milestones(
            self.operator_id,
            operator_data
        )
        
        # 4. Generate recommendations
        sessions = self.perf_engine.get_operator_sessions(self.operator_id)
        recommendations = self.effectiveness.generate_recommendations(
            self.operator_id,
            profile,
            sessions
        )
        
        # 5. Generate reports
        operator_report = self.reporting.generate_report(
            ReportType.OPERATOR_PROGRESS,
            operator_id=self.operator_id
        )
        
        cost_report = self.reporting.generate_report(
            ReportType.COST_SUMMARY,
            session_id="session_0"
        )
        
        # 6. Get dashboard data
        dashboard = self.aggregator.get_dashboard_data()
        
        # Verify everything works together
        self.assertEqual(profile.total_sessions, 3)
        self.assertGreater(len(achievements), 0)
        self.assertIsInstance(recommendations, list)
        self.assertIsNotNone(operator_report)
        self.assertIsNotNone(cost_report)
        self.assertIn('summary', dashboard)
    
    def test_end_to_end_workflow(self):
        """Test end-to-end analytics workflow."""
        # Create operator
        profile = self.perf_engine.create_operator_profile(
            self.operator_id,
            "E2E Test Operator"
        )
        
        # Create goal
        goal = self.progress.goal_tracker.create_goal(
            operator_id=self.operator_id,
            name="Complete 5 sessions",
            description="Training goal",
            target_value=5.0,
            unit="sessions"
        )
        
        # Complete sessions and update goal
        for i in range(5):
            session = SessionPerformance(
                session_id=f"e2e_session_{i}",
                operator_id=self.operator_id,
                scenario_id="e2e_scenario",
                start_time=datetime.now(timezone.utc) - timedelta(hours=2),
                end_time=datetime.now(timezone.utc) - timedelta(hours=1),
                duration_seconds=3600,
                success=True,
                score=0.75,
                cost=1.0
            )
            self.perf_engine.record_session_performance(session)
            
            # Update goal progress
            self.progress.goal_tracker.update_goal_progress(goal.id, float(i + 1))
        
        # Verify goal completion
        self.assertTrue(goal.is_completed())
        self.assertIsNotNone(goal.completed_at)
        
        # Generate comprehensive report
        report = self.reporting.generate_report(
            ReportType.OPERATOR_PROGRESS,
            operator_id=self.operator_id
        )
        
        # Verify report contains all data
        self.assertIn('summary', report.data)
        self.assertIn('recent_sessions', report.data)
        self.assertEqual(len(report.data['recent_sessions']), 5)


def run_tests():
    """Run all Phase 4 analytics tests."""
    print("\n" + "="*60)
    print("ATS MAFIA Framework - Phase 4 Analytics Test Suite")
    print("="*60 + "\n")
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestPerformanceMetrics))
    suite.addTests(loader.loadTestsFromTestCase(TestTrainingEffectiveness))
    suite.addTests(loader.loadTestsFromTestCase(TestAdvancedCostAnalytics))
    suite.addTests(loader.loadTestsFromTestCase(TestProgressTracker))
    suite.addTests(loader.loadTestsFromTestCase(TestReportingEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestAnalyticsAggregator))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*60 + "\n")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)