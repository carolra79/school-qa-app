# Full Implementation Deployment Plan

## Phase 1: Deploy Fallback Improvements ✅

### Step 1.1: Commit Current Changes
```bash
git add fallback_links.json
git add requirements.txt
git add .gitignore
git commit -m "feat(fallback): enhance fallback links with governors support

- Add governors/chair fallback links pointing to strategy page
- Add uncertainty keywords: unfortunately, do not seem to mention, does not provide
- Update gitignore to exclude test files  
- Add streamlit to requirements.txt

Improves user experience when AI cannot find specific information"

git push origin main
```

### Step 1.2: Test Fallback System
After deployment, test:
- "who is chair of the governors" → Should get strategy page link
- "events in september" → Should get calendar page link

## Phase 2: Implement Document Processor 🚀

### Step 2.1: AWS Configuration Changes

#### A. Create S3 Folder Structure
```bash
# Create processed-docs folder in S3 bucket
aws s3api put-object --bucket school-qa-docs-v2 --key processed-docs/
```

#### B. Update Knowledge Base Data Source
1. Go to AWS Bedrock Console
2. Navigate to Knowledge Bases → school-qa-knowledge-base
3. Click on Data Sources → school-qa-docs-v2
4. Edit the data source
5. Change S3 URI from: `s3://school-qa-docs-v2/school-docs/`
6. To: `s3://school-qa-docs-v2/processed-docs/`
7. Save changes

### Step 2.2: Update Lambda Function

#### A. Replace Lambda Code
1. Go to AWS Lambda Console
2. Find your current Lambda function (the one triggered by S3)
3. Replace the code with contents of `lambda_document_processor.py`
4. Update timeout to 5 minutes (for Textract processing)

#### B. Add Environment Variables
```
SOURCE_BUCKET=school-qa-docs-v2
SOURCE_PREFIX=school-docs/
PROCESSED_PREFIX=processed-docs/
KNOWLEDGE_BASE_ID=D5MRCKWCTD
DATA_SOURCE_ID=T4PVH55UXI
SYNC_DELAY_SECONDS=60
```

#### C. Update IAM Permissions
Add these permissions to your Lambda execution role:
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
        }
    ]
}
```

### Step 2.3: Test the Pipeline

#### A. Upload Test Document
1. Upload a PDF to `s3://school-qa-docs-v2/school-docs/`
2. Monitor Lambda logs for processing
3. Check `s3://school-qa-docs-v2/processed-docs/` for output
4. Wait for knowledge base sync to complete

#### B. Test Queries
Try these queries in your Streamlit app:
- "Year 6 curriculum meeting september"
- "curriculum meetings september 2025"
- "september events"

### Step 2.4: Migration Strategy

#### A. Process Existing Documents
For existing PDFs that need better indexing:
1. Re-upload them to trigger processing
2. Or manually run the processor on existing files

#### B. Monitor Results
- Check Lambda CloudWatch logs
- Monitor knowledge base ingestion jobs
- Test query accuracy improvements

## Phase 3: Commit Document Processor 📝

### Step 3.1: Add to Repository
```bash
git add lambda_document_processor.py
git add DOCUMENT_PROCESSOR_SETUP.md
git add DEPLOYMENT_PLAN.md
git commit -m "feat(processor): add automatic PDF-to-text document processor

- Add Lambda function for PDF text extraction using Textract
- Implement calendar-specific text cleaning and formatting
- Add automatic knowledge base sync after processing
- Include comprehensive setup and deployment documentation

Resolves PDF chunking issues by converting to clean text format"

git push origin main
```

## Success Criteria ✅

### Phase 1 Success:
- [ ] Fallback links work for uncertain responses
- [ ] Users get helpful links when AI can't find information
- [ ] No breaking changes to existing functionality

### Phase 2 Success:
- [ ] PDFs automatically convert to clean text
- [ ] September events queries return accurate results
- [ ] Calendar information is properly formatted and searchable
- [ ] No manual intervention needed for new uploads

### Rollback Plan 🔄

If issues occur in Phase 2:
1. Change KB data source back to `school-docs/`
2. Restore original Lambda function
3. System reverts to Phase 1 functionality

## Timeline Estimate ⏰

- **Phase 1**: 30 minutes (commit + deploy + test)
- **Phase 2**: 2-3 hours (AWS config + Lambda update + testing)
- **Phase 3**: 15 minutes (commit documentation)

**Total**: ~3-4 hours for complete implementation