#!/bin/bash

# Local Development Setup for Dog Care App
# This script sets up your local development environment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🐕 Dog Care App - Local Development Setup${NC}"
echo "Setting up your local development environment..."
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install via brew if on macOS
install_brew() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if command_exists brew; then
            echo -e "${YELLOW}📦 Installing $1 via Homebrew...${NC}"
            brew install "$1"
        else
            echo -e "${RED}❌ Homebrew not found. Please install Homebrew first.${NC}"
            echo "Visit: https://brew.sh/"
            exit 1
        fi
    else
        echo -e "${YELLOW}⚠️  Please install $1 manually for your OS${NC}"
        echo "Visit: $2"
    fi
}

# Check and install prerequisites
echo -e "${BLUE}🔍 Checking prerequisites...${NC}"

# Check AWS CLI
if ! command_exists aws; then
    echo -e "${YELLOW}⚠️  AWS CLI not found${NC}"
    install_brew "awscli" "https://aws.amazon.com/cli/"
else
    echo -e "${GREEN}✅ AWS CLI found${NC}"
fi

# Check SAM CLI
if ! command_exists sam; then
    echo -e "${YELLOW}⚠️  SAM CLI not found${NC}"
    install_brew "aws-sam-cli" "https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html"
else
    echo -e "${GREEN}✅ SAM CLI found${NC}"
fi

# Check Docker
if ! command_exists docker; then
    echo -e "${YELLOW}⚠️  Docker not found${NC}"
    echo "Please install Docker Desktop from: https://www.docker.com/products/docker-desktop"
    echo "Docker is required for local Lambda testing"
else
    echo -e "${GREEN}✅ Docker found${NC}"
fi

# Check Python
if ! command_exists python3; then
    echo -e "${YELLOW}⚠️  Python 3 not found${NC}"
    install_brew "python@3.11" "https://www.python.org/downloads/"
else
    PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
    echo -e "${GREEN}✅ Python ${PYTHON_VERSION} found${NC}"
fi

# Check pip
if ! command_exists pip3; then
    echo -e "${YELLOW}⚠️  pip3 not found${NC}"
    echo "Please install pip3"
else
    echo -e "${GREEN}✅ pip3 found${NC}"
fi

echo ""
echo -e "${BLUE}🔧 Setting up development environment...${NC}"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}🐍 Creating Python virtual environment...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${GREEN}✅ Virtual environment already exists${NC}"
fi

# Activate virtual environment and install dependencies
echo -e "${YELLOW}📦 Installing Python dependencies...${NC}"
source venv/bin/activate

# Create requirements-dev.txt if it doesn't exist
if [ ! -f "requirements-dev.txt" ]; then
    cat > requirements-dev.txt << EOF
# Development dependencies
boto3>=1.26.0
botocore>=1.29.0
pytest>=7.0.0
pytest-cov>=4.0.0
black>=22.0.0
flake8>=5.0.0
mypy>=1.0.0
requests>=2.28.0
moto>=4.2.0
EOF
fi

pip install -r requirements-dev.txt

echo -e "${GREEN}✅ Dependencies installed${NC}"

# Create test directory structure
echo -e "${YELLOW}🧪 Setting up test structure...${NC}"
mkdir -p tests/{unit,integration,fixtures}

# Create basic test files if they don't exist
if [ ! -f "tests/unit/test_dog_management.py" ]; then
    cat > tests/unit/test_dog_management.py << 'EOF'
import json
import pytest
from moto import mock_dynamodb
import boto3
from unittest.mock import patch
import sys
import os

# Add the functions directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../functions/dog_management'))

from app import lambda_handler


@mock_dynamodb
def test_create_dog():
    """Test creating a new dog"""
    # Setup mock DynamoDB
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    
    # Create mock tables
    dogs_table = dynamodb.create_table(
        TableName='dogs-test',
        KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
        BillingMode='PAY_PER_REQUEST'
    )
    
    owners_table = dynamodb.create_table(
        TableName='owners-test',
        KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
        BillingMode='PAY_PER_REQUEST'
    )
    
    # Create a test owner
    owners_table.put_item(Item={'id': 'owner-123', 'name': 'Test Owner'})
    
    # Test event
    event = {
        'httpMethod': 'POST',
        'path': '/dogs',
        'body': json.dumps({
            'name': 'Buddy',
            'breed': 'Golden Retriever',
            'age': 3,
            'size': 'large',
            'owner_id': 'owner-123'
        })
    }
    
    with patch.dict(os.environ, {'DOGS_TABLE': 'dogs-test', 'OWNERS_TABLE': 'owners-test'}):
        response = lambda_handler(event, None)
    
    assert response['statusCode'] == 201
    body = json.loads(response['body'])
    assert body['name'] == 'Buddy'
    assert body['breed'] == 'Golden Retriever'
    assert 'id' in body
