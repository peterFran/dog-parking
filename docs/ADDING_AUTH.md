# Adding Authentication to Dog Care App

## Current State
- **No authentication** - all endpoints are public
- Owner ID is passed as a parameter/body field
- Perfect for MVP development

## Authentication Options

### Option 1: AWS Cognito (Recommended)
```yaml
# Add to template.yaml
DogCareUserPool:
  Type: AWS::Cognito::UserPool
  Properties:
    UserPoolName: DogCareUsers
    Policies:
      PasswordPolicy:
        MinimumLength: 8
        RequireNumbers: true

DogCareApiAuthorizer:
  Type: AWS::ApiGateway::Authorizer
  Properties:
    Type: COGNITO_USER_POOLS
    ProviderARNs:
      - !GetAtt DogCareUserPool.Arn
```

**Changes needed:**
1. Add Cognito authorizer to API Gateway
2. Modify Lambda functions to extract user ID from JWT token
3. Update frontend to handle login/signup

### Option 2: Custom JWT with Lambda Authorizer
```python
# Custom authorizer function
def lambda_handler(event, context):
    token = event['authorizationToken']
    # Validate JWT token
    # Return IAM policy
```

### Option 3: API Key Authentication (Simple)
```yaml
# Add to template.yaml
ApiKey:
  Type: AWS::ApiGateway::ApiKey
  Properties:
    Enabled: true
```

## Implementation Plan

### Phase 1: Add Auth Layer
1. **Choose auth method** (Cognito recommended)
2. **Add auth to template.yaml**
3. **Update API Gateway** to require authentication
4. **Keep current endpoints** as admin/internal APIs

### Phase 2: Update Lambda Functions
1. **Extract user context** from auth token
2. **Replace owner_id parameter** with authenticated user ID
3. **Add user ownership validation**

### Phase 3: Frontend Integration
1. **Add login/signup flows**
2. **Store and send auth tokens**
3. **Handle token refresh**

## Example: Owner ID from Auth Token
```python
# Before (current)
def lambda_handler(event, context):
    body = json.loads(event['body'])
    owner_id = body['owner_id']  # User-provided

# After (with auth)
def lambda_handler(event, context):
    # Extract from JWT token
    claims = event['requestContext']['authorizer']['claims']
    owner_id = claims['sub']  # From authenticated user
```

## Migration Strategy
1. **Keep current APIs** for testing/admin
2. **Add new authenticated endpoints** (e.g., `/v2/dogs`)
3. **Gradually migrate** frontend to use authenticated APIs
4. **Remove public APIs** when ready

## Security Benefits
- **User isolation** - users only see their data
- **Audit trails** - know who did what
- **Rate limiting** per user
- **Secure password management**