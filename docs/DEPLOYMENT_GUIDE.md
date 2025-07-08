# 🚀 Deployment Guide

## Overview

This guide explains how to set up CI/CD pipelines for deploying the Dog Care App to AWS using GitHub Actions.

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Development   │    │     Staging     │    │   Production    │
│                 │    │                 │    │                 │
│ Manual Deploy   │    │ Auto on merge   │    │ Manual Deploy   │
│                 │    │ to main branch  │    │ (Coming soon)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🔧 Prerequisites

### 1. AWS Account Setup
- AWS account with appropriate permissions
- AWS CLI configured locally (for manual deployments)
- AWS SAM CLI installed

### 2. GitHub Repository Setup
- Repository with the Dog Care App code
- GitHub Actions enabled
- Repository secrets configured

## 🔐 GitHub Secrets Configuration

Add these secrets to your GitHub repository:

### Required Secrets

1. **AWS_ACCESS_KEY_ID**
   - AWS Access Key ID for deployment
   - Should have permissions to create/manage Lambda, API Gateway, DynamoDB, CloudFormation, IAM

2. **AWS_SECRET_ACCESS_KEY**
   - AWS Secret Access Key (corresponding to above)

3. **GITHUB_TOKEN** (automatic)
   - Automatically provided by GitHub Actions
   - Used for creating releases and commenting on PRs

### Setting Up GitHub Secrets

1. Go to your repository on GitHub
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add each secret with the exact names above

## 🌍 Environment Configuration

### Development Environment
- **Stack Name**: `dog-care-dev`
- **Trigger**: Manual via GitHub Actions
- **Purpose**: Testing new features and bug fixes

### Staging Environment
- **Stack Name**: `dog-care-staging`
- **Trigger**: Automatic on merge to `main` branch
- **Purpose**: Pre-production testing and validation

### Production Environment
- **Stack Name**: `dog-care-prod`
- **Trigger**: Manual (coming soon)
- **Purpose**: Live production environment

## 🚀 Deployment Workflows

### 1. Development Deployment (Manual)

**Trigger**: Manual via GitHub Actions UI

```bash
# Or deploy manually from local machine:
sam build
sam deploy --config-env dev
```

**What it does**:
- Validates SAM template
- Builds application
- Deploys to dev environment
- Runs smoke tests
- Comments on PR if applicable

### 2. Staging Deployment (Automatic)

**Trigger**: Push to `main` branch or merged PR

**What it does**:
- Runs full test suite
- Validates SAM template
- Builds application
- Deploys to staging environment
- Runs integration tests
- Creates GitHub release
- Sends notifications

### 3. Pull Request Testing

**Trigger**: PR opened/updated against `main` or `develop`

**What it does**:
- Runs linting (Black, Flake8)
- Runs unit tests with coverage
- Validates SAM template
- Builds application
- Comments test results on PR

## 📋 Manual Deployment Steps

### Prerequisites
```bash
# Install dependencies
pip install aws-sam-cli aws-cli

# Configure AWS credentials
aws configure
```

### Development Deployment
```bash
# Build and deploy to dev
sam build
sam deploy --config-env dev

# Or use the guided deployment
sam deploy --guided
```

### Staging Deployment
```bash
# Deploy to staging
sam build
sam deploy --config-env staging
```

### Local Testing
```bash
# Start local development environment
./setup-local-db.sh
./start-local.sh

# Test locally
./test-api.sh http://localhost:3000
```

## 🧪 Testing Strategy

### Unit Tests
- Run on every PR
- Coverage requirement: 50%+
- Fast feedback loop

### Integration Tests
- Run on staging deployment
- Tests complete API workflows
- Validates end-to-end functionality

### Smoke Tests
- Run on dev deployment
- Quick validation of core functionality
- Rapid feedback for development

## 🔍 Monitoring and Logs

### CloudWatch Logs
- Lambda function logs: `/aws/lambda/dog-care-{env}-{function}`
- API Gateway logs: Available in CloudWatch

### CloudFormation Stacks
- Dev: `dog-care-dev`
- Staging: `dog-care-staging`
- Prod: `dog-care-prod`

### API Endpoints
After deployment, your API will be available at:
```
https://{api-id}.execute-api.us-east-1.amazonaws.com/{env}/
```

## 🚨 Troubleshooting

### Common Issues

1. **AWS Credentials Error**
   ```
   Error: Unable to locate credentials
   ```
   **Solution**: Check GitHub secrets are set correctly

2. **Stack Already Exists**
   ```
   Error: Stack already exists
   ```
   **Solution**: Stack names must be unique per region

3. **Permission Denied**
   ```
   Error: User is not authorized to perform...
   ```
   **Solution**: Ensure AWS user has required permissions

4. **Test Failures**
   ```
   Error: Test coverage below threshold
   ```
   **Solution**: Add more tests or fix failing tests

### Debugging Steps

1. Check GitHub Actions logs
2. Check CloudFormation events in AWS Console
3. Check CloudWatch logs for Lambda functions
4. Validate SAM template locally: `sam validate`

## 📊 Cost Optimization

### AWS Resources Created
- **Lambda Functions**: 4 functions (pay per invocation)
- **API Gateway**: REST API (pay per request)
- **DynamoDB**: 4 tables (on-demand pricing)
- **CloudWatch**: Logs and metrics (pay per GB)

### Cost Estimates
- **Development**: < $5/month (light usage)
- **Staging**: < $10/month (testing usage)
- **Production**: Depends on traffic

## 🔒 Security Best Practices

### IAM Permissions
- Use least privilege principle
- Create dedicated deployment user
- Regularly rotate access keys

### Environment Variables
- No secrets in code
- Use AWS Systems Manager for sensitive config
- Environment-specific configurations

### API Security
- CORS properly configured
- Rate limiting (future enhancement)
- Authentication (future enhancement)

## 📝 Next Steps

1. **Set up GitHub secrets** (AWS credentials)
2. **Push code to GitHub** repository
3. **Test PR workflow** by creating a test PR
4. **Test dev deployment** by manually triggering
5. **Test staging deployment** by merging to main
6. **Monitor deployments** in AWS Console

## 🎯 Success Criteria

✅ **Development Environment**
- Manual deployment works
- API endpoints respond correctly
- Smoke tests pass

✅ **Staging Environment**
- Automatic deployment on merge
- Integration tests pass
- GitHub releases created

✅ **Pull Request Testing**
- Tests run on every PR
- Coverage requirements met
- Build validation passes

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review GitHub Actions logs
3. Check AWS CloudFormation events
4. Verify AWS credentials and permissions