# School QA Bot - Complete Deployment Manual

## Overview
AI-powered Q&A system for St Mary's School using AWS Bedrock Knowledge Base. Allows parents and students to ask questions about school documents with admin capabilities for document management.

## Architecture
- **Frontend:** Streamlit web interface
- **Compute:** EC2 t4g.micro (ARM64) with Docker
- **AI/ML:** AWS Bedrock Knowledge Base with retrieval-augmented generation
- **CDN:** CloudFront distribution for global access
- **Security:** 5 security groups with CloudFront IP ranges only
- **Storage:** S3 bucket for document storage
- **Automation:** Lambda function for CloudFront IP management

## AWS Resources Created

### Core Infrastructure
- **EC2 Instance:** `school-qa-server` (t4g.micro ARM64)
- **Instance ID:** i-[generated]
- **Public IP:** [varies on restart]
- **Key Pair:** `speech-formatter-key` (reused)
- **IAM Role:** `speech-formatter-ec2-role` (reused)

### Container & Build
- **ECR Repository:** `school-qa-agent`
- **Docker Image:** `185749752590.dkr.ecr.us-east-1.amazonaws.com/school-qa-agent:latest`
- **CodeBuild Project:** `school-qa-streamlit-app`
- **Architecture:** ARM64 (matches t4g.micro)

### CDN & Security
- **CloudFront Distribution:** `school-qa-cdn`
- **Domain:** `d225g5pz7lxh61.cloudfront.net`
- **Security Groups:** 5 groups (1 main + 4 CloudFront IP ranges)
- **Lambda Function:** `update-cloudfront-security-group` (shared)

### AI/ML Services
- **Knowledge Base ID:** `D5MRCKWCTD`
- **Data Source ID:** `T4PVH55UXI`
- **S3 Bucket:** `school-qa-docs-v2`
- **Region:** `us-east-1`

## Deployment Steps

### 1. Prerequisites
- AWS account with appropriate permissions
- Access to existing infrastructure (security groups, Lambda, IAM roles)
- School QA source code in ECR repository

### 2. Launch EC2 Instance
```bash
# Instance Configuration
Name: school-qa-server
AMI: Amazon Linux 2023
Instance Type: t4g.micro (ARM64 - important!)
Key Pair: speech-formatter-key
IAM Role: speech-formatter-ec2-role

# Security Groups (attach all 5):
- sg-094f72ff744348adb (main)
- sg-017a35d536b81ec98 (cloudfront-sg-4)
- sg-08dc714bd18f1584f (cloudfront-sg-3)
- sg-0dac64e3b0af792ab (cloudfront-sg-2)
- sg-0eb4d951a3f1bfbe4 (cloudfront-sg-5)
```

### 3. User Data Script (Optional)
```bash
#!/bin/bash
yum update -y
yum install -y docker
service docker start
usermod -a -G docker ec2-user

# Install AWS CLI for ARM64
curl "https://awscli.amazonaws.com/awscli-exe-linux-aarch64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
./aws/install

# Configure ECR login
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 185749752590.dkr.ecr.us-east-1.amazonaws.com
```

### 4. Manual Setup (if no User Data)
```bash
# SSH into instance
ssh -i "path/to/speech-formatter-key.pem" ec2-user@[PUBLIC-IP]

# Install Docker
sudo yum update -y
sudo yum install -y docker
sudo service docker start
sudo usermod -a -G docker ec2-user

# Log out and back in
exit
ssh -i "path/to/speech-formatter-key.pem" ec2-user@[PUBLIC-IP]

# Authenticate with ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 185749752590.dkr.ecr.us-east-1.amazonaws.com

# Pull and run container
docker pull 185749752590.dkr.ecr.us-east-1.amazonaws.com/school-qa-agent:latest

docker run -d -p 8501:8501 --name school-qa-bot \
  -e AWS_REGION=us-east-1 \
  -e KNOWLEDGE_BASE_ID=D5MRCKWCTD \
  -e DATA_SOURCE_ID=T4PVH55UXI \
  -e S3_BUCKET=school-qa-docs-v2 \
  185749752590.dkr.ecr.us-east-1.amazonaws.com/school-qa-agent:latest
```

