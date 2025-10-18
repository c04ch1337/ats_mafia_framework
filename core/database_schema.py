"""
ATS MAFIA Framework Database Schema

This module provides database schema definitions and persistence layer
for analytics data storage. Supports both SQLite (local) and PostgreSQL (production).
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

# Note: SQLAlchemy is an optional dependency
try:
    from sqlalchemy import (
        create_engine, Column, Integer, String, Float, Boolean,
        DateTime, JSON, ForeignKey, Text, Enum as SQLEnum
    )
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker, relationship
    import enum
    
    SQLALCHEMY_AVAILABLE = True
    Base = declarative_base()
    
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    Base = None


# Database Schema Documentation
DATABASE_SCHEMA = """
# ATS MAFIA Analytics Database Schema

## Tables

### operator_profiles
Stores operator profile information and overall statistics.

Columns:
- id (VARCHAR PRIMARY KEY): Unique operator identifier
- name (VARCHAR): Operator name
- created_at (DATETIME): When profile was created
- total_sessions (INTEGER): Total number of training sessions
- total_hours (FLOAT): Total training hours
- skill_level (VARCHAR): Current skill level (novice/intermediate/advanced/expert/master)
- total_xp (INTEGER): Total experience points
- metadata (JSON): Additional metadata

### session_performance
Stores detailed performance data for completed sessions.

Columns:
- session_id (VARCHAR PRIMARY KEY): Unique session identifier
- operator_id (VARCHAR FOREIGN KEY): References operator_profiles(id)
- scenario_id (VARCHAR): Scenario identifier
- start_time (DATETIME): Session start time
- end_time (DATETIME): Session end time
- duration_seconds (FLOAT): Session duration
- success (BOOLEAN): Whether session was successful
- score (FLOAT): Overall performance score (0.0-1.0)
- cost (FLOAT): Total cost for session
- objectives_completed (INTEGER): Number of objectives completed
- objectives_total (INTEGER): Total number of objectives
- metrics_json (JSON): Detailed metrics data

### skills
Stores individual skill proficiency data.

Columns:
- id (INTEGER PRIMARY KEY AUTOINCREMENT)
- operator_id (VARCHAR FOREIGN KEY): References operator_profiles(id)
- skill_name (VARCHAR): Name of the skill
- proficiency_level (VARCHAR): Current proficiency level
- practice_count (INTEGER): Number of times practiced
- success_rate (FLOAT): Success rate (0.0-1.0)
- average_score (FLOAT): Average performance score
- last_practiced (DATETIME): Last practice date

### achievements
Stores unlocked achievements.

Columns:
- id (VARCHAR PRIMARY KEY): Unique achievement identifier
- operator_id (VARCHAR FOREIGN KEY): References operator_profiles(id)
- milestone_id (VARCHAR): Associated milestone
- name (VARCHAR): Achievement name
- description (TEXT): Achievement description
- category (VARCHAR): Achievement category
- unlocked_at (DATETIME): When achievement was unlocked
- xp_earned (INTEGER): XP awarded

### certifications
Stores earned certifications.

Columns:
- id (INTEGER PRIMARY KEY AUTOINCREMENT)
- operator_id (VARCHAR FOREIGN KEY): References operator_profiles(id)
- certification_id (VARCHAR): Certification identifier
- earned_at (DATETIME): When certification was earned
- expires_at (DATETIME NULLABLE): When certification expires

### performance_metrics
Stores individual performance metrics.

Columns:
- id (VARCHAR PRIMARY KEY): Unique metric identifier
- timestamp (DATETIME): When metric was recorded
- operator_id (VARCHAR FOREIGN KEY): References operator_profiles(id)
- session_id (VARCHAR): Associated session
- metric_type (VARCHAR): Type of metric
- value (FLOAT): Metric value
- context_json (JSON): Additional context

### cost_history
Stores cost tracking data.

Columns:
- id (INTEGER PRIMARY KEY AUTOINCREMENT)
- timestamp (DATETIME): When cost was incurred
- operator_id (VARCHAR): Operator identifier
- session_id (VARCHAR): Session identifier
- model (VARCHAR): LLM model used
- task_type (VARCHAR): Type of task
- input_tokens (INTEGER): Number of input tokens
- output_tokens (INTEGER): Number of output tokens
- cost (FLOAT): Cost in USD
- success (BOOLEAN): Whether request was successful

### goals
Stores operator goals.