EOF
fi

if [ ! -f "tests/conftest.py" ]; then
    cat > tests/conftest.py << 'EOF'
import pytest
import boto3
from moto import mock_dynamodb
import os

@pytest.fixture
def mock_env():
    """Mock environment variables for testing"""
    env_vars = {
        'DOGS_TABLE': 'dogs-test',
        'OWNERS_TABLE': 'owners-test',
        'BOOKINGS_TABLE': 'bookings-test',
        'PAYMENTS_TABLE': 'payments-test',
        'ENVIRONMENT': 'test'
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value
    
    yield env_vars
    
    # Cleanup
    for key in env_vars.keys():
        if key in os.environ:
            del os.environ[key]
EOF
fi

echo -e "${GREEN}✅ Test structure created${NC}"

# Create local development configuration
echo -e "${YELLOW}⚙️  Creating local configuration...${NC}"

if [ ! -f "samconfig.toml" ]; then
    cat > samconfig.toml << 'EOF'
version = 0.1

[default]
[default.build]
[default.build.parameters]
cached = true
parallel = true

[default.deploy]
[default.deploy.parameters]
stack_name = "dog-care-app-dev"
s3_prefix = "dog-care-app"
region = "us-east-1"
confirm_changeset = true
capabilities = "CAPABILITY_IAM"
image_repositories = []
EOF
fi

echo -e "${GREEN}✅ Configuration created${NC}"

# Create VS Code configuration
echo -e "${YELLOW}💻 Setting up VS Code configuration...${NC}"
mkdir -p .vscode

if [ ! -f ".vscode/settings.json" ]; then
    cat > .vscode/settings.json << 'EOF'
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.linting.mypyEnabled": true,
    "python.formatting.provider": "black",
    "python.formatting.blackArgs": [
        "--line-length",
        "88"
    ],
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": [
        "tests"
    ],
    "files.exclude": {
        "**/.aws-sam": true,
        "**/__pycache__": true,
        "**/*.pyc": true
    }
}
EOF
fi

if [ ! -f ".vscode/launch.json" ]; then
    cat > .vscode/launch.json << 'EOF'
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "SAM Local API",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/venv/bin/sam",
            "args": [
                "local",
                "start-api",
                "--debug-port",
                "5986"
            ],
            "console": "integratedTerminal",
            "cwd": "${workspaceFolder}"
        }
    ]
}
EOF
fi

echo -e "${GREEN}✅ VS Code configuration created${NC}"

# Create environment file template
if [ ! -f ".env.example" ]; then
    cat > .env.example << 'EOF'
# Environment variables for local development
AWS_REGION=us-east-1
ENVIRONMENT=dev
DOGS_TABLE=dogs-dev
OWNERS_TABLE=owners-dev
BOOKINGS_TABLE=bookings-dev
PAYMENTS_TABLE=payments-dev
EOF
fi

echo -e "${GREEN}✅ Environment template created${NC}"

# Create .gitignore
if [ ! -f ".gitignore" ]; then
    cat > .gitignore << 'EOF'
# AWS SAM
.aws-sam/
packaged-template.yaml

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual environments
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Environment variables
.env
.env.local

# Test coverage
.coverage
htmlcov/
.pytest_cache/

# Logs
*.log
EOF
fi

echo -e "${GREEN}✅ .gitignore created${NC}"

# Check AWS credentials
echo ""
echo -e "${BLUE}🔑 Checking AWS credentials...${NC}"
if aws sts get-caller-identity >/dev/null 2>&1; then
    echo -e "${GREEN}✅ AWS credentials configured${NC}"
    aws sts get-caller-identity
else
    echo -e "${YELLOW}⚠️  AWS credentials not configured${NC}"
    echo "Please run: aws configure"
fi

echo ""
echo -e "${GREEN}🎉 Local development setup complete!${NC}"
echo ""
echo -e "${BLUE}📋 Next steps:${NC}"
echo "1. Configure AWS credentials (if not done): aws configure"
echo "2. Activate virtual environment: source venv/bin/activate"
echo "3. Run tests: pytest"
echo "4. Start local API: sam local start-api"
echo "5. Deploy to AWS: ./deploy.sh dev"
echo ""
echo -e "${BLUE}🔧 Development commands:${NC}"
echo "- Run tests: pytest tests/"
echo "- Format code: black functions/"
echo "- Check linting: flake8 functions/"
echo "- Type check: mypy functions/"
echo "- Start local API: sam local start-api"
echo "- Build: sam build"
echo "- Deploy: ./deploy.sh dev"
echo ""
echo -e "${GREEN}Happy coding! 🐕${NC}"