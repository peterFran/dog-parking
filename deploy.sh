#!/bin/bash

# Deploy Dog Care App Infrastructure
# Usage: ./deploy.sh [environment] [stack-name]

set -e

# Configuration
ENVIRONMENT=${1:-dev}
STACK_NAME=${2:-dog-care-app}
REGION="us-east-1"
CAPABILITIES="CAPABILITY_IAM"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🐕 Deploying Dog Care App Infrastructure${NC}"
echo "Environment: $ENVIRONMENT"
echo "Stack Name: $STACK_NAME"
echo "Region: $REGION"
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if SAM CLI is installed
if ! command -v sam &> /dev/null; then
    echo -e "${RED}❌ SAM CLI is not installed. Please install it first.${NC}"
    echo "Install with: brew install aws-sam-cli"
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ AWS credentials not configured. Please run 'aws configure' first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites check passed${NC}"
echo ""

# Build the SAM application
echo -e "${YELLOW}🏗️  Building SAM application...${NC}"
sam build

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Build failed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Build completed${NC}"
echo ""

# Deploy the application
echo -e "${YELLOW}🚀 Deploying to AWS...${NC}"
sam deploy \
    --stack-name "$STACK_NAME-$ENVIRONMENT" \
    --region "$REGION" \
    --capabilities "$CAPABILITIES" \
    --parameter-overrides "Environment=$ENVIRONMENT" \
    --resolve-s3 \
    --confirm-changeset

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Deployment failed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Deployment completed successfully${NC}"
echo ""

# Get the API Gateway URL
echo -e "${YELLOW}📋 Getting deployment information...${NC}"
API_URL=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME-$ENVIRONMENT" \
    --region "$REGION" \
    --query 'Stacks[0].Outputs[?OutputKey==`DogCareApiUrl`].OutputValue' \
    --output text)

if [ -n "$API_URL" ]; then
    echo -e "${GREEN}🌐 API Gateway URL: $API_URL${NC}"
else
    echo -e "${YELLOW}⚠️  Could not retrieve API Gateway URL${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Deployment Summary:${NC}"
echo "Environment: $ENVIRONMENT"
echo "Stack Name: $STACK_NAME-$ENVIRONMENT"
echo "Region: $REGION"
echo "API URL: $API_URL"
echo ""
echo -e "${GREEN}📖 Next steps:${NC}"
echo "1. Test the API endpoints using the URL above"
echo "2. Check CloudWatch logs for any issues"
echo "3. Set up monitoring and alarms"
echo "4. Configure custom domain (optional)"
echo ""
echo -e "${GREEN}🔧 Useful commands:${NC}"
echo "- View logs: sam logs -n DogManagementFunction --stack-name $STACK_NAME-$ENVIRONMENT"
echo "- Delete stack: sam delete --stack-name $STACK_NAME-$ENVIRONMENT"
echo "- Update stack: ./deploy.sh $ENVIRONMENT $STACK_NAME"