Columns:
- id (VARCHAR PRIMARY KEY): Unique goal identifier
- operator_id (VARCHAR FOREIGN KEY): References operator_profiles(id)
- name (VARCHAR): Goal name
- description (TEXT): Goal description
- target_value (FLOAT): Target value to achieve
- current_value (FLOAT): Current progress
- unit (VARCHAR): Unit of measurement
- deadline (DATETIME NULLABLE): Optional deadline
- created_at (DATETIME): When goal was created
- completed_at (DATETIME NULLABLE): When goal was completed

### reports
Stores generated reports.

Columns:
- id (VARCHAR PRIMARY KEY): Unique report identifier
- report_type (VARCHAR): Type of report
- title (VARCHAR): Report title
- description (TEXT): Report description
- generated_at (DATETIME): When report was generated
- generated_by (VARCHAR): Who generated the report
- data_json (JSON): Report data

## Indexes

CREATE INDEX idx_session_operator ON session_performance(operator_id);
CREATE INDEX idx_session_start ON session_performance(start_time);
CREATE INDEX idx_skills_operator ON skills(operator_id);
CREATE INDEX idx_achievements_operator ON achievements(operator_id);
CREATE INDEX idx_metrics_operator ON performance_metrics(operator_id);
CREATE INDEX idx_metrics_timestamp ON performance_metrics(timestamp);
CREATE INDEX idx_cost_timestamp ON cost_history(timestamp);
CREATE INDEX idx_cost_session ON cost_history(session_id);
"""


if SQLALCHEMY_AVAILABLE:
    
    class OperatorProfileDB(Base):
        """SQLAlchemy model for operator profiles."""
        __tablename__ = 'operator_profiles'
        
        id = Column(String(50), primary_key=True)
        name = Column(String(100), nullable=False)
        created_at = Column(DateTime, nullable=False)
        total_sessions = Column(Integer, default=0)
        total_hours = Column(Float, default=0.0)
        skill_level = Column(String(20), default='novice')
        total_xp = Column(Integer, default=0)
        metadata = Column(JSON)
        
        # Relationships
        sessions = relationship("SessionPerformanceDB", back_populates="operator")
        skills = relationship("SkillDB", back_populates="operator")
        achievements = relationship("AchievementDB", back_populates="operator")
        goals = relationship("GoalDB", back_populates="operator")
    
    
    class SessionPerformanceDB(Base):
        """SQLAlchemy model for session performance."""
        __tablename__ = 'session_performance'
        
        session_id = Column(String(50), primary_key=True)
        operator_id = Column(String(50), ForeignKey('operator_profiles.id'))
        scenario_id = Column(String(100))
        start_time = Column(DateTime, nullable=False)
        end_time = Column(DateTime, nullable=False)
        duration_seconds = Column(Float)
        success = Column(Boolean)
        score = Column(Float)
        cost = Column(Float)
        objectives_completed = Column(Integer, default=0)
        objectives_total = Column(Integer, default=0)
        metrics_json = Column(JSON)
        
        # Relationship
        operator = relationship("OperatorProfileDB", back_populates="sessions")
    
    
    class SkillDB(Base):
        """SQLAlchemy model for skills."""
        __tablename__ = 'skills'
        
        id = Column(Integer, primary_key=True, autoincrement=True)
        operator_id = Column(String(50), ForeignKey('operator_profiles.id'))
        skill_name = Column(String(100), nullable=False)
        proficiency_level = Column(String(20))
        practice_count = Column(Integer, default=0)
        success_rate = Column(Float, default=0.0)
        average_score = Column(Float, default=0.0)
        last_practiced = Column(DateTime)
        
        # Relationship
        operator = relationship("OperatorProfileDB", back_populates="skills")
    
    
    class AchievementDB(Base):
        """SQLAlchemy model for achievements."""
        __tablename__ = 'achievements'
        
        id = Column(String(50), primary_key=True)
        operator_id = Column(String(50), ForeignKey('operator_profiles.id'))
        milestone_id = Column(String(50))
        name = Column(String(100), nullable=False)
        description = Column(Text)
        category = Column(String(50))
        unlocked_at = Column(DateTime, nullable=False)
        xp_earned = Column(Integer)
        
        # Relationship
        operator = relationship("OperatorProfileDB", back_populates="achievements")
    
    
    class CertificationDB(Base):
        """SQLAlchemy model for certifications."""
        __tablename__ = 'certifications'
        
        id = Column(Integer, primary_key=True, autoincrement=True)
        operator_id = Column(String(50), ForeignKey('operator_profiles.id'))
        certification_id = Column(String(50), nullable=False)
        earned_at = Column(DateTime, nullable=False)
        expires_at = Column(DateTime, nullable=True)
    
    
    class PerformanceMetricDB(Base):
        """SQLAlchemy model for performance metrics."""
        __tablename__ = 'performance_metrics'
        
        id = Column(String(50), primary_key=True)
        timestamp = Column(DateTime, nullable=False)
        operator_id = Column(String(50), ForeignKey('operator_profiles.id'))
        session_id = Column(String(50))
        metric_type = Column(String(50))
        value = Column(Float)
        context_json = Column(JSON)
    
    
    class CostHistoryDB(Base):
        """SQLAlchemy model for cost history."""
        __tablename__ = 'cost_history'
        
        id = Column(Integer, primary_key=True, autoincrement=True)
        timestamp = Column(DateTime, nullable=False)
        operator_id = Column(String(50))
        session_id = Column(String(50))
        model = Column(String(100))
        task_type = Column(String(50))
        input_tokens = Column(Integer)
        output_tokens = Column(Integer)
        cost = Column(Float)
        success = Column(Boolean)
    
    
    class GoalDB(Base):
        """SQLAlchemy model for goals."""
        __tablename__ = 'goals'
        
        id = Column(String(50), primary_key=True)
        operator_id = Column(String(50), ForeignKey('operator_profiles.id'))
        name = Column(String(100), nullable=False)
        description = Column(Text)
        target_value = Column(Float)
        current_value = Column(Float, default=0.0)
        unit = Column(String(20))
        deadline = Column(DateTime, nullable=True)
        created_at = Column(DateTime, nullable=False)
        completed_at = Column(DateTime, nullable=True)
        
        # Relationship
        operator = relationship("OperatorProfileDB", back_populates="goals")
    
    
    class ReportDB(Base):
        """SQLAlchemy model for reports."""
        __tablename__ = 'reports'
        
        id = Column(String(50), primary_key=True)
        report_type = Column(String(50))
        title = Column(String(200))
        description = Column(Text)
        generated_at = Column(DateTime, nullable=False)
        generated_by = Column(String(100))
        data_json = Column(JSON)


class DatabaseManager:
    """
    Manages database connections and operations.
    
    Provides a unified interface for database operations with support
    for both SQLite (development) and PostgreSQL (production).
    """
    
    def __init__(self, database_url: str = "sqlite:///ats_mafia_analytics.db"):
        """
        Initialize database manager.
        
        Args:
            database_url: Database connection URL
                         Examples:
                         - SQLite: "sqlite:///ats_mafia_analytics.db"
                         - PostgreSQL: "postgresql://user:pass@localhost/ats_mafia"
        """
        self.logger = logging.getLogger("database_manager")
        
        if not SQLALCHEMY_AVAILABLE:
            self.logger.warning("SQLAlchemy not available. Database persistence disabled.")
            self.engine = None
            self.Session = None
            return
        
        try:
            self.engine = create_engine(database_url, echo=False)
            self.Session = sessionmaker(bind=self.engine)
            self.logger.info(f"Initialized database: {database_url}")
        except Exception as e:
            self.logger.error(f"Error initializing database: {e}")
            self.engine = None
            self.Session = None
    
    def create_tables(self) -> bool:
        """
        Create all database tables.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.engine or not Base:
            self.logger.error("Database engine not initialized")
            return False
        
        try:
            Base.metadata.create_all(self.engine)
            self.logger.info("Created database tables")
            return True
        except Exception as e:
            self.logger.error(f"Error creating tables: {e}")
            return False
    
    def get_session(self):
        """
        Get a new database session.
        
        Returns:
            Database session or None if not available
        """
        if not self.Session:
            return None
        return self.Session()
    
    def export_schema_sql(self, output_path: str) -> bool:
        """
        Export schema as SQL file.
        
        Args:
            output_path: Path to output SQL file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(DATABASE_SCHEMA, encoding='utf-8')
            self.logger.info(f"Exported schema to {output_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error exporting schema: {e}")
            return False


# Export schema documentation function
def get_schema_documentation() -> str:
    """
    Get comprehensive schema documentation.
    
    Returns:
        Schema documentation as string
    """
    return DATABASE_SCHEMA


# Export initialization function
def initialize_database(database_url: str = "sqlite:///ats_mafia_analytics.db") -> Optional[DatabaseManager]:
    """
    Initialize database with tables.
    
    Args:
        database_url: Database connection URL
        
    Returns:
        DatabaseManager instance or None if failed
    """
    try:
        db_manager = DatabaseManager(database_url)
        if db_manager.engine:
            db_manager.create_tables()
            return db_manager
        return None
    except Exception as e:
        logging.error(f"Error initializing database: {e}")
        return None