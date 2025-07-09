# IAM Policy Update for Venue Management

The venue management feature requires additional IAM permissions. Please update the GitHub Actions user policy with the following additions:

## Required Updates

### 1. DynamoDB Table Access
Add venues table to DynamoDB permissions:
```json
"arn:aws:dynamodb:*:*:table/venues-*"
```

### 2. Lambda Function Access
Add venue management Lambda function:
```json
"arn:aws:lambda:*:*:function:venue-management-*"
```

### 3. CloudWatch Logs Access
Add venue management log group:
```json
"arn:aws:logs:*:*:log-group:/aws/lambda/venue-management-*"
```

### 4. IAM Role Access
Add venue management role pattern:
```json
"arn:aws:iam::*:role/*VenueManagement*"
```

## Complete Updated Policy

The complete updated policy is available in `corrected-iam-policy.json`.

## To Apply the Update

1. Go to AWS IAM Console
2. Find the `github-actions-dog-parking` user
3. Update the attached policy with the new permissions
4. Retry the failed deployment

## Error Being Fixed

```
User: arn:aws:iam::946358504058:user/github-actions-dog-parking is not authorized to perform: logs:DeleteLogGroup on resource: arn:aws:logs:us-east-1:946358504058:log-group:/aws/lambda/venue-management-staging
```

This error occurs because the venue management log group was added but permissions weren't updated to include it.