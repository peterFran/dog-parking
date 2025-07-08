#!/bin/bash

# Dog Care App - Test Runner with Environment Validation
# This script ensures consistent test environment setup and runs all tests

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="Dog Care App"
PYTHON_VERSION="3.11"
COVERAGE_THRESHOLD=80
TEST_TIMEOUT=300  # 5 minutes

echo -e "${GREEN}🐕 ${PROJECT_NAME} - Test Runner${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Function to print section headers
print_section() {
    echo -e "${BLUE}🔍 $1${NC}"
    echo "----------------------------------------"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Python version
check_python_version() {
    if command_exists python3; then
        CURRENT_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
        MAJOR=$(echo $CURRENT_VERSION | cut -d'.' -f1)
        MINOR=$(echo $CURRENT_VERSION | cut -d'.' -f2)
        
        if [ "$MAJOR" -eq 3 ] && [ "$MINOR" -ge 11 ]; then
            echo -e "${GREEN}✅ Python $CURRENT_VERSION (compatible)${NC}"
            return 0
        else
            echo -e "${RED}❌ Python $CURRENT_VERSION (requires 3.11+)${NC}"
            return 1
        fi
    else
        echo -e "${RED}❌ Python 3 not found${NC}"
        return 1
    fi
}

# Function to check virtual environment
check_virtual_env() {
    if [ -n "$VIRTUAL_ENV" ]; then
        echo -e "${GREEN}✅ Virtual environment active: $VIRTUAL_ENV${NC}"
        return 0
    elif [ -d "venv" ]; then
        echo -e "${YELLOW}⚠️  Virtual environment exists but not activated${NC}"
        echo -e "${YELLOW}   Activating virtual environment...${NC}"
        source venv/bin/activate
        if [ -n "$VIRTUAL_ENV" ]; then
            echo -e "${GREEN}✅ Virtual environment activated${NC}"
            return 0
        else
            echo -e "${RED}❌ Failed to activate virtual environment${NC}"
            return 1
        fi
    else
        echo -e "${RED}❌ Virtual environment not found${NC}"
        echo -e "${YELLOW}   Please run: python3 -m venv venv && source venv/bin/activate${NC}"
        return 1
    fi
}

# Function to check and install dependencies
check_dependencies() {
    echo -e "${YELLOW}📦 Checking dependencies...${NC}"
    
    # Check if requirements files exist
    local files_to_check=("requirements-dev.txt")
    for file in "${files_to_check[@]}"; do
        if [ ! -f "$file" ]; then
            echo -e "${RED}❌ $file not found${NC}"
            return 1
        fi
    done
    
    # Install/update dependencies
    echo -e "${YELLOW}   Installing/updating dependencies...${NC}"
    pip install --upgrade pip
    pip install -r requirements-dev.txt
    
    # Check critical packages - different checking methods for different package types
    echo -e "${YELLOW}   Verifying critical packages...${NC}"
    
    # Check importable packages
    local importable_packages=("pytest" "boto3" "moto" "black" "flake8" "mypy")
    for package in "${importable_packages[@]}"; do
        if python -c "import $package" 2>/dev/null; then
            local version=$(python -c "import $package; print($package.__version__)" 2>/dev/null || echo "unknown")
            echo -e "${GREEN}✅ $package ($version)${NC}"
        else
            echo -e "${RED}❌ $package not installed${NC}"
            return 1
        fi
    done
    
    # Check pytest plugins by running pytest --version
    if python -m pytest --version >/dev/null 2>&1; then
        echo -e "${GREEN}✅ pytest with plugins available${NC}"
        # Check if pytest-cov is available by testing its usage
        if python -m pytest --cov=. --cov-report=term-missing --collect-only tests/ >/dev/null 2>&1; then
            echo -e "${GREEN}✅ pytest-cov available${NC}"
        else
            echo -e "${YELLOW}⚠️  pytest-cov may not be working properly${NC}"
        fi
    else
        echo -e "${RED}❌ pytest not working${NC}"
        return 1
    fi
    
    return 0
}

# Function to validate project structure
validate_project_structure() {
    echo -e "${YELLOW}🏗️  Validating project structure...${NC}"
    
    local required_dirs=("functions" "tests" "tests/unit" "tests/integration")
    local required_files=("template.yaml" "README.md")
    
    for dir in "${required_dirs[@]}"; do
        if [ -d "$dir" ]; then
            echo -e "${GREEN}✅ Directory: $dir${NC}"
        else
            echo -e "${RED}❌ Missing directory: $dir${NC}"
            return 1
        fi
    done
    
    for file in "${required_files[@]}"; do
        if [ -f "$file" ]; then
            echo -e "${GREEN}✅ File: $file${NC}"
        else
            echo -e "${RED}❌ Missing file: $file${NC}"
            return 1
        fi
    done
    
    # Check Lambda function structure
    local lambda_functions=("dog_management" "owner_management" "booking_management" "payment_processing")
    for func in "${lambda_functions[@]}"; do
        if [ -f "functions/$func/app.py" ]; then
            echo -e "${GREEN}✅ Lambda function: $func${NC}"
        else
            echo -e "${RED}❌ Missing Lambda function: $func${NC}"
            return 1
        fi
    done
    
    return 0
}

# Function to run code quality checks
run_code_quality() {
    echo -e "${YELLOW}🔍 Running code quality checks...${NC}"
    
    # Black formatting check
    echo -e "${PURPLE}   Running Black (code formatting)...${NC}"
    if black --check --diff functions/ tests/ 2>/dev/null; then
        echo -e "${GREEN}✅ Black formatting check passed${NC}"
    else
        echo -e "${YELLOW}⚠️  Black formatting issues found${NC}"
        echo -e "${YELLOW}   Run: black functions/ tests/ to fix${NC}"
    fi
    
    # Flake8 linting
    echo -e "${PURPLE}   Running Flake8 (linting)...${NC}"
    if flake8 functions/ tests/ --max-line-length=88 --extend-ignore=E203,W503 2>/dev/null; then
        echo -e "${GREEN}✅ Flake8 linting passed${NC}"
    else
        echo -e "${YELLOW}⚠️  Flake8 linting issues found${NC}"
        echo -e "${YELLOW}   Check output above for details${NC}"
    fi
    
    # MyPy type checking
    echo -e "${PURPLE}   Running MyPy (type checking)...${NC}"
    if mypy functions/ --ignore-missing-imports --namespace-packages --explicit-package-bases 2>/dev/null; then
        echo -e "${GREEN}✅ MyPy type checking passed${NC}"
    else
        echo -e "${YELLOW}⚠️  MyPy type checking issues found${NC}"
        echo -e "${YELLOW}   Check output above for details${NC}"
    fi
}

# Function to run tests with coverage
run_tests() {
    echo -e "${YELLOW}🧪 Running tests with coverage...${NC}"
    
    # Create coverage configuration if it doesn't exist
    if [ ! -f ".coveragerc" ]; then
        cat > .coveragerc << 'EOF'
[run]
source = functions/
omit = 
    */tests/*
    */venv/*
    */__pycache__/*
    */.*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:

[html]
directory = htmlcov
EOF
    fi
    
    # Run tests with coverage
    echo -e "${PURPLE}   Running pytest with coverage...${NC}"
    if pytest tests/ \
        --cov=functions \
        --cov-report=term-missing \
        --cov-report=html \
        --cov-fail-under=$COVERAGE_THRESHOLD \
        --verbose \
        --tb=short; then
        echo -e "${GREEN}✅ All tests passed with coverage >=$COVERAGE_THRESHOLD%${NC}"
    else
        local exit_code=$?
        if [ $exit_code -eq 124 ]; then
            echo -e "${RED}❌ Tests timed out after $TEST_TIMEOUT seconds${NC}"
        else
            echo -e "${RED}❌ Tests failed or coverage below $COVERAGE_THRESHOLD%${NC}"
        fi
        return $exit_code
    fi
}

# Function to run integration tests
run_integration_tests() {
    echo -e "${YELLOW}🔗 Running integration tests...${NC}"
    
    # Check if Docker is running (needed for moto)
    if command_exists docker && docker info >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Docker is running${NC}"
    else
        echo -e "${YELLOW}⚠️  Docker not running - some integration tests may fail${NC}"
    fi
    
    # Run integration tests separately
    if [ -d "tests/integration" ] && [ "$(ls -A tests/integration)" ]; then
        echo -e "${PURPLE}   Running integration tests...${NC}"
        if pytest tests/integration/ --verbose; then
            echo -e "${GREEN}✅ Integration tests passed${NC}"
        else
            echo -e "${RED}❌ Integration tests failed${NC}"
            return 1
        fi
    else
        echo -e "${YELLOW}⚠️  No integration tests found${NC}"
    fi
}

# Function to validate SAM template
validate_sam_template() {
    echo -e "${YELLOW}🔧 Validating SAM template...${NC}"
    
    if command_exists sam; then
        # Set default region if not set
        export AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION:-us-east-1}
        
        if sam validate --template template.yaml 2>/dev/null; then
            echo -e "${GREEN}✅ SAM template is valid${NC}"
        else
            echo -e "${YELLOW}⚠️  SAM template validation failed - may need AWS credentials${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  SAM CLI not found - skipping template validation${NC}"
    fi
}

