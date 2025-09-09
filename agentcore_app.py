import boto3
import json
from datetime import datetime
from config import AUTHORIZED_UPLOADERS, USER_CREDENTIALS, AWS_REGION, KNOWLEDGE_BASE_ID, DATA_SOURCE_ID, S3_BUCKET, S3_PREFIX

class SchoolQAAgent:
    def __init__(self):
        self.bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name=AWS_REGION)
        self.s3_client = boto3.client('s3', region_name=AWS_REGION)
        self.bedrock_agent = boto3.client('bedrock-agent', region_name=AWS_REGION)
    
    def authenticate(self, username, password):
        """Simple authentication"""
        return username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password
    
    def can_upload(self, username):
        """Check upload permissions"""
        return username in AUTHORIZED_UPLOADERS
    
    def upload_document(self, file_content, filename, username):
        """Upload document to S3"""
        try:
            file_key = f"{S3_PREFIX}{filename}"
            self.s3_client.put_object(
                Bucket=S3_BUCKET,
                Key=file_key,
                Body=file_content,
                Metadata={'uploaded_by': username}
            )
            
            # Trigger knowledge base sync
            self.bedrock_agent.start_ingestion_job(
                knowledgeBaseId=KNOWLEDGE_BASE_ID,
                dataSourceId=DATA_SOURCE_ID
            )
            return {"success": True, "message": "Document uploaded and sync initiated"}
        except Exception as e:
            return {"success": False, "message": f"Upload failed: {str(e)}"}
    
    def query(self, question):
        """Query the knowledge base"""
        try:
            current_date = datetime.now().strftime("%B %Y")
            current_month = datetime.now().month
            
            if current_month in [9, 10, 11, 12]:
                current_term = "Autumn"
            elif current_month in [1, 2, 3, 4]:
                current_term = "Spring"
            else:
                current_term = "Summer"
            
            response = self.bedrock_agent_runtime.retrieve_and_generate(
                input={'text': question},
                retrieveAndGenerateConfiguration={
                    'type': 'KNOWLEDGE_BASE',
                    'knowledgeBaseConfiguration': {
                        'knowledgeBaseId': KNOWLEDGE_BASE_ID,
                        'modelArn': f'arn:aws:bedrock:{AWS_REGION}::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0',
                        'generationConfiguration': {
                            'promptTemplate': {
                                'textPromptTemplate': f'''Answer the question based on the school documents. Be direct and concise.

CONTEXT: Today is {current_term} term {current_date}. Terms typically Autumn: early Sept to late December then a break for christmas. Spring: Early Jan to late March or early April then a break for easter. Summer: late april to late july then a break for the summer holidays. The most accurate document for term dates will be a pdf with the title:St-Marys-Term-Dates

CRITICAL: When someone asks "last day of term" or "end of term", they mean the current {current_term} term. You should be able to see 3 last days of term, one for December, one for March or April and one for July. If you are not sure what the current date or term is, give all three dates in the form "the last days of term are: Autumn <date>, Spring <date>, Summer <date>"

Question: $query$
Context: $search_results$

Answer:'''
                            }
                        }
                    }
                }
            )
            
            answer = response['output']['text']
            sources = []
            
            if 'citations' in response:
                for citation in response['citations']:
                    for reference in citation.get('retrievedReferences', []):
                        sources.append({
                            'content': reference.get('content', {}).get('text', ''),
                            'source': reference.get('location', {}).get('s3Location', {}).get('uri', 'Unknown')
                        })
            
            return {"answer": answer, "sources": sources}
            
        except Exception as e:
            return {"error": f"Query failed: {str(e)}"}

# AgentCore handler
def lambda_handler(event, context):
    agent = SchoolQAAgent()
    
    try:
        body = json.loads(event.get('body', '{}'))
        action = body.get('action')
        
        if action == 'authenticate':
            username = body.get('username')
            password = body.get('password')
            success = agent.authenticate(username, password)
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'authenticated': success,
                    'can_upload': agent.can_upload(username) if success else False
                })
            }
        
        elif action == 'upload':
            username = body.get('username')
            filename = body.get('filename')
            file_content = body.get('file_content')  # base64 encoded
            
            if not agent.can_upload(username):
                return {
                    'statusCode': 403,
                    'body': json.dumps({'error': 'Upload not authorized'})
                }
            
            import base64
            file_data = base64.b64decode(file_content)
            result = agent.upload_document(file_data, filename, username)
            
            return {
                'statusCode': 200 if result['success'] else 400,
                'body': json.dumps(result)
            }
        
        elif action == 'query':
            question = body.get('question')
            result = agent.query(question)
            
            return {
                'statusCode': 200,
                'body': json.dumps(result)
            }
        
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Invalid action'})
            }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
