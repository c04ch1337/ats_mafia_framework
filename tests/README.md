# ATS MAFIA Framework Testing Suite

This directory contains the comprehensive testing suite for the ATS MAFIA framework, designed to ensure all components work together seamlessly and meet production requirements.

## Overview

The testing suite provides:

- **Unit Tests**: Testing individual components in isolation
- **Integration Tests**: Testing component interactions
- **System Tests**: Testing complete user workflows
- **Security Tests**: Validating security measures and ethical compliance
- **Performance Tests**: Validating performance metrics and scalability
- **Compliance Tests**: Ensuring regulatory and ethical compliance

## Structure

```
tests/
├── framework/              # Core testing framework
│   ├── __init__.py
│   ├── test_framework.py   # Base test framework
│   ├── test_types.py       # Test type definitions
│   ├── test_runner.py      # Test execution engine
│   └── decorators.py       # Test decorators
├── unit/                   # Unit tests
│   ├── __init__.py
│   ├── test_config.py      # Configuration tests
│   ├── test_logging.py     # Logging tests
│   ├── test_profile_manager.py
│   ├── test_tool_system.py
│   ├── test_communication.py
│   └── test_orchestrator.py
├── integration/            # Integration tests
│   ├── __init__.py
│   ├── test_profile_integration.py
│   ├── test_tool_integration.py
│   └── test_communication_integration.py
├── system/                 # System tests
│   ├── __init__.py
│   ├── test_end_to_end.py
│   ├── test_training_scenarios.py
│   └── test_user_workflows.py
├── security/               # Security tests
│   ├── __init__.py
│   ├── test_authentication.py
│   ├── test_authorization.py
│   ├── test_encryption.py
│   └── test_ethical_compliance.py
├── performance/            # Performance tests
│   ├── __init__.py
│   ├── test_load_testing.py
│   ├── test_stress_testing.py
│   └── test_benchmarks.py
├── compliance/             # Compliance tests
│   ├── __init__.py
│   ├── test_gdpr_compliance.py
│   ├── test_security_standards.py
│   └── test_ethical_guidelines.py
├── utils/                  # Test utilities
│   ├── __init__.py
│   ├── test_utils.py       # General utilities
│   ├── mock_data_generator.py
│   ├── test_helpers.py
│   ├── assertions.py
│   └── fixtures.py
├── reports/                # Test reporting
│   ├── __init__.py
│   ├── test_reporter.py    # Main reporter
│   ├── validation_report_generator.py
│   ├── formatters/         # Report formatters
│   └── templates.py
├── run_tests.py            # Basic test runner
├── execute_comprehensive_tests.py  # Comprehensive test suite
└── README.md               # This file
```

## Quick Start

### Basic Test Execution

```bash
# Run all tests
python -m ats_mafia_framework.tests.run_tests

# Run specific test types
python -m ats_mafia_framework.tests.run_tests --test-type unit
python -m ats_mafia_framework.tests.run_tests --test-type integration
python -m ats_mafia_framework.tests.run_tests --test-type system

# Run with validation
python -m ats_mafia_framework.tests.run_tests --validation

# Run with parallel execution
python -m ats_mafia_framework.tests.run_tests --parallel --workers 4
```

### Comprehensive Test Execution

```bash
# Run full comprehensive test suite
python -m ats_mafia_framework.tests.execute_comprehensive_tests
```

### Test Configuration

Tests can be configured through command-line arguments:

- `--test-type`: Type of tests to run (unit, integration, system, all)
- `--output-dir`: Output directory for test results
- `--parallel`: Run tests in parallel
- `--workers`: Number of parallel workers
- `--timeout`: Test timeout in seconds
- `--log-level`: Log level (DEBUG, INFO, WARNING, ERROR)
- `--validation`: Run comprehensive validation tests

## Test Categories

### Unit Tests

Unit tests test individual components in isolation:

- **Configuration System**: Loading, validation, and management
- **Logging System**: Structured logging and audit trails
- **Profile Manager**: Profile loading and management
- **Tool System**: Tool registration and execution
- **Communication**: Message handling and protocols
- **Orchestrator**: Training session management

### Integration Tests

Integration tests test component interactions:

