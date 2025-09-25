import boto3
import json
import time
import os
import re
from datetime import datetime

def lambda_handler(event, context):
    """
    Process uploaded documents: convert to clean text, then trigger knowledge base sync
    """
    
    # Configuration
    source_bucket = os.environ.get('SOURCE_BUCKET', 'school-qa-docs-v2')
    source_prefix = os.environ.get('SOURCE_PREFIX', 'school-docs/')
    processed_prefix = os.environ.get('PROCESSED_PREFIX', 'processed-docs/')
    knowledge_base_id = os.environ.get('KNOWLEDGE_BASE_ID', 'D5MRCKWCTD')
    data_source_id = os.environ.get('DATA_SOURCE_ID', 'T4PVH55UXI')
    delay_seconds = int(os.environ.get('SYNC_DELAY_SECONDS', '60'))
    
    s3_client = boto3.client('s3')
    bedrock_agent = boto3.client('bedrock-agent')
    
    try:
        print(f"Received event: {json.dumps(event)}")
        
        processed_files = []
        
        # Process each S3 event record
        for record in event.get('Records', []):
            bucket = record['s3']['bucket']['name']
            key = record['s3']['object']['key']
            
            print(f"Processing file: {key}")
            
            # Skip if already processed or not in source folder
            if key.startswith(processed_prefix):
                print(f"Skipping already processed file: {key}")
                continue
                
            if not key.startswith(source_prefix):
                print(f"Skipping file outside source folder: {key}")
                continue
            
            # Skip folder entries
            if key.endswith('/'):
                print(f"Skipping folder: {key}")
                continue
            
            # Process the file based on type
            processed_text = process_document(s3_client, bucket, key)
            
            if processed_text:
                # Save processed text
                processed_key = save_processed_text(
                    s3_client, bucket, key, processed_text, processed_prefix
                )
                processed_files.append(processed_key)
                print(f"✅ Processed and saved: {processed_key}")
            else:
                print(f"⚠️ Could not process file: {key}")
        
        # If we processed any files, trigger knowledge base sync
        if processed_files:
            if delay_seconds > 0:
                print(f"Waiting {delay_seconds} seconds before triggering sync...")
                time.sleep(delay_seconds)
            
            trigger_knowledge_base_sync(bedrock_agent, knowledge_base_id, data_source_id)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'Documents processed and sync triggered',
                    'processed_files': processed_files
                })
            }
        else:
            return {
                'statusCode': 200,
                'body': json.dumps('No files processed')
            }
        
    except Exception as e:
        print(f"Error processing documents: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        }

def process_document(s3_client, bucket, key):
    """Process a document based on its file type"""
    
    file_ext = key.lower().split('.')[-1]
    
    try:
        if file_ext == 'pdf':
            return process_pdf(s3_client, bucket, key)
        elif file_ext in ['docx', 'doc']:
            return process_word_doc(s3_client, bucket, key)
        elif file_ext == 'txt':
            return process_text_file(s3_client, bucket, key)
        else:
            print(f"Unsupported file type: {file_ext}")
            return None
            
    except Exception as e:
        print(f"Error processing {key}: {e}")
        return None

def process_pdf(s3_client, bucket, key):
    """Convert PDF to clean text using Amazon Textract"""
    try:
        textract = boto3.client('textract')
        
        print(f"Extracting text from PDF: {key}")
        
        response = textract.detect_document_text(
            Document={
                'S3Object': {
                    'Bucket': bucket,
                    'Name': key
                }
            }
        )
        
        # Extract text blocks in reading order
        text_blocks = []
        for block in response.get('Blocks', []):
            if block['BlockType'] == 'LINE':
                text_blocks.append(block['Text'])
        
        raw_text = '\n'.join(text_blocks)
        
        # Clean up the text for better AI processing
        cleaned_text = clean_document_text(raw_text, key)
        
        return cleaned_text
        
    except Exception as e:
        print(f"Error processing PDF {key}: {e}")
        return None

def process_word_doc(s3_client, bucket, key):
    """Process Word documents - let them pass through for now"""
    try:
        # Word docs usually process better than PDFs in Bedrock
        # For now, we'll let Bedrock handle them directly
        print(f"Word document {key} will be processed by Bedrock directly")
        return None  # Don't process, let Bedrock handle it
        
    except Exception as e:
        print(f"Error processing Word doc {key}: {e}")
        return None

def process_text_file(s3_client, bucket, key):
    """Process plain text files"""
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        content = response['Body'].read().decode('utf-8')
        
        # Clean up text formatting
        cleaned_text = clean_document_text(content, key)
        
        return cleaned_text
        
    except Exception as e:
        print(f"Error processing text file {key}: {e}")
        return None

def clean_document_text(raw_text, filename):
    """Clean up document text for better AI processing"""
    
    filename_lower = filename.lower()
    
    # Special handling for calendar documents
    if 'calendar' in filename_lower or 'dates' in filename_lower:
        return clean_calendar_text(raw_text)
    
    # General text cleaning
    return clean_general_text(raw_text)

def clean_calendar_text(raw_text):
    """Clean up calendar-specific text"""
    
    lines = raw_text.split('\n')
    cleaned_lines = []
    current_month = None
    current_year = None
    
    # Find year in document
    for line in lines:
        if '2025' in line or '2026' in line:
            if '2025' in line:
                current_year = '2025'
            if '2026' in line:
                current_year = '2026'
            break
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Skip header/footer lines
        if any(skip in line.lower() for skip in ['key:', 'sh =', 'smc =', 'is =', 'ms =', 'js =', 'tbc =']):
            continue
        
        # Detect month headers
        months = ['September', 'October', 'November', 'December', 'January', 'February', 'March', 'April', 'May', 'June', 'July']
        for month in months:
            if month in line and (current_year in line if current_year else True):
                current_month = month
                cleaned_lines.append(f"\n{month.upper()} {current_year or '2025'} EVENTS:\n")
                break
        else:
            # Process event lines
            if current_month and any(day in line for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']):
                cleaned_line = format_calendar_event(line, current_month, current_year or '2025')
                if cleaned_line:
                    cleaned_lines.append(cleaned_line)
            elif line and not line.startswith(('KEY:', 'Please note')):
                cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)

def format_calendar_event(line, month, year):
    """Format calendar event lines for better AI understanding"""
    try:
        # Fix common OCR issues
        line = re.sub(r'(\d+)\s+(st|nd|rd|th)', r'\1\2', line)  # Fix "8 th" -> "8th"
        
        # Convert 24-hour times to 12-hour
        time_conversions = {
            '15:00': '3:00pm', '15:15': '3:15pm', '15:30': '3:30pm', '15:45': '3:45pm',
            '16:00': '4:00pm', '16:15': '4:15pm', '16:30': '4:30pm', '16:45': '4:45pm',
            '10:00': '10:00am', '11:00': '11:00am', '14:00': '2:00pm'
        }
        
        for time_24, time_12 in time_conversions.items():
            line = line.replace(time_24, time_12)
        
        # Convert location codes
        location_conversions = {
            ' SH': ', School Hall',
            ' SMC': ', St Mary\'s Church', 
            ' IS': ', Infant Site',
            ' MS': ', Middle Site',
            ' JS': ', Junior Site'
        }
        
        for code, location in location_conversions.items():
            line = line.replace(code, location)
        
        # Add month and year if missing
        if month not in line:
            # Find day pattern and insert month/year
            day_pattern = r'(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s+(\d+(?:st|nd|rd|th))'
            match = re.search(day_pattern, line)
            if match:
                day_part = match.group(0)
                rest = line[match.end():].strip()
                if rest.startswith(':'):
                    rest = rest[1:].strip()
                line = f"{day_part} {month} {year}: {rest}"
        
        return line
        
    except Exception as e:
        print(f"Error formatting calendar event: {e}")
        return line

def clean_general_text(raw_text):
    """General text cleaning for non-calendar documents"""
    
    # Remove excessive whitespace
    lines = [line.strip() for line in raw_text.split('\n')]
    lines = [line for line in lines if line]  # Remove empty lines
    
    # Join with single newlines
    cleaned_text = '\n'.join(lines)
    
    # Fix common OCR issues
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)  # Multiple spaces to single
    cleaned_text = re.sub(r'\n\s*\n', '\n\n', cleaned_text)  # Multiple newlines to double
    
    return cleaned_text

