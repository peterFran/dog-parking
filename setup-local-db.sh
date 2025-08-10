#!/bin/bash

echo "🗄️  Setting up Local DynamoDB"
echo "============================="

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi

# Start DynamoDB Local container
echo "🚀 Starting DynamoDB Local container..."
docker run -d \
    --name dynamodb-local \
    --network sam-local \
    -p 8000:8000 \
    amazon/dynamodb-local:latest \
    -jar DynamoDBLocal.jar \
    -sharedDb \
    -inMemory

# Wait for DynamoDB to start
echo "⏳ Waiting for DynamoDB Local to start..."
sleep 5

# Create tables
echo "📋 Creating tables..."

aws dynamodb create-table \
    --table-name dogs-local \
    --attribute-definitions \
        AttributeName=id,AttributeType=S \
        AttributeName=owner_id,AttributeType=S \
    --key-schema \
        AttributeName=id,KeyType=HASH \
    --global-secondary-indexes \
        'IndexName=owner-index,KeySchema=[{AttributeName=owner_id,KeyType=HASH}],Projection={ProjectionType=ALL}' \
    --billing-mode PAY_PER_REQUEST \
    --endpoint-url http://localhost:8000 \
    --region us-east-1

aws dynamodb create-table \
    --table-name owners-local \
    --attribute-definitions \
        AttributeName=user_id,AttributeType=S \
    --key-schema \
        AttributeName=user_id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --endpoint-url http://localhost:8000 \
    --region us-east-1

aws dynamodb create-table \
    --table-name bookings-local \
    --attribute-definitions \
        AttributeName=id,AttributeType=S \
        AttributeName=owner_id,AttributeType=S \
        AttributeName=start_time,AttributeType=S \
    --key-schema \
        AttributeName=id,KeyType=HASH \
    --global-secondary-indexes \
        'IndexName=owner-time-index,KeySchema=[{AttributeName=owner_id,KeyType=HASH},{AttributeName=start_time,KeyType=RANGE}],Projection={ProjectionType=ALL}' \
    --billing-mode PAY_PER_REQUEST \
    --endpoint-url http://localhost:8000 \
    --region us-east-1

aws dynamodb create-table \
    --table-name payments-local \
    --attribute-definitions \
        AttributeName=id,AttributeType=S \
        AttributeName=booking_id,AttributeType=S \
    --key-schema \
        AttributeName=id,KeyType=HASH \
    --global-secondary-indexes \
        'IndexName=booking-index,KeySchema=[{AttributeName=booking_id,KeyType=HASH}],Projection={ProjectionType=ALL}' \
    --billing-mode PAY_PER_REQUEST \
    --endpoint-url http://localhost:8000 \
    --region us-east-1

echo "✅ Local DynamoDB setup complete!"
echo "📊 DynamoDB Admin UI: http://localhost:8000/shell"
echo ""
echo "To stop DynamoDB Local:"
echo "  docker stop dynamodb-local"
echo "  docker rm dynamodb-local"