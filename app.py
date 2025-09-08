import streamlit as st
import boto3
import uuid
from datetime import datetime
from config import AUTHORIZED_UPLOADERS, USER_CREDENTIALS, AWS_REGION, KNOWLEDGE_BASE_ID, DATA_SOURCE_ID, S3_BUCKET, S3_PREFIX, SEARCH_RESULTS_LIMIT

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = ""

def simple_auth():
    """Simple authentication system for uploads only"""
    if not st.session_state.authenticated:
        st.sidebar.title("Login (for uploads)")
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")
        
        if st.sidebar.button("Login"):
            if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
                st.session_state.authenticated = True
                st.session_state.username = username
                st.rerun()
            else:
                st.sidebar.error("Invalid credentials")

def can_upload():
    """Check if user can upload documents"""
    return st.session_state.username in AUTHORIZED_UPLOADERS

def upload_to_s3(file):
    """Upload file to S3 bucket"""
    try:
        s3_client = boto3.client('s3', region_name=AWS_REGION)
        file_key = f"{S3_PREFIX}{file.name}"
        
        s3_client.upload_fileobj(
            file,
            S3_BUCKET,
            file_key,
            ExtraArgs={'Metadata': {'uploaded_by': st.session_state.username}}
        )
        return True, file_key
    except Exception as e:
        st.error(f"Error uploading to S3: {str(e)}")
        return False, None

def sync_knowledge_base():
    """Trigger knowledge base sync after upload"""
    try:
        bedrock_agent = boto3.client('bedrock-agent', region_name=AWS_REGION)
        
        response = bedrock_agent.start_ingestion_job(
            knowledgeBaseId=KNOWLEDGE_BASE_ID,
            dataSourceId=DATA_SOURCE_ID
        )
        return True
    except Exception as e:
        st.error(f"Error syncing knowledge base: {str(e)}")
        return False

def query_knowledge_base(query):
    """Query Bedrock Knowledge Base"""
    try:
        bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name=AWS_REGION)
        
        # Get current date for context
        current_date = datetime.now().strftime("%B %Y")  # e.g., "September 2025"
        current_month = datetime.now().month
        
        # Determine current school term based on month
        if current_month in [9, 10, 11, 12]:
            current_term = "Autumn"
        elif current_month in [1, 2, 3, 4]:
            current_term = "Spring"
        else:  # May, June, July, August
            current_term = "Summer"
        
        response = bedrock_agent_runtime.retrieve_and_generate(
            input={
                'text': query
            },
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
        
        return answer, sources
        
    except Exception as e:
        return f"Error querying knowledge base: {str(e)}", []

def main():
    st.set_page_config(page_title="St Marys Class Rep Bot", layout="wide")
    
    simple_auth()
    
    st.title("📚 St Marys Year 5 Class Rep Bot")
    st.caption("Powered by AWS Bedrock Knowledge Base")
    
    if st.session_state.authenticated:
        st.write(f"Welcome, {st.session_state.username}!")
    
    # Sidebar for logout
    if st.session_state.authenticated and st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.username = ""
        st.rerun()
    
    # Main interface
    if st.session_state.authenticated and can_upload():
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.header("📤 Document Upload")
            
            uploaded_files = st.file_uploader(
                "Upload documents",
                type=['pdf', 'docx', 'txt'],
                accept_multiple_files=True
            )
            
            if uploaded_files:
                if st.button("Upload to Knowledge Base"):
                    progress_bar = st.progress(0)
                    success_count = 0
                    
                    for i, file in enumerate(uploaded_files):
                        st.write(f"Uploading {file.name}...")
                        success, file_key = upload_to_s3(file)
                        
                        if success:
                            st.success(f"✅ {file.name} uploaded successfully")
                            success_count += 1
                        
                        progress_bar.progress((i + 1) / len(uploaded_files))
                    
                    if success_count > 0:
                        st.info("🔄 Syncing knowledge base... This may take a few minutes.")
                        if sync_knowledge_base():
                            st.success("Knowledge base sync initiated!")
                        else:
                            st.warning("Upload successful, but sync failed. Documents will be available after manual sync.")
            
            st.info("💡 Documents are stored in AWS S3 and processed by Bedrock Knowledge Base for fast, accurate responses.")
    else:
        col2 = st.container()
    
    with col2:
        st.header("❓ Ask Questions")
        
        # Initialize session state for selected question
        if 'selected_question' not in st.session_state:
            st.session_state.selected_question = ""
        if 'show_answer' not in st.session_state:
            st.session_state.show_answer = False
        if 'current_answer' not in st.session_state:
            st.session_state.current_answer = ""
        if 'current_sources' not in st.session_state:
            st.session_state.current_sources = []
        
        question = st.text_input("Ask the Class Rep Bot a question:", 
                                value=st.session_state.selected_question, 
                                key="question_input")
        
        # Always show Ask button, and process on button click or when question changes
        ask_button = st.button("Ask", key="ask_button")
        
        # Process question if button clicked or if it's a new question from suggestions
        if question and (ask_button or (question != st.session_state.get('last_processed_question', ''))):
            st.session_state.last_processed_question = question
            with st.spinner("Searching knowledge base and generating answer..."):
                answer, sources = query_knowledge_base(question)
                
                # Store answer in session state
                st.session_state.current_answer = answer
                st.session_state.current_sources = sources
                st.session_state.show_answer = True
                
                # Clear the question box for next question
                st.session_state.selected_question = ""
                st.rerun()
        
        # Display answer if available
        if st.session_state.show_answer and st.session_state.current_answer:
            st.subheader("💬 Answer:")
            st.write(st.session_state.current_answer)
            
            if st.session_state.current_sources:
                with st.expander("📖 Source Documents"):
                    for i, source in enumerate(st.session_state.current_sources, 1):
                        st.write(f"**Source {i}:**")
                        st.write(source['content'][:300] + "..." if len(source['content']) > 300 else source['content'])
                        st.caption(f"From: {source['source'].split('/')[-1] if '/' in source['source'] else source['source']}")
                        st.write("---")
        
        # Sample questions that populate the input box
        st.subheader("💡 Suggested Questions")
        sample_questions = [
            "When are 5M PE Days?",
            "What are the term dates for 2025-26?",
            "When is the christmas fair?",
            "When does the autumn term end in 2025?"
        ]
        
        for q in sample_questions:
            if st.button(q, key=f"sample_{q}"):
                st.session_state.selected_question = q
                st.session_state.show_answer = False  # Clear previous answer
                st.rerun()

if __name__ == "__main__":
    main()