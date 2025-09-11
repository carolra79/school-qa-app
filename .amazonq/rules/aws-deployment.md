# AWS Deployment Restrictions

## Purpose
Prevent automatic AWS service deployment to allow manual learning and configuration.

## Deployment Rules

### No Automatic AWS Service Creation
- **DO NOT** create, deploy, or modify AWS resources automatically
- **DO NOT** use AWS CLI commands that create services (create-*, put-*, deploy, etc.)
- **DO NOT** suggest Infrastructure as Code (CloudFormation, CDK, Terraform) for deployment

### Manual Configuration Only
- User will manually create and configure all AWS resources in the console
- Provide guidance on what resources are needed, not how to create them automatically
- Focus on explaining AWS service configurations and relationships

### Allowed AWS Operations
- **READ operations only**: describe-*, list-*, get-*, head-*
- **Data operations**: uploading files to existing S3 buckets, querying existing services
- **Configuration retrieval**: reading from existing resources

### Documentation Requirements
- Document required AWS services and their purpose
- List necessary IAM permissions without creating policies
- Explain resource relationships and dependencies
- Provide console navigation guidance when helpful
- **Document all AWS resources created**: Include resource names, IDs, configurations, and purpose in project documentation

## Examples

### ✅ Allowed
```bash
aws s3 ls s3://existing-bucket
aws bedrock-agent describe-knowledge-base --knowledge-base-id existing-id
```

### ❌ Not Allowed
```bash
aws s3 mb s3://new-bucket
aws bedrock-agent create-knowledge-base
aws cloudformation deploy
```
