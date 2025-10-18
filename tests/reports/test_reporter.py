"""
ATS MAFIA Test Reporter

This module provides comprehensive test reporting functionality for
the ATS MAFIA framework.
"""

import json
import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timezone
from pathlib import Path
import logging

from ..framework.test_types import TestExecutionContext, TestSuiteResult
from .formatters import (
    HTMLReportFormatter,
    JSONReportFormatter,
    XMLReportFormatter,
    CSVReportFormatter
)
from .templates import ReportTemplates


class TestReporter:
    """
    Comprehensive test reporter for ATS MAFIA framework.
    
    Generates detailed reports in multiple formats including
    HTML, JSON, XML, and CSV.
    """
    
    def __init__(self, output_directory: str = "test_results/reports"):
        """
        Initialize the test reporter.
        
        Args:
            output_directory: Directory to save reports
        """
        self.output_directory = Path(output_directory)
        self.output_directory.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger("test_reporter")
        
        # Initialize formatters
        self.html_formatter = HTMLReportFormatter()
        self.json_formatter = JSONReportFormatter()
        self.xml_formatter = XMLReportFormatter()
        self.csv_formatter = CSVReportFormatter()
        
        # Report templates
        self.templates = ReportTemplates()
    
    async def generate_reports(self, 
                              execution_results: Dict[str, Any],
                              context: TestExecutionContext,
                              formats: Optional[List[str]] = None) -> Dict[str, str]:
        """
        Generate test reports in multiple formats.
        
        Args:
            execution_results: Test execution results
            context: Test execution context
            formats: List of formats to generate (defaults to all)
            
        Returns:
            Dictionary mapping format names to file paths
        """
        if formats is None:
            formats = ["html", "json", "xml", "csv"]
        
        execution_id = execution_results.get('execution_id', 'unknown')
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        
        report_files = {}
        
        for format_name in formats:
            try:
                if format_name.lower() == "html":
                    file_path = await self._generate_html_report(execution_results, context, execution_id, timestamp)
                    report_files["html"] = file_path
                elif format_name.lower() == "json":
                    file_path = await self._generate_json_report(execution_results, context, execution_id, timestamp)
                    report_files["json"] = file_path
                elif format_name.lower() == "xml":
                    file_path = await self._generate_xml_report(execution_results, context, execution_id, timestamp)
                    report_files["xml"] = file_path
                elif format_name.lower() == "csv":
                    file_path = await self._generate_csv_report(execution_results, context, execution_id, timestamp)
                    report_files["csv"] = file_path
                else:
                    self.logger.warning(f"Unsupported report format: {format_name}")
                    
            except Exception as e:
                self.logger.error(f"Failed to generate {format_name} report: {e}")
        
        # Generate summary report
        try:
            summary_path = await self._generate_summary_report(execution_results, context, execution_id, timestamp)
            report_files["summary"] = summary_path
        except Exception as e:
            self.logger.error(f"Failed to generate summary report: {e}")
        
        self.logger.info(f"Generated {len(report_files)} reports for execution {execution_id}")
        return report_files
    
    async def generate_suite_report(self,
                                   suite_results: Dict[str, Any],
                                   context: TestExecutionContext,
                                   formats: Optional[List[str]] = None) -> Dict[str, str]:
        """
        Generate reports for a specific test suite.
        
        Args:
            suite_results: Test suite results
            context: Test execution context
            formats: List of formats to generate
            
        Returns:
            Dictionary mapping format names to file paths
        """
        if formats is None:
            formats = ["html", "json"]
        
        suite_id = suite_results.get('suite_id', 'unknown')
        suite_name = suite_results.get('suite_name', 'unknown_suite')
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        
        report_files = {}
        
        for format_name in formats:
            try:
                if format_name.lower() == "html":
                    file_path = await self._generate_suite_html_report(suite_results, context, suite_id, suite_name, timestamp)
                    report_files["html"] = file_path
                elif format_name.lower() == "json":
                    file_path = await self._generate_suite_json_report(suite_results, context, suite_id, suite_name, timestamp)
                    report_files["json"] = file_path
                    
            except Exception as e:
                self.logger.error(f"Failed to generate suite {format_name} report: {e}")
        
        return report_files
    
    async def _generate_html_report(self,
                                   execution_results: Dict[str, Any],
                                   context: TestExecutionContext,
                                   execution_id: str,
                                   timestamp: str) -> str:
        """Generate HTML report."""
        file_path = self.output_directory / f"report_{execution_id}_{timestamp}.html"
        
        # Prepare report data
        report_data = {
            "execution_results": execution_results,
            "context": context.to_dict(),
            "generation_time": datetime.now(timezone.utc).isoformat(),
            "summary": self._calculate_summary(execution_results)
        }
        
        # Generate HTML content
        html_content = await self.html_formatter.format_report(report_data)
        
        # Write to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(file_path)
    
    async def _generate_json_report(self,
                                   execution_results: Dict[str, Any],
                                   context: TestExecutionContext,
                                   execution_id: str,
                                   timestamp: str) -> str:
        """Generate JSON report."""
        file_path = self.output_directory / f"report_{execution_id}_{timestamp}.json"
        
        # Prepare report data
        report_data = {
            "execution_results": execution_results,
            "context": context.to_dict(),
            "generation_time": datetime.now(timezone.utc).isoformat(),
            "summary": self._calculate_summary(execution_results)
        }
        
        # Generate JSON content
        json_content = await self.json_formatter.format_report(report_data)
        
        # Write to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(json_content)
        
        return str(file_path)
    
    async def _generate_xml_report(self,
                                  execution_results: Dict[str, Any],
                                  context: TestExecutionContext,
                                  execution_id: str,
                                  timestamp: str) -> str:
        """Generate XML report."""
        file_path = self.output_directory / f"report_{execution_id}_{timestamp}.xml"
        
        # Prepare report data
        report_data = {
            "execution_results": execution_results,
            "context": context.to_dict(),
            "generation_time": datetime.now(timezone.utc).isoformat(),
            "summary": self._calculate_summary(execution_results)
        }
        
        # Generate XML content
        xml_content = await self.xml_formatter.format_report(report_data)
        
        # Write to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        return str(file_path)
    
    async def _generate_csv_report(self,
                                  execution_results: Dict[str, Any],
                                  context: TestExecutionContext,
                                  execution_id: str,
                                  timestamp: str) -> str:
        """Generate CSV report."""
        file_path = self.output_directory / f"report_{execution_id}_{timestamp}.csv"
        
        # Prepare report data
        report_data = {
            "execution_results": execution_results,
            "context": context.to_dict(),
            "generation_time": datetime.now(timezone.utc).isoformat()
        }
        
        # Generate CSV content
        csv_content = await self.csv_formatter.format_report(report_data)
        
        # Write to file
        with open(file_path, 'w', encoding='utf-8', newline='') as f:
            f.write(csv_content)
        
        return str(file_path)
    
    async def _generate_summary_report(self,
                                      execution_results: Dict[str, Any],
                                      context: TestExecutionContext,
                                      execution_id: str,
                                      timestamp: str) -> str:
        """Generate summary report."""
        file_path = self.output_directory / f"summary_{execution_id}_{timestamp}.txt"
        
        summary = self._calculate_summary(execution_results)
        
        # Generate summary content
        summary_content = self.templates.get_summary_template().format(
            execution_id=execution_id,
            start_time=execution_results.get('start_time', 'Unknown'),
            end_time=execution_results.get('end_time', 'Unknown'),
            duration=execution_results.get('total_duration', 0),
            total_tests=summary['total_tests'],
            passed_tests=summary['passed_tests'],
            failed_tests=summary['failed_tests'],
            skipped_tests=summary['skipped_tests'],
            error_tests=summary['error_tests'],
            success_rate=summary['success_rate'],
            status="PASSED" if summary['failed_tests'] + summary['error_tests'] == 0 else "FAILED"
        )
        
        # Write to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(summary_content)
        
        return str(file_path)
    
    async def _generate_suite_html_report(self,
                                         suite_results: Dict[str, Any],
                                         context: TestExecutionContext,
                                         suite_id: str,
                                         suite_name: str,
                                         timestamp: str) -> str:
        """Generate HTML report for a specific suite."""
        file_path = self.output_directory / f"suite_{suite_name}_{timestamp}.html"
        
        # Prepare report data
        report_data = {
            "suite_results": suite_results,
            "context": context.to_dict(),
            "generation_time": datetime.now(timezone.utc).isoformat(),
            "summary": self._calculate_suite_summary(suite_results)
        }
        
        # Generate HTML content
        html_content = await self.html_formatter.format_suite_report(report_data)
        
        # Write to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(file_path)
    
    async def _generate_suite_json_report(self,
                                         suite_results: Dict[str, Any],
                                         context: TestExecutionContext,
                                         suite_id: str,
                                         suite_name: str,
                                         timestamp: str) -> str:
        """Generate JSON report for a specific suite."""
        file_path = self.output_directory / f"suite_{suite_name}_{timestamp}.json"
        
        # Prepare report data
        report_data = {
            "suite_results": suite_results,
            "context": context.to_dict(),
            "generation_time": datetime.now(timezone.utc).isoformat(),
            "summary": self._calculate_suite_summary(suite_results)
        }
        
        # Generate JSON content
        json_content = await self.json_formatter.format_suite_report(report_data)
        
        # Write to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(json_content)
        
        return str(file_path)
    
    def _calculate_summary(self, execution_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate summary statistics from execution results."""
        total_tests = execution_results.get('total_tests', 0)
        passed_tests = execution_results.get('passed_tests', 0)
        failed_tests = execution_results.get('failed_tests', 0)
        skipped_tests = execution_results.get('skipped_tests', 0)
        error_tests = execution_results.get('error_tests', 0)
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'skipped_tests': skipped_tests,
            'error_tests': error_tests,
            'success_rate': success_rate,
            'status': 'PASSED' if failed_tests + error_tests == 0 else 'FAILED'
        }
    
    def _calculate_suite_summary(self, suite_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate summary statistics for a suite."""
        total_tests = suite_results.get('total_tests', 0)
        passed_tests = suite_results.get('passed_tests', 0)
        failed_tests = suite_results.get('failed_tests', 0)
        skipped_tests = suite_results.get('skipped_tests', 0)
        error_tests = suite_results.get('error_tests', 0)
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'skipped_tests': skipped_tests,
            'error_tests': error_tests,
            'success_rate': success_rate,
            'status': 'PASSED' if failed_tests + error_tests == 0 else 'FAILED'
        }
    
    async def generate_trend_report(self,
                                   historical_results: List[Dict[str, Any]],
                                   output_file: Optional[str] = None) -> str:
        """
        Generate a trend report from historical test results.
        
        Args:
            historical_results: List of historical execution results
            output_file: Optional output file path
            
        Returns:
            Path to generated trend report
        """
        if output_file is None:
            timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
            output_file = self.output_directory / f"trend_report_{timestamp}.html"
        
        # Calculate trend statistics
        trend_data = self._calculate_trend_statistics(historical_results)
        
        # Generate trend report content
        trend_content = await self.html_formatter.format_trend_report(trend_data)
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(trend_content)
        
        return str(output_file)
    
    def _calculate_trend_statistics(self, historical_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate trend statistics from historical results."""
        if not historical_results:
            return {}
        
        # Sort by start time
        sorted_results = sorted(historical_results, key=lambda x: x.get('start_time', ''))
        
        # Calculate trends
        trend_data = {
            'executions': len(sorted_results),
            'date_range': {
                'start': sorted_results[0].get('start_time', ''),
                'end': sorted_results[-1].get('end_time', '')
            },
            'overall_stats': {
                'total_tests': sum(r.get('total_tests', 0) for r in sorted_results),
                'total_passed': sum(r.get('passed_tests', 0) for r in sorted_results),
                'total_failed': sum(r.get('failed_tests', 0) for r in sorted_results),
                'total_errors': sum(r.get('error_tests', 0) for r in sorted_results)
            },
            'success_rate_trend': [],
            'execution_times': [],
            'test_counts': []
        }
        
        # Calculate overall success rate
        total_tests = trend_data['overall_stats']['total_tests']
        total_passed = trend_data['overall_stats']['total_passed']
        trend_data['overall_success_rate'] = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        # Calculate per-execution trends
        for result in sorted_results:
            total_tests_exec = result.get('total_tests', 0)
            passed_tests_exec = result.get('passed_tests', 0)
            success_rate_exec = (passed_tests_exec / total_tests_exec * 100) if total_tests_exec > 0 else 0
            
            trend_data['success_rate_trend'].append({
                'execution_id': result.get('execution_id', ''),
                'date': result.get('start_time', ''),
                'success_rate': success_rate_exec
            })
            
            trend_data['execution_times'].append({
                'execution_id': result.get('execution_id', ''),
                'date': result.get('start_time', ''),
                'duration': result.get('total_duration', 0)
            })
            
            trend_data['test_counts'].append({
                'execution_id': result.get('execution_id', ''),
                'date': result.get('start_time', ''),
                'total_tests': total_tests_exec,
                'passed_tests': passed_tests_exec,
                'failed_tests': result.get('failed_tests', 0),
                'error_tests': result.get('error_tests', 0)
            })
        
        return trend_data
    
    async def generate_coverage_report(self,
                                     coverage_data: Dict[str, Any],
                                     output_file: Optional[str] = None) -> str:
        """
        Generate a code coverage report.
        
        Args:
            coverage_data: Coverage data
            output_file: Optional output file path
            
        Returns:
            Path to generated coverage report
        """
        if output_file is None:
            timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
            output_file = self.output_directory / f"coverage_report_{timestamp}.html"
        
        # Generate coverage report content
        coverage_content = await self.html_formatter.format_coverage_report(coverage_data)
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(coverage_content)
        
        return str(output_file)