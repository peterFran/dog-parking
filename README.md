# Dog Care App - AWS Lambda Infrastructure

A serverless dog care application built on AWS Lambda, API Gateway, and DynamoDB.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client App    │────│   API Gateway   │────│   Lambda        │
│   (Web/Mobile)  │    │   (REST API)    │    │   Functions     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
                                              ┌─────────────────┐
                                              │   DynamoDB      │
                                              │   Tables        │
                                              └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

1. **AWS Account** with appropriate permissions
2. **AWS CLI** installed and configured
3. **SAM CLI** installed
4. **Python 3.11** (for local development)
5. **Docker** (for local testing)

### Installation

```bash
# Clone or navigate to project directory
cd /Users/petermeckiffe/Documents/workspace/dogparking

# Install AWS CLI (if not already installed)
brew install awscli

# Install SAM CLI
brew install aws-sam-cli

# Configure AWS credentials
aws configure

# Deploy the infrastructure
./deploy.sh dev dog-care-app
```

### What Gets Deployed

- **4 Lambda Functions**: Dog, Owner, Booking, and Payment management
- **4 DynamoDB Tables**: Dogs, Owners, Bookings, and Payments
- **1 API Gateway**: REST API with CORS enabled
- **CloudWatch Log Groups**: For monitoring and debugging

## 📋 API Documentation

### Dogs API

#### Create Dog
```bash
POST /dogs
{
  "name": "Buddy",
  "breed": "Golden Retriever",
  "age": 3,
  "size": "large",
  "owner_id": "owner-123",
  "vaccination_status": "up-to-date",
  "special_needs": ["medication"],
  "emergency_contact": "+1234567890"
}
```

#### Get Dog
```bash
GET /dogs/{id}
```

#### List Dogs
```bash
GET /dogs?owner_id=owner-123
```

#### Update Dog
```bash
PUT /dogs/{id}
{
  "name": "Updated Name",
  "age": 4
}
```

#### Delete Dog
```bash
DELETE /dogs/{id}
```

### Owners API

#### Register Owner
```bash
POST /owners/register
{
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+1234567890",
  "address": {
    "street": "123 Main St",
    "city": "Anytown",
    "state": "CA",
    "zip": "12345"
  }
}
```

#### Get Owner Profile
```bash
GET /owners/profile?owner_id=owner-123
```

#### Update Owner Profile
```bash
PUT /owners/profile?owner_id=owner-123
{
  "name": "Updated Name",
  "phone": "+1234567890"
}
```

### Bookings API

#### Create Booking
```bash
POST /bookings
{
  "dog_id": "dog-123",
  "owner_id": "owner-123",
  "service_type": "daycare",
  "start_time": "2024-01-01T09:00:00Z",
  "end_time": "2024-01-01T17:00:00Z",
  "special_instructions": "Feed at 12pm"
}
```

#### List Bookings
```bash
GET /bookings?owner_id=owner-123
```

#### Get Booking
```bash
GET /bookings/{id}
```

#### Update Booking
```bash
PUT /bookings/{id}
{
  "status": "confirmed",
  "special_instructions": "Updated instructions"
}
```

#### Cancel Booking
```bash
DELETE /bookings/{id}
```

### Payments API

#### Process Payment
```bash
POST /payments
{
  "booking_id": "booking-123",
  "amount": 45.00,
  "payment_method": "credit_card",
  "payment_token": "test_success"
}
```

#### Get Payment
```bash
GET /payments/{id}
```

#### List Payments
```bash
GET /payments?booking_id=booking-123
```

## 🧪 Testing

### Local Testing with SAM

```bash
# Start API locally
sam local start-api

# Test specific function
sam local invoke DogManagementFunction --event events/create-dog.json

# Generate test events
sam local generate-event apigateway aws-proxy --body '{"name":"Test Dog"}' --path /dogs --method POST
```

### API Testing Examples

