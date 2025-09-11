# School Q&A Bot

AI-powered document Q&A system using AWS Bedrock Knowledge Base.

## Features
- Public access for questions
- Admin-only document uploads
- AWS Bedrock Knowledge Base integration
- Streamlit web interface

## Deployment on AWS App Runner

### Environment Variables Required:
- `AWS_REGION`: us-east-1
- `KNOWLEDGE_BASE_ID`: D5MRCKWCTD
- `DATA_SOURCE_ID`: T4PVH55UXI
- `S3_BUCKET`: school-qa-docs-v2

### AWS Permissions Required:
- Bedrock access
- S3 access to your bucket
- App Runner service role

## Local Development
```bash
pip install -r requirements.txt
streamlit run app.py
```

# Pipeline Test - ECS Fargate Deployment