def save_processed_text(s3_client, bucket, original_key, processed_text, processed_prefix):
    """Save the processed text to S3"""
    
    # Create new key in processed folder
    filename = original_key.split('/')[-1]
    name_without_ext = '.'.join(filename.split('.')[:-1])
    processed_key = f"{processed_prefix}{name_without_ext}_processed.txt"
    
    # Add metadata
    metadata = {
        'original-file': original_key.replace('/', '-'),  # S3 metadata keys can't have /
        'processed-date': datetime.utcnow().isoformat(),
        'processor': 'document-processor-lambda'
    }
    
    # Upload processed text
    s3_client.put_object(
        Bucket=bucket,
        Key=processed_key,
        Body=processed_text.encode('utf-8'),
        ContentType='text/plain',
        Metadata=metadata
    )
    
    return processed_key

def trigger_knowledge_base_sync(bedrock_agent, knowledge_base_id, data_source_id):
    """Trigger knowledge base sync after processing"""
    try:
        print(f"Triggering Knowledge Base sync for KB: {knowledge_base_id}, DS: {data_source_id}")
        
        response = bedrock_agent.start_ingestion_job(
            knowledgeBaseId=knowledge_base_id,
            dataSourceId=data_source_id
        )
        
        job_id = response.get('ingestionJobId')
        print(f"✅ Knowledge Base sync started with job ID: {job_id}")
        
    except Exception as e:
        print(f"❌ Error triggering sync: {e}")
        raise