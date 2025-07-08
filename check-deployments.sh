#!/bin/bash

echo "🔍 Dog Care App - Deployment Status Check"
echo "========================================"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Please install it first."
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured. Please run 'aws configure'"
    exit 1
fi

echo "✅ AWS CLI configured"
echo ""

# Function to check stack status
check_stack() {
    local stack_name=$1
    local env_name=$2
    
    echo "🔍 Checking $env_name environment ($stack_name)..."
    
    # Check if stack exists
    if aws cloudformation describe-stacks --stack-name "$stack_name" --region us-east-1 &> /dev/null; then
        # Get stack status
        status=$(aws cloudformation describe-stacks \
            --stack-name "$stack_name" \
            --query 'Stacks[0].StackStatus' \
            --output text \
            --region us-east-1)
        
        # Get API URL
        api_url=$(aws cloudformation describe-stacks \
            --stack-name "$stack_name" \
            --query 'Stacks[0].Outputs[?OutputKey==`DogCareApiUrl`].OutputValue' \
            --output text \
            --region us-east-1)
        
        # Get creation time
        created=$(aws cloudformation describe-stacks \
            --stack-name "$stack_name" \
            --query 'Stacks[0].CreationTime' \
            --output text \
            --region us-east-1)
        
        # Get last updated time
        updated=$(aws cloudformation describe-stacks \
            --stack-name "$stack_name" \
            --query 'Stacks[0].LastUpdatedTime' \
            --output text \
            --region us-east-1)
        
        if [ "$status" = "CREATE_COMPLETE" ] || [ "$status" = "UPDATE_COMPLETE" ]; then
            echo "   ✅ Status: $status"
            echo "   🔗 API URL: $api_url"
            echo "   📅 Created: $created"
            if [ "$updated" != "None" ]; then
                echo "   🔄 Updated: $updated"
            fi
            
            # Test API health
            echo "   🧪 Testing API health..."
            response=$(curl -s -o /dev/null -w "%{http_code}" -X GET "$api_url/health" --max-time 10)
            if [ "$response" = "200" ]; then
                echo "   ✅ API health check: OK"
            else
                echo "   ⚠️  API health check: Failed (HTTP $response)"
            fi
        else
            echo "   ⚠️  Status: $status"
            echo "   🔗 API URL: $api_url"
        fi
    else
        echo "   ❌ Stack not found - environment not deployed"
    fi
    echo ""
}

# Check all environments
check_stack "dog-care-dev" "Development"
check_stack "dog-care-staging" "Staging"
check_stack "dog-care-prod" "Production"

# Check for recent CloudFormation events
echo "📋 Recent CloudFormation Events (last 5):"
echo "----------------------------------------"
for stack in "dog-care-dev" "dog-care-staging" "dog-care-prod"; do
    if aws cloudformation describe-stacks --stack-name "$stack" --region us-east-1 &> /dev/null; then
        echo "Stack: $stack"
        aws cloudformation describe-stack-events \
            --stack-name "$stack" \
            --region us-east-1 \
            --query 'StackEvents[0:5].[Timestamp,LogicalResourceId,ResourceStatus,ResourceStatusReason]' \
            --output table
        echo ""
    fi
done

# Summary
echo "📊 Summary:"
echo "----------"
echo "🏠 Local Development: http://localhost:3000 (if running)"
echo "🔧 Development: $(aws cloudformation describe-stacks --stack-name dog-care-dev --region us-east-1 --query 'Stacks[0].Outputs[?OutputKey==`DogCareApiUrl`].OutputValue' --output text 2>/dev/null || echo 'Not deployed')"
echo "🚀 Staging: $(aws cloudformation describe-stacks --stack-name dog-care-staging --region us-east-1 --query 'Stacks[0].Outputs[?OutputKey==`DogCareApiUrl`].OutputValue' --output text 2>/dev/null || echo 'Not deployed')"
echo "🌟 Production: $(aws cloudformation describe-stacks --stack-name dog-care-prod --region us-east-1 --query 'Stacks[0].Outputs[?OutputKey==`DogCareApiUrl`].OutputValue' --output text 2>/dev/null || echo 'Not deployed')"

echo ""
echo "🎯 Quick Commands:"
echo "  Local: ./start-local.sh"
echo "  Dev Deploy: sam deploy --config-env dev"
echo "  Staging Deploy: sam deploy --config-env staging"
echo "  Check Logs: aws logs tail /aws/lambda/dog-care-dev-DogManagementFunction --follow"
echo ""
echo "✅ Check complete!"