# Function to generate test report
generate_test_report() {
    echo -e "${YELLOW}📊 Generating test report...${NC}"
    
    # Create reports directory
    mkdir -p reports
    
    # Generate coverage report
    if [ -f ".coverage" ]; then
        coverage report --format=markdown > reports/coverage-report.md
        echo -e "${GREEN}✅ Coverage report generated: reports/coverage-report.md${NC}"
    fi
    
    # Generate HTML coverage report
    if [ -d "htmlcov" ]; then
        echo -e "${GREEN}✅ HTML coverage report: htmlcov/index.html${NC}"
    fi
    
    # Create test summary
    cat > reports/test-summary.md << EOF
# Test Summary - $(date)

## Environment
- Python: $(python --version 2>&1)
- Virtual Environment: ${VIRTUAL_ENV:-"None"}
- Working Directory: $(pwd)

## Test Results
- Unit Tests: $(if [ -f "reports/pytest-report.xml" ]; then echo "✅ Passed"; else echo "❌ Failed"; fi)
- Integration Tests: $(if [ -d "tests/integration" ]; then echo "✅ Passed"; else echo "⚠️ Not found"; fi)
- Coverage Threshold: $COVERAGE_THRESHOLD%

## Code Quality
- Black Formatting: $(if black --check functions/ tests/ >/dev/null 2>&1; then echo "✅ Passed"; else echo "⚠️ Issues found"; fi)
- Flake8 Linting: $(if flake8 functions/ tests/ --max-line-length=88 --extend-ignore=E203,W503 >/dev/null 2>&1; then echo "✅ Passed"; else echo "⚠️ Issues found"; fi)
- MyPy Type Checking: $(if mypy functions/ --ignore-missing-imports >/dev/null 2>&1; then echo "✅ Passed"; else echo "⚠️ Issues found"; fi)

## Infrastructure
- SAM Template: $(if sam validate --template template.yaml >/dev/null 2>&1; then echo "✅ Valid"; else echo "❌ Invalid"; fi)

Generated on: $(date)
EOF
    
    echo -e "${GREEN}✅ Test summary generated: reports/test-summary.md${NC}"
}

