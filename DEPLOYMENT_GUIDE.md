# St Mary's School Q&A Bot - Complete Deployment Guide

## Overview
AI-powered Q&A system for St Mary's School using AWS Bedrock Knowledge Base. Allows parents and students to ask questions about school documents with admin capabilities for document management.

## Current Architecture (ECS Fargate)
- **Frontend:** Streamlit web interface
- **Compute:** ECS Fargate (serverless containers)
- **AI/ML:** AWS Bedrock Knowledge Base with retrieval-augmented generation
- **CDN:** CloudFront distribution for global access
- **Security:** Multiple security groups with proper network isolation
- **Storage:** S3 bucket for document storage
- **Build Pipeline:** CodeBuild for automated Docker builds

## AWS Resources Created

### Core Infrastructure
- **ECS Cluster:** `school-qa-cluster`
- **ECS Service:** `school-qa-service`
- **Task Definition:** `school-qa-task:5` (current revision)
- **Launch Type:** AWS Fargate (serverless)
- **CPU/Memory:** 0.25 vCPU / 0.5 GB (free tier)
- **Desired Tasks:** 1

### Container & Build Pipeline
- **ECR Repository:** `school-qa-agent`
- **Docker Image:** `185749752590.dkr.ecr.us-east-1.amazonaws.com/school-qa-agent:latest`
- **CodeBuild Project:** `school-qa-streamlit-app`
- **Architecture:** ARM64
- **Build Spec:** `buildspec.yaml` (supports both ECS and EC2 deployments)

### Networking & Security
- **VPC:** `vpc-4f652935` (default VPC)
- **Subnets:** All default subnets across availability zones
- **Application Load Balancer:** `school-qa-alb2-1354046734.us-east-1.elb.amazonaws.com`
- **CloudFront Distribution:** `https://d3agi2buko5b65.cloudfront.net/`
- **Security Group:** `sg-040d5bf56839194b3` (ECS-ALB-security-group)

### Security Group Configuration
**Inbound Rules:**
- **Port 8501:** TCP, Source: Multiple CloudFront security groups
- **Port 8501:** TCP, Source: Personal IPs (work/home)
- **Port 22:** SSH access from home IP

**Outbound Rules:**
- **Port 443:** HTTPS to 0.0.0.0/0 (required for ECR access)
- **Port 8501:** TCP to CloudFront security groups

### IAM Roles & Permissions
- **Task Execution Role:** `ecsTaskExecutionRole`
  - Policies: `AmazonECSTaskExecutionRolePolicy`, `AmazonBedrockFullAccess`, `AmazonS3FullAccess`
  - Purpose: ECS operations + Bedrock API access + S3 access
- **Service-Linked Role:** `AWSServiceRoleForECS`
  - Purpose: ECS cluster management

### AI/ML Services (Bedrock)
- **Knowledge Base ID:** `D5MRCKWCTD`
- **Data Source ID:** `T4PVH55UXI`
- **S3 Bucket:** `school-qa-docs-v2`
- **S3 Folder:** `school-docs/` (for document uploads)
- **Region:** `us-east-1`

## Environment Variables
The ECS task uses these environment variables:
```
AWS_REGION=us-east-1
KNOWLEDGE_BASE_ID=D5MRCKWCTD
DATA_SOURCE_ID=T4PVH55UXI
S3_BUCKET=school-qa-docs-v2
```

## Application Features
- **Public Q&A Interface:** Students/parents can ask questions
- **Admin Panel:** Password-protected document upload (sidebar)
- **Document Processing:** Automatic knowledge base sync after uploads
- **AI Responses:** Powered by AWS Bedrock with retrieval-augmented generation
- **Suggested Questions:** Pre-defined common questions for easy access

## Access Information
- **Production URL:** https://d3agi2buko5b65.cloudfront.net/
- **ALB URL:** http://school-qa-alb2-1354046734.us-east-1.elb.amazonaws.com
- **Admin Access:** Via sidebar login in the web interface
- **Admin Credentials:** username: `admin`, password: `admin123`
- **Port:** 8501 (Streamlit default)
- **Protocol:** HTTPS via CloudFront, HTTP via ALB

## Deployment Flow

### CodeBuild Configuration
The `buildspec.yaml` supports both ECS and EC2 deployments:

**For ECS Deployment:**
- Set environment variable: `DEPLOYMENT_TYPE=ECS`
- Optional: `ECS_CLUSTER_NAME=school-qa-cluster`
- Optional: `ECS_SERVICE_NAME=school-qa-service`

**For EC2 Deployment:**
- Leave `DEPLOYMENT_TYPE` blank or set to `EC2`

### Build Process
1. **Code** → GitHub repository: `https://github.com/carolra79/school-qa-app.git`
2. **Build** → CodeBuild creates Docker image and pushes to ECR
3. **Deploy** → ECS automatically updates service (if `DEPLOYMENT_TYPE=ECS`)
4. **Access** → Users connect via CloudFront or ALB

### Manual ECS Service Update
If needed, manually update the ECS service:
```bash
aws ecs update-service --cluster school-qa-cluster --service school-qa-service --force-new-deployment --region us-east-1
```

## File Structure
```
school-qa/
├── app_agentcore.py          # Main Streamlit application
├── config.py                 # Environment variables configuration
├── bedrock_config.json       # Bedrock model configuration
├── buildspec.yaml           # CodeBuild specification
├── Dockerfile               # Container configuration
├── requirements.txt         # Python dependencies
├── st-marys-logo.png       # School logo
├── README.md               # Basic project info
└── .gitignore              # Git ignore rules
```

## Key Technical Decisions
- **ECS Fargate over EC2:** Serverless, no server management
- **ALB + CloudFront:** Proper load balancing with CDN
- **WebSocket Support:** Streamlit WebSockets work through ALB
- **ARM64 Architecture:** Cost-effective and performant
- **Single IAM Role:** Simplified permissions management
- **Default VPC:** Simplified networking setup

## Troubleshooting

### Common Issues
1. **Tasks Stuck in Pending:** Check security group outbound rules for HTTPS (port 443)
2. **ECR Pull Errors:** Ensure task execution role has ECR permissions
3. **Network Timeout:** Verify subnets have internet access
4. **WebSocket Issues:** Ensure ALB allows WebSocket upgrade headers

### Debug Commands
```bash
# Check ECS service status
aws ecs describe-services --cluster school-qa-cluster --services school-qa-service --region us-east-1

# Check task logs
aws logs describe-log-groups --log-group-name-prefix "/ecs/school-qa" --region us-east-1

# Test ECR access
aws ecr describe-repositories --repository-names school-qa-agent --region us-east-1
```

### Container Logs
Access logs through:
1. ECS Console → Clusters → school-qa-cluster → Services → school-qa-service → Tasks → [Task ID] → Logs
2. CloudWatch Logs → `/ecs/school-qa-task`

## Maintenance

### Updates
1. Push code changes to GitHub
2. Trigger CodeBuild with `DEPLOYMENT_TYPE=ECS`
3. ECS automatically deploys new version
4. Verify deployment via CloudFront URL

### Scaling
- **Horizontal:** Increase desired task count in ECS service
- **Vertical:** Update task definition with more CPU/memory
- **Cost:** Stay within free tier limits (1 task recommended)

### Monitoring
- **CloudWatch Logs:** ECS task logs
- **CloudWatch Metrics:** ECS service metrics
- **Health Checks:** ALB health checks on port 8501
- **Access Logs:** CloudFront access logs (if enabled)

## Security Notes
- **No direct internet exposure:** All access via CloudFront/ALB
- **Corporate compliant:** No 0.0.0.0/0 inbound rules on port 8501
- **HTTPS encryption:** Via CloudFront
- **IAM least privilege:** Task role has only required permissions
- **Network isolation:** Private subnets with controlled access

## Cost Optimization
- **Fargate Spot:** Consider for non-production workloads
- **CloudWatch log retention:** Set to 7-30 days
- **Monitor Bedrock usage:** Track API calls and costs
- **Stop/Start:** Scale to 0 tasks when not needed

## Backup & Recovery
- **Source code:** GitHub repository
- **Documents:** S3 bucket (school-qa-docs-v2)
- **Configuration:** This deployment guide
- **Infrastructure:** Recreatable via AWS Console or IaC

---
**Deployment Date:** 2025-09-15  
**Last Updated:** 2025-09-15  
**Version:** 2.0 (ECS Fargate)  
**Status:** Production Ready ✅  
**Access:** https://d3agi2buko5b65.cloudfront.net/
