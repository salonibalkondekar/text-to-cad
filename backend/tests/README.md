# Text-to-CAD Backend Test Suite

This directory contains comprehensive tests for the Text-to-CAD backend API.

## Test Structure

```
tests/
├── __init__.py          # Test package initialization
├── conftest.py          # Pytest configuration and fixtures
├── test_app.py          # Main application tests
├── test_security.py     # Security and edge case tests
├── test_integration.py  # Integration and workflow tests
└── README.md           # This file
```

## Test Categories

### 1. Unit Tests (`test_app.py`)
- API endpoint functionality
- Helper function behavior
- Data validation
- Error handling
- Model generation logic

### 2. Security Tests (`test_security.py`)
- Code injection prevention
- Path traversal protection
- XSS handling
- Resource exhaustion protection
- Authentication bypass attempts
- Input validation

### 3. Integration Tests (`test_integration.py`)
- Complete user workflows
- AI service failure recovery
- Data persistence across operations
- Concurrent operation handling
- Error recovery mechanisms

## Running Tests

### Quick Start
```bash
# Run all tests
cd backend
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_app.py

# Run specific test class
pytest tests/test_app.py::TestAPIEndpoints

# Run specific test
pytest tests/test_app.py::TestAPIEndpoints::test_generate_model_success
```

### Using the Test Runner Script
```bash
cd backend
./run_tests.sh
```

### Test Markers
```bash
# Run only unit tests
pytest -m "unit"

# Run only integration tests
pytest -m "integration"

# Run only security tests
pytest -m "security"

# Skip slow tests
pytest -m "not slow"
```

## Test Coverage

Current test coverage targets:
- Overall: 80% minimum
- Critical paths: 95% minimum
- Error handling: 90% minimum

View coverage report:
```bash
# Generate HTML coverage report
pytest --cov=app --cov-report=html

# Open in browser
open htmlcov/index.html
```

## Key Test Scenarios

### API Endpoints
- ✅ Model generation from text prompts
- ✅ Direct BadCAD code execution
- ✅ User registration and authentication
- ✅ Model count tracking and limits
- ✅ File download functionality
- ✅ Admin data access

### Error Handling
- ✅ AI service failures with fallback
- ✅ BadCAD execution errors
- ✅ Invalid input handling
- ✅ Resource limits enforcement
- ✅ Concurrent request handling

### Security
- ✅ Code injection attempts
- ✅ Path traversal in downloads
- ✅ XSS in prompts
- ✅ Resource exhaustion
- ⚠️  Admin endpoint lacks authentication (documented issue)
- ⚠️  CORS allows all origins (documented issue)

## Known Issues and Limitations

1. **Security Concerns**
   - Admin endpoint has no authentication
   - CORS configuration allows all origins
   - Code execution uses unrestricted `exec()`

2. **Resource Management**
   - No cleanup of temporary STL files
   - In-memory storage not suitable for production
   - No rate limiting implemented

3. **Data Persistence**
   - JSON file storage is not thread-safe
   - No database integration
   - Manual user count tracking

## Writing New Tests

### Test Structure Template
```python
class TestFeatureName:
    """Test description"""
    
    def setup_method(self):
        """Reset state before each test"""
        # Clear databases, reset mocks, etc.
    
    def test_happy_path(self):
        """Test normal successful operation"""
        # Arrange
        # Act
        # Assert
    
    def test_error_case(self):
        """Test error handling"""
        # Test specific error scenarios
    
    def test_edge_case(self):
        """Test boundary conditions"""
        # Test limits, empty values, etc.
```

### Mocking External Services
```python
# Mock Gemini AI
with patch('app.generate_badcad_code_with_gemini') as mock_gemini:
    mock_gemini.return_value = "BadCAD code here"
    
# Mock BadCAD execution
with patch('app.execute_badcad_and_export') as mock_execute:
    mock_execute.return_value = "/path/to/stl"
```

## CI/CD Integration

Tests run automatically on:
- Push to main/develop branches
- Pull requests to main
- Manual workflow dispatch

GitHub Actions workflow: `.github/workflows/backend-tests.yml`

## Future Improvements

1. **Add performance tests**
   - Response time benchmarks
   - Load testing
   - Memory usage profiling

2. **Enhance security testing**
   - Automated vulnerability scanning
   - Penetration testing scenarios
   - Authentication implementation tests

3. **Improve test isolation**
   - Better cleanup between tests
   - Dockerized test environment
   - Test database fixtures

4. **Add contract tests**
   - API schema validation
   - Frontend-backend contract tests
   - OpenAPI specification compliance