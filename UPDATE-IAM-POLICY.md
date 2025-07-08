# Update IAM Policy for GitHub Actions

The deployment is failing due to insufficient IAM permissions. Follow these steps to update the IAM policy:

## Step 1: Update IAM Policy in AWS Console

1. Go to AWS Console → IAM → Users
2. Find your `github-actions-dog-parking` user
3. Click on the user, then go to "Permissions" tab
4. Remove the existing custom policy
5. Click "Add permissions" → "Attach policies directly"
6. Click "Create policy"
7. Choose "JSON" tab
8. Copy and paste the content from `github-actions-iam-policy.json`
9. Click "Next: Tags" → "Next: Review"
10. Name the policy: `GitHubActions-DogParking-FullAccess`
11. Click "Create policy"
12. Go back to your user and attach this new policy

## Step 2: Alternative - Attach AWS Managed Policies (Easier but less secure)

If you prefer a quicker solution, you can attach these AWS managed policies instead:

1. `PowerUserAccess` - Provides full access except IAM user/group management
2. `IAMReadOnlyAccess` - Allows reading IAM roles (needed for Lambda execution roles)

**Note:** This gives broader permissions than needed but will definitely work.

## Step 3: Test the Deployment

After updating the policy, trigger a new deployment by pushing a commit or manually running the GitHub Actions workflow.

## Common Missing Permissions

The most common issues are:
- **S3 bucket creation** - SAM needs to create buckets for packaging
- **IAM role creation** - Lambda functions need execution roles
- **CloudFormation** - SAM uses CloudFormation for deployment
- **API Gateway** - Creating and managing API endpoints

## Security Best Practice

The provided policy follows the principle of least privilege while still allowing SAM deployments. It's more secure than using `PowerUserAccess` but more permissive than the original minimal policy.