# CodeCoach AI API Test Suite Documentation

## Overview

This comprehensive test suite provides production-grade testing for all critical API endpoints in the CodeCoach AI backend. The suite covers functional accuracy, boundary conditions, load limits, security vulnerabilities, and OpenAPI contract compliance.

## Test Suite Structure

```
tests/
├── __init__.py
├── conftest.py                 # Test configuration and fixtures
├── pytest.ini                 # Pytest configuration
├── test_requirements.txt      # Test dependencies
├── fixtures/                  # Test data factories and mocks
│   ├── __init__.py
│   └── factories.py          # Test data generation utilities
├── integration/              # Integration tests
│   ├── __init__.py
│   ├── test_health_endpoints.py
│   ├── test_coach_endpoints.py
│   ├── test_questions_endpoints.py
│   └── test_run_endpoints.py
├── unit/                     # Unit tests
│   ├── __init__.py
│   └── test_boundary_conditions.py
├── performance/              # Performance and load tests
│   ├── __init__.py
│   └── test_load_limits.py
├── security/                 # Security vulnerability tests
│   ├── __init__.py
│   └── test_security_vulnerabilities.py
└── e2e/                      # End-to-end tests (future)
    └── __init__.py
```

## Test Categories

### 1. Functional Accuracy Tests
- **Health Endpoints**: `/health`, `/health/detailed`
- **Coach Endpoints**: `/api/coach/`, `/api/coach/stream`, `/api/coach/modes`, `/api/coach/languages`
- **Questions Endpoints**: `/api/questions/`, `/api/questions/{id}`, `/api/questions/search`, `/api/questions/stats`
- **Run Endpoints**: `/api/run/`, `/api/run/validate`, `/api/run/languages`, `/api/run/runtimes`

### 2. Boundary Condition Tests
- Maximum string lengths (up to 10KB)
- Empty string handling
- Unicode character support
- Large array sizes (100+ elements)
- Numeric boundary values (INT_MAX, INT_MIN)
- Enum value validation
- Special character handling

### 3. Load Testing
- Concurrent request handling (100+ concurrent users)
- Memory usage monitoring (< 50MB increase)
- Response time percentiles (p50 < 100ms, p95 < 200ms)
- Rate limiting effectiveness
- CPU intensive operations
- Database query performance

### 4. Security Testing
- SQL injection prevention
- XSS (Cross-Site Scripting) prevention
- Path traversal protection
- Command injection prevention
- XXE (XML External Entity) prevention
- Rate limiting bypass attempts
- Authentication bypass attempts
- CORS policy validation
- Input validation length limits

### 5. OpenAPI Contract Validation
- Schema compliance testing
- Response format validation
- Required field enforcement
- Data type consistency
- HTTP status code verification

## Running Tests

### Prerequisites
```bash
cd backend
pip install -r requirements.txt
pip install -r tests/test_requirements.txt
```

### Basic Test Execution
```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit -v
pytest tests/integration -v
pytest tests/security -v
pytest tests/performance -v

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test markers
pytest -m "not slow" -v
pytest -m integration -v
```

### Performance Testing
```bash
# Run performance tests
pytest tests/performance -v

# Run load tests with Locust
locust -f tests/performance/test_load_limits.py --host http://localhost:8000

# Headless load testing
locust -f tests/performance/test_load_limits.py --headless -u 100 -r 10 -t 60s --host http://localhost:8000
```

### Security Testing
```bash
# Run security tests
pytest tests/security -v

# Run security scanning tools
bandit -r app -f json -o security-report.json
safety check --json --output safety-report.json
```

## Test Data and Factories

### Test Data Generators
- **CoachingRequestFactory**: Generates realistic coaching requests
- **CodeExecutionFactory**: Generates code execution requests
- **QuestionFactory**: Generates complete question objects
- **TestDataGenerator**: Provides utility methods for test data

### Mock Objects
- **MockNIMService**: Mock NVIDIA NIM API responses
- **MockPistonService**: Mock Piston API responses
- **MockQuestionsService**: Mock questions database

### Test Scenarios
- Valid request scenarios
- Invalid input scenarios
- Boundary condition scenarios
- Security attack scenarios
- Performance load scenarios

## Performance Benchmarks

### Response Time Targets
- **Health endpoints**: < 50ms
- **Questions endpoints**: < 200ms
- **Code execution**: < 2s
- **AI coaching**: < 5s
- **Streaming responses**: < 100ms initial response

### Load Targets
- **100 concurrent users** without degradation
- **1000 requests/minute** sustained load
- **99.9% uptime** during load testing
- **Memory usage** < 500MB under normal load

## Security Test Coverage

### Vulnerability Categories
- **Input validation** testing
- **Authentication bypass** attempts
- **Authorization escalation** testing
- **Rate limiting** bypass attempts
- **Injection attack** prevention

### Security Test Cases
- **Malicious payload** testing
- **Boundary overflow** testing
- **Authentication token** manipulation
- **CORS policy** bypass attempts
- **Rate limiting** stress testing

## CI/CD Integration

### GitHub Actions Workflow
- **Automated testing** on PR/push
- **Test coverage reporting** (minimum 85%)
- **Performance regression detection**
- **Security scanning** integration
- **OpenAPI contract validation**

### Quality Gates
- **Test coverage** >= 85%
- **Performance regression** < 10%
- **Security vulnerabilities** = 0
- **API contract compliance** = 100%
- **All tests passing** = Required

## Configuration Files

### pytest.ini
- Test discovery configuration
- Coverage settings
- Markers for test categorization
- Logging configuration

### test_requirements.txt
- All test dependencies
- Security scanning tools
- Performance testing libraries
- Coverage reporting tools

## Environment Variables

### Test Environment
```bash
# Required for testing
export NVIDIA_API_KEY=test_nvidia_key
export PISTON_API_URL=https://emkc.org/api/v2/piston
export QUESTIONS_FILE_PATH=tests/fixtures/test_questions.json
export RATE_LIMIT_PER_MINUTE=100
export RATE_LIMIT_PER_HOUR=1000
export ENVIRONMENT=testing
```

## Troubleshooting

### Common Issues
1. **Test failures**: Check environment variables and mock services
2. **Performance issues**: Monitor memory usage and response times
3. **Security warnings**: Review security scan reports
4. **Coverage gaps**: Check coverage reports for untested code

### Debug Commands
```bash
# Run tests with verbose output
pytest -v -s

# Run specific test with debugging
pytest tests/integration/test_health_endpoints.py::TestHealthEndpoints::test_health_check_basic -v -s

# Run with coverage report
pytest --cov=app --cov-report=term-missing

# Run security scan
bandit -r app -f json
```

## Future Enhancements

### Planned Test Additions
- **End-to-end workflow tests**
- **Database migration tests**
- **Integration with external services**
- **Performance benchmarking suite**
- **Security penetration testing**
- **Chaos engineering tests**

### Monitoring Integration
- **Test result dashboards**
- **Performance trend analysis**
- **Security vulnerability tracking**
- **API contract compliance monitoring**

## Support and Maintenance

### Test Maintenance
- Regular test data updates
- Performance benchmark recalibration
- Security test case updates
- Mock service updates

### Documentation Updates
- Test case documentation
- Performance benchmark updates
- Security vulnerability tracking
- API contract changes

For questions or issues, please refer to the main project documentation or create an issue in the repository.