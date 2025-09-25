# Document Processor Setup Guide

This guide shows how to implement the automatic PDF-to-text conversion pipeline.

## Architecture Overview

```
📄 Upload to s3://bucket/school-docs/
    ↓
🤖 Lambda: Convert PDF to clean text (Textract)
    ↓
💾 Save to s3://bucket/processed-docs/
    ↓
🔍 Knowledge Base indexes clean text only
    ↓
✅ Perfect search results
```

## Setup Steps

### 1. Update S3 Bucket Structure

Create the new folder structure:
```
s3://school-qa-docs-v2/
├── school-docs/          ← Original uploads (triggers processing)
├── processed-docs/       ← Clean text versions (indexed by KB)
└── config/              ← Configuration files (existing)
```

### 2. Update Knowledge Base Data Source

**IMPORTANT**: Change your Bedrock Knowledge Base data source to point to `processed-docs/` instead of `school-docs/`

1. Go to AWS Bedrock Console
2. Find your Knowledge Base: `school-qa-knowledge-base`
3. Edit the Data Source configuration
4. Change S3 path from `s3://school-qa-docs-v2/school-docs/` to `s3://school-qa-docs-v2/processed-docs/`
5. Save changes

### 3. Replace Lambda Function

Replace your current Lambda function code with `lambda_document_processor.py`

**Environment Variables Needed:**
```
SOURCE_BUCKET=school-qa-docs-v2
SOURCE_PREFIX=school-docs/
PROCESSED_PREFIX=processed-docs/
KNOWLEDGE_BASE_ID=D5MRCKWCTD
DATA_SOURCE_ID=T4PVH55UXI
SYNC_DELAY_SECONDS=60
```

**IAM Permissions Needed:**
Your Lambda execution role needs these additional permissions:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "textract:DetectDocumentText"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject"
            ],
            "Resource": [
                "arn:aws:s3:::school-qa-docs-v2/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "bedrock-agent:StartIngestionJob"
            ],
            "Resource": "*"
        }
    ]
}
```

### 4. Test the Pipeline

1. **Upload a PDF** to `s3://school-qa-docs-v2/school-docs/`
2. **Check Lambda logs** - should show PDF processing
3. **Check processed-docs folder** - should contain `filename_processed.txt`
4. **Wait for KB sync** - should complete automatically
5. **Test queries** in your Streamlit app

## How It Works

### PDF Processing Flow:
1. **S3 Event** triggers Lambda when file uploaded to `school-docs/`
2. **Textract** extracts text from PDF
3. **Text Cleaning** formats calendar events properly:
   - Fixes OCR issues ("8 th" → "8th")
   - Converts times ("15:30" → "3:30pm") 
   - Expands locations ("SH" → "School Hall")
   - Adds month/year to events
4. **Save to processed-docs/** as clean text file
5. **Trigger KB sync** to index the clean text
6. **Perfect chunking** results in accurate search

### File Type Handling:
- **PDFs**: Processed with Textract + cleaning
- **Word docs**: Pass through to Bedrock (usually work fine)
- **Text files**: Light cleaning only
- **Other formats**: Ignored

### Calendar-Specific Cleaning:
The processor detects calendar documents and applies special formatting:
```
Input:  "Monday 8 th Year 6 Curriculum meeting for parents, 15:30 – 16:00 SH"
Output: "Monday 8th September 2025: Year 6 Curriculum meeting for parents, 3:30pm - 4:00pm, School Hall"
```

## Benefits

✅ **Consistent Results** - No more PDF parsing surprises  
✅ **Better Chunking** - Clean text chunks predictably  
✅ **Debugging** - See exactly what gets indexed  
✅ **Quality Control** - Fix issues before indexing  
✅ **Automatic** - No manual intervention needed  

## Rollback Plan

If issues occur, you can quickly rollback:
1. Change KB data source back to `school-docs/`
2. Restore original Lambda function
3. System works as before

## Monitoring

Check these to monitor the system:
- **Lambda logs** - Processing success/failures
- **S3 processed-docs folder** - Generated text files
- **Bedrock ingestion jobs** - Indexing status
- **Streamlit app** - Query accuracy

## Future Enhancements

- Add support for more file types
- Implement document versioning
- Add quality scoring for processed text
- Create admin dashboard for monitoring