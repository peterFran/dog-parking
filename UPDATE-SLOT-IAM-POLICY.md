# IAM Policy Update for Slot Management

The slot management feature requires additional IAM permissions. Please update the GitHub Actions user policy with the following additions:

## Required Updates

### 1. DynamoDB Table Access
Add slots table to DynamoDB permissions:
```json
"arn:aws:dynamodb:*:*:table/slots-*"
```

### 2. Lambda Function Access
Add slot management Lambda function:
```json
"arn:aws:lambda:*:*:function:slot-management-*"
```

### 3. CloudWatch Logs Access
Add slot management log group:
```json
"arn:aws:logs:*:*:log-group:/aws/lambda/slot-management-*"
```

### 4. IAM Role Access
Add slot management role pattern:
```json
"arn:aws:iam::*:role/*SlotManagement*"
```

## To Apply the Update

1. Go to AWS IAM Console: https://console.aws.amazon.com/iam/
2. Navigate to Users → `github-actions-dog-parking`
3. Click on the attached policy (likely named `github-actions-policy` or similar)
4. Click "Edit policy"
5. Add the following resources to the appropriate sections:

### DynamoDB Section (Statement with dynamodb:* actions):
```json
{
  "Effect": "Allow",
  "Action": [
    "dynamodb:CreateTable",
    "dynamodb:DeleteTable",
    "dynamodb:DescribeTable",
    "dynamodb:UpdateTable",
    "dynamodb:TagResource",
    "dynamodb:UntagResource"
  ],
  "Resource": [
    "arn:aws:dynamodb:*:*:table/dogs-*",
    "arn:aws:dynamodb:*:*:table/owners-*",
    "arn:aws:dynamodb:*:*:table/bookings-*",
    "arn:aws:dynamodb:*:*:table/venues-*",
    "arn:aws:dynamodb:*:*:table/slots-*"
  ]
}
```

### Lambda Section (Statement with lambda:* actions):
```json
{
  "Effect": "Allow",
  "Action": [
    "lambda:CreateFunction",
    "lambda:DeleteFunction",
    "lambda:GetFunction",
    "lambda:UpdateFunctionCode",
    "lambda:UpdateFunctionConfiguration",
    "lambda:ListTags",
    "lambda:TagResource",
    "lambda:UntagResource",
    "lambda:AddPermission",
    "lambda:RemovePermission"
  ],
  "Resource": [
    "arn:aws:lambda:*:*:function:dog-management-*",
    "arn:aws:lambda:*:*:function:owner-management-*",
    "arn:aws:lambda:*:*:function:booking-management-*",
    "arn:aws:lambda:*:*:function:venue-management-*",
    "arn:aws:lambda:*:*:function:slot-management-*"
  ]
}
```

### CloudWatch Logs Section (Statement with logs:* actions):
```json
{
  "Effect": "Allow",
  "Action": [
    "logs:CreateLogGroup",
    "logs:DeleteLogGroup",
    "logs:DescribeLogGroups",
    "logs:PutRetentionPolicy",
    "logs:TagLogGroup",
    "logs:UntagLogGroup"
  ],
  "Resource": [
    "arn:aws:logs:*:*:log-group:/aws/lambda/dog-management-*",
    "arn:aws:logs:*:*:log-group:/aws/lambda/owner-management-*",
    "arn:aws:logs:*:*:log-group:/aws/lambda/booking-management-*",
    "arn:aws:logs:*:*:log-group:/aws/lambda/venue-management-*",
    "arn:aws:logs:*:*:log-group:/aws/lambda/slot-management-*"
  ]
}
```

### IAM Role Section (Statement with iam:* actions):
```json
{
  "Effect": "Allow",
  "Action": [
    "iam:CreateRole",
    "iam:DeleteRole",
    "iam:GetRole",
    "iam:PutRolePolicy",
    "iam:DeleteRolePolicy",
    "iam:AttachRolePolicy",
    "iam:DetachRolePolicy",
    "iam:PassRole",
    "iam:TagRole",
    "iam:UntagRole"
  ],
  "Resource": [
    "arn:aws:iam::*:role/*DogManagement*",
    "arn:aws:iam::*:role/*OwnerManagement*",
    "arn:aws:iam::*:role/*BookingManagement*",
    "arn:aws:iam::*:role/*VenueManagement*",
    "arn:aws:iam::*:role/*SlotManagement*"
  ]
}
```

6. Click "Next" and "Save changes"

## Error Being Fixed

The current deployment is failing with:

```
DELETE_FAILED  AWS::Logs::LogGroup  SlotManagementLogGroup
User: arn:aws:iam::946358504058:user/github-actions-dog-parking is not authorized to perform:
logs:DeleteLogGroup on resource: arn:aws:logs:us-east-1:946358504058:log-group:/aws/lambda/slot-management-test-dog-care-test-18449277561
```

This error occurs because the slot management log group was added but permissions weren't updated to include it.

## After Updating Permissions

Once you've updated the IAM policy:

1. The stuck CloudFormation stack (`dog-care-test-18449277561`) is in ROLLBACK_FAILED state
2. You'll need to manually delete the log group that's blocking cleanup:
   ```bash
   aws logs delete-log-group --log-group-name /aws/lambda/slot-management-test-dog-care-test-18449277561 --region us-east-1
   ```

3. Then continue the rollback:
   ```bash
   aws cloudformation continue-update-rollback --stack-name dog-care-test-18449277561 --region us-east-1
   ```

4. Once the rollback completes, re-run the GitHub Actions workflow to deploy again with proper permissions.
