#!/bin/bash

echo "🐕 Starting Dog Care App Locally"
echo "================================"

# Check if SAM is installed
if ! command -v sam &> /dev/null; then
    echo "❌ AWS SAM CLI not found. Install it first:"
    echo "   brew install aws-sam-cli"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi

echo "✅ Prerequisites check passed"
echo ""

# Set environment variables for local development
export AWS_DEFAULT_REGION=us-east-1
export AWS_ACCESS_KEY_ID=dummy
export AWS_SECRET_ACCESS_KEY=dummy

echo "🚀 Starting SAM Local API..."
echo "API Gateway will be available at: http://localhost:3000"
echo "DynamoDB Local will be available at: http://localhost:8000"
echo ""
echo "Available endpoints:"
echo "  POST   /owners/register"
echo "  GET    /owners/profile?owner_id=xxx"
echo "  PUT    /owners/profile?owner_id=xxx"
echo "  POST   /dogs"
echo "  GET    /dogs?owner_id=xxx"
echo "  POST   /bookings"
echo "  GET    /bookings?owner_id=xxx"
echo "  POST   /payments"
echo "  GET    /payments/xxx"
echo ""
echo "Press Ctrl+C to stop the services"
echo ""

# Start SAM local with DynamoDB and environment variables
sam local start-api \
  --docker-network sam-local \
  --parameter-overrides Environment=local \
  --env-vars env-vars.json