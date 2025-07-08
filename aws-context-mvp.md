# AWS Lambda MVP Implementation Checklist

**Goal: Get a working API with Lambda functions and datastore running in 3-5 days**

## Day 1: Basic Setup

### AWS Account Preparation

- [ ] Create AWS account or use existing with admin access
- [ ] Install AWS CLI v2 and configure with access keys
- [ ] Install AWS SAM CLI for local development
- [ ] Set up basic billing alerts ($10, $50, $100 thresholds)
- [ ] Choose a single region (us-east-1 recommended for beginners)

### Development Environment

- [ ] Install Docker Desktop for local Lambda testing
- [ ] Set up code editor with AWS Toolkit extension
- [ ] Create project directory structure:
  ```
  my-api/
  ├── functions/
  ├── template.yaml (SAM template)
  └── README.md
  ```

## Day 2: Database Setup

### DynamoDB Table Creation

- [ ] Create DynamoDB table via AWS Console:
  - Table name: `MyAppData`
  - Partition key: `id` (String)
  - Use on-demand billing mode
  - Keep all other defaults
- [ ] Note the table ARN for IAM permissions
- [ ] Test table with a few manual records in AWS Console

### Basic IAM Role

- [ ] Create Lambda execution role with these policies:
  - `AWSLambdaBasicExecutionRole` (for CloudWatch logs)
  - Custom policy for DynamoDB access:
    ```json
    {
      "Version": "2012-10-17",
      "Statement": [
        {
          "Effect": "Allow",
          "Action": [
            "dynamodb:GetItem",
            "dynamodb:PutItem",
            "dynamodb:UpdateItem",
            "dynamodb:DeleteItem",
            "dynamodb:Scan",
            "dynamodb:Query"
          ],
          "Resource": "arn:aws:dynamodb:REGION:ACCOUNT:table/MyAppData"
        }
      ]
    }
    ```

## Day 3: Lambda Functions

### Core CRUD Functions

- [ ] Create `get-item` Lambda function:
  - Runtime: Python 3.11 or Node.js 18.x
  - Memory: 256MB
  - Timeout: 30 seconds
  - Implement GET operation for single item
- [ ] Create `create-item` Lambda function:
  - Implement POST operation with input validation
  - Return created item with generated ID
- [ ] Create `list-items` Lambda function:
  - Implement GET operation for multiple items
  - Add basic pagination if needed
- [ ] Test each function individually in AWS Console

### Function Code Template (Python)

```python
import json
import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('MyAppData')

def lambda_handler(event, context):
    try:
        # Your logic here
        result = {"message": "success"}

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(result)
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e)})
        }
```

## Day 4: API Gateway Setup

### REST API Creation

- [ ] Create new REST API in AWS Console
- [ ] Create resource: `/items`
- [ ] Create sub-resource: `/items/{id}`
- [ ] Set up methods:
  - `GET /items` → `list-items` Lambda
  - `POST /items` → `create-item` Lambda
  - `GET /items/{id}` → `get-item` Lambda

### Method Configuration

- [ ] For each method, configure:
  - Integration type: Lambda Function
  - Enable Lambda Proxy integration
  - Set appropriate Lambda function
  - Enable CORS if building frontend
- [ ] Deploy API to "dev" stage
- [ ] Note the API Gateway URL for testing

### Basic Testing

- [ ] Test each endpoint using curl or Postman:

  ```bash
  # Create item
  curl -X POST https://YOUR-API-ID.execute-api.REGION.amazonaws.com/dev/items \
    -H "Content-Type: application/json" \
    -d '{"name": "Test Item", "description": "My first item"}'

  # Get all items
  curl https://YOUR-API-ID.execute-api.REGION.amazonaws.com/dev/items

  # Get specific item
  curl https://YOUR-API-ID.execute-api.REGION.amazonaws.com/dev/items/ITEM-ID
  ```

## Day 5: Polish and Documentation

### Error Handling Improvements

- [ ] Add input validation to all Lambda functions
- [ ] Implement proper HTTP status codes (400, 404, 500)
- [ ] Add structured logging with print statements
- [ ] Test error scenarios (invalid input, missing items)

### Basic Monitoring

- [ ] Check CloudWatch Logs for each Lambda function
- [ ] Set up basic CloudWatch alarms:
  - Error rate > 5%
  - Duration > 10 seconds
- [ ] Test API Gateway access logs (enable if needed)

### Documentation

- [ ] Create README with:
  - API endpoint URLs
  - Request/response examples
  - How to deploy changes
  - Basic troubleshooting steps
- [ ] Document environment variables and configuration
- [ ] Add cost estimates for current usage

## Optional Day 6: Basic Improvements

### Performance Optimization

- [ ] Increase Lambda memory to 512MB if functions are slow
- [ ] Add connection reuse for DynamoDB client
- [ ] Implement basic caching for read operations

### Security Hardening

- [ ] Remove hardcoded values, use environment variables
- [ ] Add API key requirement to API Gateway (optional)
- [ ] Review IAM permissions and remove unnecessary access

### Development Workflow

- [ ] Set up SAM template for infrastructure as code:

  ```yaml
  AWSTemplateFormatVersion: "2010-09-09"
  Transform: AWS::Serverless-2016-10-31

  Resources:
    MyApiFunction:
      Type: AWS::Serverless::Function
      Properties:
        CodeUri: functions/
        Handler: app.lambda_handler
        Runtime: python3.11
        Events:
          Api:
            Type: Api
            Properties:
              Path: /items
              Method: get
  ```

- [ ] Test local development with `sam local start-api`
- [ ] Deploy using `sam deploy --guided`

## Success Criteria for MVP

### Functional Requirements

- [ ] Can create new items via POST request
- [ ] Can retrieve single item by ID via GET request
- [ ] Can list all items via GET request
- [ ] API returns proper JSON responses
- [ ] Basic error handling for common scenarios

### Technical Requirements

- [ ] All Lambda functions execute under 5 seconds
- [ ] API Gateway responds within 2 seconds for typical requests
- [ ] DynamoDB operations complete successfully
- [ ] CloudWatch logs show no critical errors
- [ ] Total AWS cost under $5 for development testing

### Deliverables

- [ ] Working API with documented endpoints
- [ ] 3 Lambda functions handling core CRUD operations
- [ ] DynamoDB table storing application data
- [ ] Basic monitoring and logging in place
- [ ] README with setup and usage instructions

## Next Steps After MVP

Once your MVP is working, consider these improvements:

1. **Add UPDATE and DELETE operations** to complete CRUD
2. **Implement proper authentication** (Cognito or API keys)
3. **Add input validation** and request/response schemas
4. **Set up CI/CD pipeline** for automated deployments
5. **Add comprehensive error handling** and retry logic
6. **Implement caching** for better performance
7. **Add integration tests** for reliability
8. **Monitor costs** and optimize resource allocation

## Common Gotchas to Avoid

- [ ] Remember to enable CORS if building a web frontend
- [ ] Use environment variables for table names and region settings
- [ ] Don't forget to deploy API Gateway after making changes
- [ ] Check IAM permissions if getting access denied errors
- [ ] Use proper JSON parsing in Lambda functions
- [ ] Handle DynamoDB exceptions gracefully
- [ ] Set appropriate Lambda timeouts (30s is usually enough for simple operations)