- **Profile Integration**: Profile switching and management
- **Tool Integration**: Tool execution with profiles
- **Communication Integration**: Agent communication workflows
- **Orchestration Integration**: End-to-end training scenarios

### System Tests

System tests test complete user workflows:

- **End-to-End Scenarios**: Complete training workflows
- **Training Scenarios**: Red Team vs Blue Team exercises
- **User Workflows**: Typical user interactions
- **Multi-Agent Scenarios**: Complex multi-agent training

### Security Tests

Security tests validate security measures:

- **Authentication**: Agent and session authentication
- **Authorization**: Role-based access control
- **Encryption**: Data and communication encryption
- **Ethical Compliance**: Ethical guidelines enforcement

### Performance Tests

Performance tests validate system performance:

- **Load Testing**: Performance under expected load
- **Stress Testing**: Performance beyond expected limits
- **Benchmarks**: Performance metrics and baselines
- **Scalability**: System scalability testing

### Compliance Tests

Compliance tests ensure regulatory compliance:

- **GDPR Compliance**: Data protection requirements
- **Security Standards**: Industry security standards
- **Ethical Guidelines**: Ethical training requirements
- **Access Controls**: Access control compliance

## Test Framework Features

### Decorators

The testing framework provides several decorators for marking tests:

```python
@unit_test(name="test_config_loading", priority=TestPriority.HIGH)
def test_config_loading(self):
    # Unit test implementation
    pass

@integration_test(timeout=300.0)
def test_profile_integration(self):
    # Integration test implementation
    pass

@security_test
def test_authentication_security(self):
    # Security test implementation
    pass
```

### Test Utilities

The framework provides utilities for:

- **Mock Data Generation**: Generate test data
- **Temporary Files**: Create temporary test files
- **Network Simulation**: Simulate network conditions
- **Performance Measurement**: Measure execution time
- **Condition Waiting**: Wait for conditions to be met

### Reporting

The framework generates comprehensive reports in multiple formats:

- **HTML Reports**: Interactive web reports
- **JSON Reports**: Machine-readable reports
- **XML Reports**: Structured XML reports
- **CSV Reports**: Tabular data reports
- **Validation Reports**: Comprehensive validation reports

## Test Results

Test results are saved to the specified output directory:

```
test_results/
├── reports/
│   ├── report_*.html        # HTML reports
│   ├── report_*.json        # JSON reports
│   ├── report_*.xml         # XML reports
│   ├── report_*.csv         # CSV reports
│   └── validation_report.json  # Validation report
├── coverage/
│   └── coverage_report.json # Coverage report
├── performance/
│   └── performance_benchmarks.json
└── logs/
    └── test_execution.log   # Execution logs
```

## Validation Criteria

The ATS MAFIA framework is considered production-ready when:

1. **Success Rate**: ≥95% of all tests pass
2. **Critical Components**: All core components pass
3. **Security**: All security tests pass
4. **Performance**: Performance metrics meet requirements
5. **Compliance**: All compliance tests pass
6. **Coverage**: ≥80% code coverage

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed
2. **Permission Errors**: Check file permissions for output directory
3. **Timeout Errors**: Increase timeout values for slow tests
4. **Memory Errors**: Reduce parallel workers or increase memory

### Debug Mode

Run tests in debug mode for detailed information:

```bash
python -m ats_mafia_framework.tests.run_tests --log-level DEBUG
```

### Test Isolation

Tests are designed to be isolated and independent. Each test:
- Creates its own temporary environment
- Cleans up after execution
- Doesn't depend on other tests

## Contributing

When adding new tests:

1. Follow the existing test structure
2. Use appropriate decorators
3. Include comprehensive assertions
4. Add documentation for complex tests
5. Update this README if adding new test categories

## Continuous Integration

The test suite is designed for CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run Tests
  run: |
    python -m ats_mafia_framework.tests.execute_comprehensive_tests
    
- name: Upload Test Results
  uses: actions/upload-artifact@v2
  with:
    name: test-results
    path: comprehensive_test_results/
```

## Support

For test-related issues:

1. Check the test execution logs
2. Review the validation report
3. Verify test environment setup
4. Consult the framework documentation

## License

This testing suite is part of the ATS MAFIA framework and follows the same licensing terms.