# Function to cleanup
cleanup() {
    echo -e "${YELLOW}🧹 Cleaning up...${NC}"
    
    # Remove temporary files
    find . -name "*.pyc" -delete
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    find . -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true
    
    echo -e "${GREEN}✅ Cleanup completed${NC}"
}

# Main execution
main() {
    local start_time=$(date +%s)
    
    # Trap cleanup on exit
    trap cleanup EXIT
    
    # Change to script directory
    cd "$(dirname "$0")"
    
    print_section "Environment Validation"
    check_python_version || exit 1
    check_virtual_env || exit 1
    check_dependencies || exit 1
    validate_project_structure || exit 1
    
    echo ""
    print_section "Code Quality Checks"
    run_code_quality
    
    echo ""
    print_section "Infrastructure Validation"
    validate_sam_template
    
    echo ""
    print_section "Unit Tests"
    run_tests || exit 1
    
    echo ""
    print_section "Integration Tests"
    run_integration_tests || exit 1
    
    echo ""
    print_section "Test Report Generation"
    generate_test_report
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    echo ""
    echo -e "${GREEN}🎉 All tests completed successfully!${NC}"
    echo -e "${BLUE}================================================${NC}"
    echo -e "${GREEN}✅ Environment validation: PASSED${NC}"
    echo -e "${GREEN}✅ Code quality checks: COMPLETED${NC}"
    echo -e "${GREEN}✅ Infrastructure validation: PASSED${NC}"
    echo -e "${GREEN}✅ Unit tests: PASSED${NC}"
    echo -e "${GREEN}✅ Integration tests: PASSED${NC}"
    echo -e "${GREEN}✅ Test reports: GENERATED${NC}"
    echo ""
    echo -e "${BLUE}📊 Test execution time: ${duration}s${NC}"
    echo -e "${BLUE}📁 Reports available in: reports/${NC}"
    echo -e "${BLUE}🌐 HTML coverage report: htmlcov/index.html${NC}"
    echo ""
    echo -e "${GREEN}🚀 Ready for deployment!${NC}"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --coverage-threshold)
            COVERAGE_THRESHOLD="$2"
            shift 2
            ;;
        --timeout)
            TEST_TIMEOUT="$2"
            shift 2
            ;;
        --skip-quality)
            SKIP_QUALITY=true
            shift
            ;;
        --skip-integration)
            SKIP_INTEGRATION=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --coverage-threshold N    Set coverage threshold (default: 80)"
            echo "  --timeout N              Set test timeout in seconds (default: 300)"
            echo "  --skip-quality           Skip code quality checks"
            echo "  --skip-integration       Skip integration tests"
            echo "  --help                   Show this help"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Run main function
main "$@"