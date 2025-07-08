#!/bin/bash

echo "🚀 Dog Care App - AWS Deployment Setup"
echo "======================================"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Please install it:"
    echo "   pip install awscli"
    echo "   OR brew install awscli"
    exit 1
fi

# Check if SAM CLI is installed
if ! command -v sam &> /dev/null; then
    echo "❌ AWS SAM CLI not found. Please install it:"
    echo "   pip install aws-sam-cli"
    echo "   OR brew install aws-sam-cli"
    exit 1
fi

echo "✅ AWS CLI and SAM CLI are installed"

# Check AWS credentials
echo ""
echo "🔐 Checking AWS credentials..."
if aws sts get-caller-identity &> /dev/null; then
    echo "✅ AWS credentials are configured"
    AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
    AWS_USER=$(aws sts get-caller-identity --query Arn --output text)
    echo "   Account: $AWS_ACCOUNT"
    echo "   User: $AWS_USER"
else
    echo "❌ AWS credentials not configured"
    echo "   Please run: aws configure"
    echo "   You'll need:"
    echo "   - AWS Access Key ID"
    echo "   - AWS Secret Access Key"
    echo "   - Default region (us-east-1)"
    exit 1
fi

# Validate SAM template
echo ""
echo "🔍 Validating SAM template..."
if sam validate --template template.yaml; then
    echo "✅ SAM template is valid"
else
    echo "❌ SAM template validation failed"
    exit 1
fi

# Test build
echo ""
echo "🔨 Testing SAM build..."
if sam build --template template.yaml; then
    echo "✅ SAM build successful"
else
    echo "❌ SAM build failed"
    exit 1
fi

# Ask user if they want to deploy to dev
echo ""
read -p "🚀 Do you want to deploy to dev environment now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 Deploying to dev environment..."
    
    if sam deploy --config-env dev --no-confirm-changeset; then
        echo "✅ Dev deployment successful!"
        
        # Get API URL
        API_URL=$(aws cloudformation describe-stacks \
          --stack-name dog-care-dev \
          --query 'Stacks[0].Outputs[?OutputKey==`DogCareApiUrl`].OutputValue' \
          --output text \
          --region us-east-1)
        
        echo ""
        echo "🎉 Your API is deployed at: $API_URL"
        echo ""
        
        # Test the API
        echo "🧪 Testing the deployed API..."
        response=$(curl -s -X POST "$API_URL/owners/register" \
          -H "Content-Type: application/json" \
          -d '{"name":"Test User","email":"test@example.com","phone":"+1234567890"}')
        
        if echo "$response" | grep -q '"id"'; then
            echo "✅ API test successful!"
            echo "Response: $response"
        else
            echo "❌ API test failed"
            echo "Response: $response"
        fi
    else
        echo "❌ Dev deployment failed"
        exit 1
    fi
else
    echo "⏭️  Skipping deployment"
fi

echo ""
echo "🎯 Next Steps:"
echo "1. Push your code to GitHub"
echo "2. Add AWS credentials to GitHub secrets:"
echo "   - AWS_ACCESS_KEY_ID"
echo "   - AWS_SECRET_ACCESS_KEY"
echo "3. Test the workflows:"
echo "   - Create a PR to test PR workflow"
echo "   - Merge to main to test staging deployment"
echo "   - Use 'Actions' tab to manually deploy to dev"
echo ""
echo "📚 For detailed instructions, see: docs/DEPLOYMENT_GUIDE.md"
echo ""
echo "✅ Setup complete! Happy coding! 🎉"