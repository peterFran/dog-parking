#!/bin/bash

# Firebase Emulator Integration Test Runner
# This script starts the Firebase Auth emulator and runs integration tests

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔥 Firebase Emulator Integration Test Runner${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Check if Firebase CLI is installed
if ! command -v firebase &> /dev/null; then
    echo -e "${RED}❌ Firebase CLI not found${NC}"
    echo -e "${YELLOW}Install with: npm install -g firebase-tools${NC}"
    exit 1
fi

# Check if SAM CLI is available
if ! command -v sam &> /dev/null; then
    echo -e "${YELLOW}⚠️  SAM CLI not found - you'll need to start the API manually${NC}"
    echo -e "${YELLOW}Install SAM CLI or start API with another method${NC}"
    SAM_AVAILABLE=false
else
    SAM_AVAILABLE=true
fi

# Set environment variables
export FIREBASE_AUTH_EMULATOR_HOST="localhost:9099"
export API_BASE_URL="http://127.0.0.1:3000"

echo -e "${BLUE}🔧 Configuration:${NC}"
echo "Firebase Auth Emulator: $FIREBASE_AUTH_EMULATOR_HOST"
echo "API Base URL: $API_BASE_URL"
echo ""

# Function to cleanup processes
cleanup() {
    echo -e "\n${YELLOW}🧹 Cleaning up processes...${NC}"
    
    # Kill Firebase emulator
    if [[ -n $FIREBASE_PID ]]; then
        kill $FIREBASE_PID 2>/dev/null || true
        echo "Firebase emulator stopped"
    fi
    
    # Kill SAM local API
    if [[ -n $SAM_PID ]]; then
        kill $SAM_PID 2>/dev/null || true
        echo "SAM local API stopped"
    fi
    
    echo -e "${GREEN}✅ Cleanup completed${NC}"
}

# Set up cleanup on script exit
trap cleanup EXIT

# Start Firebase Auth emulator
echo -e "${BLUE}🔥 Starting Firebase Auth emulator...${NC}"
firebase emulators:start --only auth --project demo-dog-care > firebase-emulator.log 2>&1 &
FIREBASE_PID=$!

# Wait for Firebase emulator to start
echo "Waiting for Firebase emulator to start..."
sleep 5

# Check if Firebase emulator is running
if ! curl -s http://localhost:9099/ > /dev/null; then
    echo -e "${RED}❌ Firebase emulator failed to start${NC}"
    echo "Check firebase-emulator.log for details"
    exit 1
fi

echo -e "${GREEN}✅ Firebase emulator running on port 9099${NC}"

# Start SAM local API if available
if [[ $SAM_AVAILABLE == true ]]; then
    echo -e "${BLUE}🚀 Starting SAM local API...${NC}"
    sam local start-api --host 127.0.0.1 --port 3000 > sam-local.log 2>&1 &
    SAM_PID=$!
    
    # Wait for SAM to start
    echo "Waiting for SAM local API to start..."
    sleep 10
    
    # Check if API is running
    if ! curl -s http://127.0.0.1:3000/venues > /dev/null; then
        echo -e "${YELLOW}⚠️  SAM local API might not be ready yet${NC}"
        echo "Continuing with tests - they will skip if API is not available"
    else
        echo -e "${GREEN}✅ SAM local API running on port 3000${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Please start your API manually before running tests${NC}"
    echo "Example: sam local start-api --host 127.0.0.1 --port 3000"
    echo ""
    read -p "Press Enter when your API is running, or Ctrl+C to cancel..."
fi

echo ""
echo -e "${BLUE}🧪 Running integration tests...${NC}"
echo "Test file: tests/integration/test_api_with_firebase_emulator.py"
echo ""

# Activate virtual environment if it exists
if [[ -d "venv" ]]; then
    source venv/bin/activate
    echo -e "${GREEN}✅ Virtual environment activated${NC}"
fi

# Run the integration tests
python -m pytest tests/integration/test_api_with_firebase_emulator.py -v --tb=short

TEST_EXIT_CODE=$?

echo ""
if [[ $TEST_EXIT_CODE -eq 0 ]]; then
    echo -e "${GREEN}🎉 All integration tests passed!${NC}"
else
    echo -e "${RED}❌ Some integration tests failed${NC}"
fi

echo ""
echo -e "${BLUE}📋 Log files created:${NC}"
echo "- firebase-emulator.log: Firebase emulator output"
if [[ $SAM_AVAILABLE == true ]]; then
    echo "- sam-local.log: SAM local API output"
fi

echo ""
echo -e "${BLUE}🔗 Firebase Emulator UI: http://localhost:4000${NC}"
echo -e "${BLUE}🔗 API Endpoint: http://127.0.0.1:3000${NC}"

exit $TEST_EXIT_CODE