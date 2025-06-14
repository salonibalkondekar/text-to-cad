#!/bin/bash

# Text-to-CAD Backend Test Runner
# This script runs all tests with various options

echo "==================================="
echo "Text-to-CAD Backend Test Suite"
echo "==================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Change to backend directory
cd "$(dirname "$0")"

# Function to run tests
run_tests() {
    local test_type=$1
    local test_command=$2
    
    echo -e "\n${YELLOW}Running $test_type tests...${NC}"
    if $test_command; then
        echo -e "${GREEN}✓ $test_type tests passed${NC}"
        return 0
    else
        echo -e "${RED}✗ $test_type tests failed${NC}"
        return 1
    fi
}

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo -e "${YELLOW}Warning: No virtual environment detected${NC}"
    echo "Consider activating a virtual environment before running tests"
fi

# Install test dependencies if needed
echo "Checking test dependencies..."
if command -v uv > /dev/null 2>&1; then
    echo "Using uv for dependency management..."
    INSTALL_CMD="uv pip install"
else
    echo "Using pip for dependency management..."
    INSTALL_CMD="pip install"
fi

pip show pytest > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "Installing test dependencies..."
    $INSTALL_CMD -r requirements.txt
fi

# Run different test suites
all_passed=true

# Unit tests
if ! run_tests "Unit" "pytest tests/test_app.py -v --tb=short"; then
    all_passed=false
fi

# Security tests - with timeout to prevent infinite loops
if ! run_tests "Security" "pytest tests/test_security.py -v --tb=short --timeout=10"; then
    all_passed=false
fi

# Integration tests
if ! run_tests "Integration" "pytest tests/test_integration.py -v --tb=short"; then
    all_passed=false
fi

# All tests with coverage - skip if individual tests failed
if [ "$all_passed" = true ]; then
    echo -e "\n${YELLOW}Running all tests with coverage report...${NC}"
    pytest tests/ --cov=app --cov-report=term-missing --cov-report=html:htmlcov -v --tb=short
    
    # Print summary
    echo -e "\n${GREEN}====================================${NC}"
    echo -e "${GREEN}Test Summary${NC}"
    echo -e "${GREEN}====================================${NC}"
    pytest tests/ --cov=app --cov-report=term-missing | grep -E "(passed|failed|coverage|TOTAL)"
else
    echo -e "\n${RED}Skipping coverage report due to test failures${NC}"
fi

# Generate coverage badge if coverage-badge is installed
if command -v coverage-badge &> /dev/null; then
    coverage-badge -o coverage.svg -f
    echo -e "${GREEN}Coverage badge generated: coverage.svg${NC}"
fi

# Summary
echo -e "\n==================================="
if [ "$all_passed" = true ]; then
    echo -e "${GREEN}All test suites passed!${NC}"
    echo -e "Coverage report: ${YELLOW}htmlcov/index.html${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed!${NC}"
    exit 1
fi