# School Q&A Bot - Requirements Document

## Overview
AI-powered document Q&A system for St Marys Year 5 class representatives using AWS Bedrock Knowledge Base with Streamlit web interface.

## User Stories

### Public Users (Parents/Students)
- As a parent, I want to ask questions about school information so I can get quick answers without searching through documents
- As a parent, I want to see suggested common questions so I can find information faster
- As a user, I want the interface to be simple and intuitive so I can use it without training

### Admin Users (Class Representatives)
- As an admin, I want to upload school documents so the bot can answer questions about them
- As an admin, I want to update bot prompts/instructions without redeploying the app so I can improve responses quickly
- As an admin, I want to see upload status and sync progress so I know when new documents are available
- As an admin, I want to clear chat history for privacy management

## Functional Requirements

### Core Q&A Functionality
- **FR-001**: System must accept natural language questions from users
- **FR-002**: System must search uploaded documents and provide relevant answers
- **FR-003**: System must display suggested common questions for user guidance
- **FR-004**: System must show question and answer in a clear, formatted display
- **FR-005**: System must handle cases where information is not available in documents

### Document Management
- **FR-006**: Admin users must authenticate before accessing upload features
- **FR-007**: System must accept PDF, TXT, and DOCX file uploads
- **FR-008**: System must store uploaded documents in S3 bucket
- **FR-009**: System must trigger knowledge base sync after document upload
- **FR-010**: System must provide upload status feedback to admin users

### Configuration Management
- **FR-011**: System must load Bedrock prompts and settings from S3 configuration
- **FR-012**: System must cache configuration to minimize S3 calls
- **FR-013**: System must fall back to local config if S3 config unavailable
- **FR-014**: Configuration changes must take effect without app redeployment

### User Interface
- **FR-015**: Public interface must not show admin features
- **FR-016**: Admin interface must show document management panel
- **FR-017**: System must display school branding (logo, colors)
- **FR-018**: Interface must be responsive for mobile and desktop use

## Technical Requirements

### AWS Integration
- **TR-001**: Must use AWS Bedrock Knowledge Base for document retrieval
- **TR-002**: Must use AWS S3 for document storage and configuration
- **TR-003**: Must use Claude 3 Sonnet model for answer generation
- **TR-004**: Must handle AWS service errors gracefully

### Performance
- **TR-005**: Configuration must be cached for 5 minutes to reduce S3 calls
- **TR-006**: Question processing must complete within 30 seconds
- **TR-007**: File uploads must support files up to 10MB
- **TR-008**: Application must minimize AWS service costs through efficient resource usage

### Security
- **TR-009**: Admin authentication required for document uploads
- **TR-010**: No sensitive data should be logged or exposed
- **TR-011**: S3 bucket access must use proper IAM permissions

### Deployment
- **TR-012**: Must support containerized deployment with Docker
- **TR-013**: Must use environment variables for AWS configuration
- **TR-014**: Must handle app restarts without data loss

## Environment Variables Required
- `AWS_REGION`: us-east-1
- `KNOWLEDGE_BASE_ID`: D5MRCKWCTD
- `DATA_SOURCE_ID`: T4PVH55UXI
- `S3_BUCKET`: school-qa-docs-v2

## Configuration Structure (S3)
```json
{
  "system_instructions": "Bot behavior and response guidelines",
  "model_arn": "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0",
  "temperature": 0.1,
  "max_tokens": 1000
}
```

## Success Criteria
- Parents can get answers to school questions in under 30 seconds
- Admins can upload documents and update bot behavior without developer intervention
- System maintains 99% uptime during school hours
- Configuration changes take effect within 5 minutes
- Interface works on mobile devices used by parents

## Out of Scope
- Multi-school support
- Advanced user roles beyond admin/public
- Document version control
- Analytics and usage reporting
- Integration with school management systems