```bash
# Replace YOUR_API_URL with your actual API Gateway URL
API_URL="https://your-api-id.execute-api.us-east-1.amazonaws.com/dev"

# Register a new owner
curl -X POST $API_URL/owners/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+1234567890"
  }'

# Create a dog
curl -X POST $API_URL/dogs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Buddy",
    "breed": "Golden Retriever",
    "age": 3,
    "size": "large",
    "owner_id": "owner-your-id-here"
  }'

# Create a booking
curl -X POST $API_URL/bookings \
  -H "Content-Type: application/json" \
  -d '{
    "dog_id": "dog-your-id-here",
    "owner_id": "owner-your-id-here",
    "service_type": "daycare",
    "start_time": "2024-01-01T09:00:00Z",
    "end_time": "2024-01-01T17:00:00Z"
  }'
```

## 📊 Monitoring

### CloudWatch Dashboards

```bash
# View function logs
sam logs -n DogManagementFunction --stack-name dog-care-app-dev

# View all logs
sam logs --stack-name dog-care-app-dev
```

### Key Metrics to Monitor

- **Error Rate**: < 0.1%
- **Duration**: < 5 seconds
- **Cold Starts**: < 5%
- **Concurrent Executions**: Monitor for throttling
- **DynamoDB Throttles**: Should be 0

## 💰 Cost Optimization

### Expected Monthly Costs (Development)

- **Lambda**: $5-15 (1M requests)
- **API Gateway**: $10-20 (1M requests)
- **DynamoDB**: $5-10 (on-demand)
- **CloudWatch**: $2-5 (logs/metrics)
- **Total**: ~$25-50/month

### Cost Optimization Tips

1. **Use appropriate Lambda memory**: Start with 512MB
2. **Enable DynamoDB auto-scaling**: For production
3. **Set up cost alerts**: $50, $100 thresholds
4. **Clean up test data**: Regularly
5. **Use reserved capacity**: For predictable workloads

## 🔧 Development Workflow

### Local Development

```bash
# Install dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/

# Format code
black functions/
flake8 functions/

# Type checking
mypy functions/
```

### Deployment

```bash
# Deploy to development
./deploy.sh dev

# Deploy to staging
./deploy.sh staging

# Deploy to production
./deploy.sh prod
```

## 🔐 Security

### Authentication & Authorization

Currently using basic owner-based data isolation. For production, consider:

1. **JWT tokens** for API authentication
2. **API Gateway authorizers**
3. **Fine-grained IAM roles**
4. **Rate limiting**
5. **Input validation**

### Security Best Practices

- Store sensitive data in AWS Secrets Manager
- Use environment variables for configuration
- Enable API Gateway logging
- Implement proper error handling
- Use HTTPS only

## 🚨 Troubleshooting

### Common Issues

1. **Deployment fails**: Check AWS credentials and permissions
2. **API returns 502**: Check Lambda function logs
3. **DynamoDB errors**: Verify table names and indexes
4. **CORS issues**: Ensure proper headers are set
5. **Cold starts**: Consider provisioned concurrency

### Debug Commands

```bash
# View CloudFormation stack
aws cloudformation describe-stacks --stack-name dog-care-app-dev

# View function configuration
aws lambda get-function --function-name dog-management-dev

# View API Gateway
aws apigateway get-rest-apis

# View DynamoDB tables
aws dynamodb list-tables
```

## 📚 Next Steps

### Phase 1: MVP Completion (Week 1-2)
- [ ] Complete API testing
- [ ] Add input validation
- [ ] Set up basic monitoring
- [ ] Create simple frontend

### Phase 2: Enhanced Features (Week 3-4)
- [ ] Add authentication (Cognito)
- [ ] Implement real payment processing
- [ ] Add email notifications
- [ ] Create admin dashboard

### Phase 3: Production Ready (Week 5-6)
- [ ] Set up CI/CD pipeline
- [ ] Add comprehensive testing
- [ ] Implement caching
- [ ] Add performance monitoring

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes
4. Add tests
5. Submit pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review CloudWatch logs
3. Open an issue in the repository
4. Contact the development team

---

**Happy coding! 🐕**