"""
ATS MAFIA Framework Testing Suite

This module provides comprehensive testing infrastructure for the ATS MAFIA framework.
It includes unit tests, integration tests, system tests, and validation utilities.
"""

__version__ = "1.0.0"
__author__ = "ATS MAFIA Team"
__description__ = "Comprehensive testing suite for ATS MAFIA framework"

# Test framework imports
from .framework import TestFramework, TestRunner
from .utils import TestUtils, MockDataGenerator, TestHelpers
from .reports import TestReporter, ValidationReportGenerator
from .fixtures import TestFixtures, TestData

__all__ = [
    "TestFramework",
    "TestRunner", 
    "TestUtils",
    "MockDataGenerator",
    "TestHelpers",
    "TestReporter",
    "ValidationReportGenerator",
    "TestFixtures",
    "TestData"
]