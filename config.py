# Configuration for the Document Q&A System
import os

# Users who can upload documents
AUTHORIZED_UPLOADERS = [
    "admin",
    # Add more usernames here
]

# Simple user credentials (in production, use proper authentication)
USER_CREDENTIALS = {
    "admin": "admin123",
    "student1": "password123",
    "student2": "password123",
    # Add more users here
}

# AWS Bedrock settings - use environment variables in production
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
KNOWLEDGE_BASE_ID = os.getenv("KNOWLEDGE_BASE_ID", "D5MRCKWCTD")
DATA_SOURCE_ID = os.getenv("DATA_SOURCE_ID", "T4PVH55UXI")
S3_BUCKET = os.getenv("S3_BUCKET", "school-qa-docs-v2")
S3_PREFIX = "school-docs/"

# Application settings
SEARCH_RESULTS_LIMIT = 5
