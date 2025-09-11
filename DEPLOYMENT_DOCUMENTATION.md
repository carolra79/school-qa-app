# St Marys Year5 Class Rep Bot - Complete Deployment Documentation

## Overview
You've created a fully functional AI-powered Q&A system for St Marys School using AWS services. The system allows students and parents to ask questions about school documents, with admin capabilities for document management.

## Architecture Components

### 1. Application Code
**Location:** `/mnt/c/Users/rayfielc/school-qa/`
- **Main App:** `app_agentcore.py` - Streamlit web interface
- **Configuration:** `config.py` - Environment variables and settings
- **Dependencies:** `requirements.txt` - Python packages
- **Docker:** `Dockerfile` - Container configuration

### 2. AWS Infrastructure

#### Container Registry (ECR)
- **Repository:** `school-qa-agent`
- **Region:** `us-east-1`
- **Image URI:** `185749752590.dkr.ecr.us-east-1.amazonaws.com/school-qa-agent:latest`
- **Architecture:** ARM64 (built with `amazonlinux-aarch64-standard:3.0`)

#### Build Pipeline (CodeBuild)
- **Project:** `school-qa-streamlit-app`
- **Build Spec:** Automated Docker build and ECR push
- **Trigger:** Manual builds via console
- **Output:** Docker image pushed to ECR

#### Container Orchestration (ECS)
- **Cluster:** `school-qa-app-cluster`
- **Service:** `school-qa-app`
- **Task Definition:** `school-qa-task:4` (final working revision)
- **Launch Type:** AWS Fargate (serverless)
- **CPU/Memory:** 0.25 vCPU / 0.5 GB (free tier)
- **Desired Tasks:** 1

#### Networking
- **VPC:** `vpc-4f652935` (default VPC)
- **Subnets:** All default subnets across availability zones
- **Security Group:** `sg-89173ed8` (default, modified)
- **Public IP:** `54.158.200.147` (current)
- **Port:** 8501 (Streamlit default)

#### Security Group Rules
**Inbound Rules:**
- **Port 8501:** TCP, Source: 0.0.0.0/0 (internet access)
- **All Traffic:** Source: sg-89173ed8 (internal communication)

#### IAM Roles
- **Task Execution Role:** `ecsTaskExecutionRole`
  - Policies: `AmazonECSTaskExecutionRolePolicy`, `AmazonBedrockFullAccess`
  - Purpose: ECS operations + Bedrock API access
- **Task Role:** `ecsTaskExecutionRole` (same role used for both)
  - Purpose: Application AWS API calls
- **Service-Linked Role:** `AWSServiceRoleForECS`
  - Purpose: ECS cluster management

#### AI/ML Services (Bedrock)
- **Knowledge Base ID:** `D5MRCKWCTD`
- **Data Source ID:** `T4PVH55UXI`
- **S3 Bucket:** `school-qa-docs-v2`
- **Region:** `us-east-1`

### 3. Environment Variables
The application uses these environment variables:
```
AWS_REGION=us-east-1
KNOWLEDGE_BASE_ID=D5MRCKWCTD
DATA_SOURCE_ID=T4PVH55UXI
S3_BUCKET=school-qa-docs-v2
```

### 4. Application Features
- **Public Q&A Interface:** Students/parents can ask questions
- **Admin Panel:** Password-protected document upload (sidebar)
- **Document Processing:** Automatic knowledge base sync after uploads
- **AI Responses:** Powered by AWS Bedrock with retrieval-augmented generation

### 5. Access Information
- **Public URL:** http://54.158.200.147:8501
- **Admin Access:** Via sidebar login in the web interface
- **Port:** 8501 (Streamlit default)
- **Protocol:** HTTP (WebSocket support for Streamlit)

### 6. Key Technical Decisions
- **ECS Fargate over App Runner:** WebSocket support required for Streamlit
- **ARM64 Architecture:** Matches CodeBuild environment
- **Single IAM Role:** `ecsTaskExecutionRole` serves both task execution and application needs
- **Default VPC:** Simplified networking setup
- **Public IP Assignment:** Required for internet access

### 7. Deployment Flow
1. **Code** → Local development in `/mnt/c/Users/rayfielc/school-qa/`
2. **Build** → CodeBuild creates Docker image
3. **Store** → Image pushed to ECR repository
4. **Deploy** → ECS Fargate runs container with public access
5. **Access** → Users connect via public IP on port 8501

### 8. Troubleshooting Notes
- **Architecture Mismatch:** Ensure ARM64 consistency between CodeBuild and ECS
- **Credentials Issues:** Task role must have Bedrock permissions
- **Network Access:** Security group must allow port 8501 from 0.0.0.0/0
- **WebSocket Support:** ECS Fargate supports WebSockets, App Runner does not

### 9. Maintenance
- **Updates:** Rebuild Docker image via CodeBuild, update ECS service
- **Monitoring:** CloudWatch logs available for debugging
- **Scaling:** Increase desired tasks if needed (stay within free tier)
- **Security:** Regular review of IAM permissions and security group rules

This architecture provides a scalable, serverless solution for the school's Q&A needs while staying within AWS free tier limits.
