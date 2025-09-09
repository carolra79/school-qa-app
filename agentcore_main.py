import json
import boto3
from datetime import datetime
from config import AUTHORIZED_UPLOADERS, USER_CREDENTIALS, AWS_REGION, KNOWLEDGE_BASE_ID, DATA_SOURCE_ID, S3_BUCKET, S3_PREFIX

class SchoolQAAgentCore:
    def __init__(self):
        self.bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name=AWS_REGION)
        self.s3_client = boto3.client('s3', region_name=AWS_REGION)
        self.bedrock_agent = boto3.client('bedrock-agent', region_name=AWS_REGION)
        self.session_data = {}
    
    def process_message(self, session_id, message, user_context=None):
        """Main AgentCore message processing"""
        
        # Handle authentication commands
        if message.startswith("/login"):
            parts = message.split()
            if len(parts) == 3:
                username, password = parts[1], parts[2]
                if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
                    self.session_data[session_id] = {
                        'authenticated': True,
                        'username': username,
                        'can_upload': username in AUTHORIZED_UPLOADERS
                    }
                    return f"✅ Welcome {username}! {'You can upload documents.' if username in AUTHORIZED_UPLOADERS else 'Read-only access.'}"
                else:
                    return "❌ Invalid credentials"
            return "Usage: /login <username> <password>"
        
        # Check authentication for other commands
        session = self.session_data.get(session_id, {})
        if not session.get('authenticated'):
            return "Please login first with: /login <username> <password>"
        
        # Handle upload command
        if message.startswith("/upload"):
            if not session.get('can_upload'):
                return "❌ You don't have upload permissions"
            return "To upload documents, use the web interface or send files directly to this chat."
        
        # Handle logout
        if message == "/logout":
            if session_id in self.session_data:
                del self.session_data[session_id]
            return "👋 Logged out successfully"
        
        # Handle help
        if message == "/help":
            return """📚 St Marys Class Rep Bot Commands:
/login <username> <password> - Login to the system
/upload - Get upload instructions
/logout - Logout
/help - Show this help

Or just ask questions like:
• When are 5M PE Days?
• What are the term dates for 2025-26?
• When is the christmas fair?
• When does the autumn term end in 2025?"""
        
        # Process regular questions
        return self._query_knowledge_base(message)
    
    def _query_knowledge_base(self, question):
        """Query Bedrock Knowledge Base"""
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
            
            # Add sources if available
            if 'citations' in response:
                sources = []
                for citation in response['citations']:
                    for reference in citation.get('retrievedReferences', []):
                        source_name = reference.get('location', {}).get('s3Location', {}).get('uri', 'Unknown')
                        sources.append(source_name.split('/')[-1] if '/' in source_name else source_name)
                
                if sources:
                    answer += f"\n\n📖 Sources: {', '.join(set(sources))}"
            
            return answer
            
        except Exception as e:
            return f"❌ Error: {str(e)}"

# AgentCore Lambda handler
def lambda_handler(event, context):
    agent = SchoolQAAgentCore()
    
    try:
        # Extract message and session from event
        body = json.loads(event.get('body', '{}'))
        message = body.get('message', '')
        session_id = body.get('session_id', 'default')
        
        # Process the message
        response_text = agent.process_message(session_id, message)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'response': response_text,
                'session_id': session_id
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': str(e)
            })
        }

if __name__ == "__main__":
    # Test locally
    agent = SchoolQAAgentCore()
    
    print("🤖 St Marys Class Rep Bot (AgentCore)")
    print("Type /help for commands or ask questions directly")
    
    session_id = "test_session"
    
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ['quit', 'exit']:
            break
        
        response = agent.process_message(session_id, user_input)
        print(f"Bot: {response}")
