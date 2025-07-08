#!/bin/bash

# Fix corrupted SAM managed stack
echo "🔧 Fixing corrupted SAM managed stack..."

# Check if the stack exists and its status
echo "📊 Checking stack status..."
aws cloudformation describe-stacks \
    --stack-name aws-sam-cli-managed-default \
    --region us-east-1 \
    --query 'Stacks[0].{Status:StackStatus,Reason:StackStatusReason}' \
    --output table || echo "Stack might not exist or is inaccessible"

# Delete the corrupted stack
echo "🗑️  Deleting corrupted SAM managed stack..."
aws cloudformation delete-stack \
    --stack-name aws-sam-cli-managed-default \
    --region us-east-1

echo "⏳ Waiting for stack deletion to complete..."
aws cloudformation wait stack-delete-complete \
    --stack-name aws-sam-cli-managed-default \
    --region us-east-1

echo "✅ Stack deleted successfully! You can now retry the deployment."