### 5. Create CloudFront Distribution
```bash
# CloudFront Configuration
Origin Domain: ec2-[PUBLIC-IP].compute-1.amazonaws.com
Protocol: HTTP only
Port: 8501
Cache Policy: CachingDisabled
Origin Request Policy: CORS-S3Origin
Viewer Protocol Policy: Redirect HTTP to HTTPS
Allowed HTTP Methods: GET, HEAD, OPTIONS, PUT, POST, PATCH, DELETE
```

### 6. Security Configuration
- **Remove any 0.0.0.0/0 rules** from security groups
- **Only allow CloudFront IP ranges** (managed by Lambda function)
- **Optional:** Keep personal IP for admin access

## Environment Variables
```bash
AWS_REGION=us-east-1
KNOWLEDGE_BASE_ID=D5MRCKWCTD
DATA_SOURCE_ID=T4PVH55UXI
S3_BUCKET=school-qa-docs-v2
```

## Access URLs
- **Production (Global):** https://d225g5pz7lxh61.cloudfront.net
- **Direct (Admin only):** http://[PUBLIC-IP]:8501 (if personal IP rule exists)

## Application Features
- **Public Q&A Interface:** Students/parents ask questions about school documents
- **Admin Panel:** Password-protected document upload (sidebar)
- **Document Processing:** Automatic knowledge base sync after uploads
- **AI Responses:** Powered by AWS Bedrock with retrieval-augmented generation

## Maintenance

### Starting/Stopping
```bash
# Stop instance to save costs
aws ec2 stop-instances --instance-ids i-[INSTANCE-ID]

# Start instance when needed
aws ec2 start-instances --instance-ids i-[INSTANCE-ID]

# Container management
docker start school-qa-bot
docker stop school-qa-bot
docker restart school-qa-bot
```

### Updates
```bash
# Rebuild Docker image via CodeBuild
# Pull new image
docker pull 185749752590.dkr.ecr.us-east-1.amazonaws.com/school-qa-agent:latest

# Update container
docker stop school-qa-bot
docker rm school-qa-bot
docker run -d -p 8501:8501 --name school-qa-bot \
  -e AWS_REGION=us-east-1 \
  -e KNOWLEDGE_BASE_ID=D5MRCKWCTD \
  -e DATA_SOURCE_ID=T4PVH55UXI \
  -e S3_BUCKET=school-qa-docs-v2 \
  185749752590.dkr.ecr.us-east-1.amazonaws.com/school-qa-agent:latest
```

### Monitoring
- **CloudWatch Logs:** `/aws/codebuild/school-qa-streamlit-app`
- **Container Logs:** `docker logs school-qa-bot`
- **Health Check:** Access CloudFront URL

## Troubleshooting

### Common Issues
1. **Architecture Mismatch:** Ensure ARM64 consistency (t4g.micro + ARM64 Docker image)
2. **Access Denied:** Check IAM role has Bedrock permissions
3. **Network Timeout:** Verify security groups allow CloudFront IPs
4. **Container Won't Start:** Check environment variables and Docker logs

### Debug Commands
```bash
# Check container status
docker ps
docker logs school-qa-bot

# Check AWS permissions
aws bedrock list-knowledge-bases
aws s3 ls s3://school-qa-docs-v2

# Test network connectivity
curl -I http://localhost:8501
```

## Cost Optimization
- **Stop EC2 instance** when not in use (~$6.50/month savings)
- **CloudWatch log retention:** Set to 7-30 days
- **Monitor Bedrock usage** for cost control

## Security Notes
- **No 0.0.0.0/0 inbound rules** (corporate compliant)
- **CloudFront-only access** for external users
- **Automatic IP management** via Lambda function
- **Admin access** via personal IP (optional)
- **HTTPS encryption** via CloudFront

## Backup & Recovery
- **Source code:** Stored in ECR repository
- **Documents:** Stored in S3 bucket (school-qa-docs-v2)
- **Configuration:** Documented in this manual
- **Infrastructure:** Recreatable via this deployment guide

---
**Deployment Date:** 2025-09-09  
**Last Updated:** 2025-09-09  
**Version:** 1.0  
**Status:** Production Ready ✅
