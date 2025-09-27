import streamlit as st
import boto3
import uuid
import json
from config import AWS_REGION, S3_BUCKET, DATA_SOURCE_ID, KNOWLEDGE_BASE_ID

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_bedrock_config():
    """Load Bedrock configuration from S3"""
    try:
        s3_client = boto3.client('s3', region_name=AWS_REGION)
        response = s3_client.get_object(Bucket=S3_BUCKET, Key='config/bedrock_config.json')
        return json.loads(response['Body'].read().decode('utf-8'))
    except Exception as e:
        # Fallback to local config
        with open('bedrock_config.json', 'r') as f:
            return json.load(f)

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_fallback_config():
    """Load fallback links configuration from S3"""
    try:
        s3_client = boto3.client('s3', region_name=AWS_REGION)
        response = s3_client.get_object(Bucket=S3_BUCKET, Key='config/fallback_links.json')
        return json.loads(response['Body'].read().decode('utf-8'))
    except Exception as e:
        # Fallback to local config
        with open('fallback_links.json', 'r') as f:
            return json.load(f)

def get_fallback_link(question, answer):
    """Get appropriate fallback link based on question content and answer uncertainty"""
    try:
        config = load_fallback_config()
        
        # Check if answer indicates uncertainty
        uncertainty_detected = any(keyword.lower() in answer.lower() 
                                 for keyword in config['uncertainty_keywords'])
        
        if not uncertainty_detected:
            return None
            
        # Match question to appropriate link
        question_lower = question.lower()
        fallback_links = config['fallback_links']
        
        for topic, link in fallback_links.items():
            if topic != 'default' and topic in question_lower:
                return link
                
        # Return default link if no specific match
        return fallback_links['default']
        
    except Exception as e:
        return None

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

def simple_auth():
    """Simple authentication system for admin uploads only"""
    if not st.session_state.authenticated:
        # Add spacing to align with main header
        st.sidebar.markdown("<br><br><br><br><br>", unsafe_allow_html=True)
        st.sidebar.title("Admin Login")
        st.sidebar.markdown("<br>", unsafe_allow_html=True)
        username = st.sidebar.text_input("Username")
        st.sidebar.markdown("<br>", unsafe_allow_html=True)
        password = st.sidebar.text_input("Password", type="password")
        
        if st.sidebar.button("Login"):
            if username == "admin" and password == "admin123":
                st.session_state.authenticated = True
                st.session_state.username = username
                st.rerun()
            else:
                st.sidebar.error("Invalid admin credentials")

def upload_to_s3(file):
    """Upload file to S3 bucket - Updated 2025-09-15 16:43"""
    try:
        s3_client = boto3.client('s3', region_name=AWS_REGION)
        file_key = f"school-docs/{file.name}"
        print(f"DEBUG: Uploading to S3 path: {file_key}")  # Debug line
        
        s3_client.upload_fileobj(
            file,
            S3_BUCKET,
            file_key,
            ExtraArgs={'Metadata': {'uploaded_by': st.session_state.username}}
        )
        return True, None
    except Exception as e:
        return False, str(e)

def sync_knowledge_base():
    """Trigger knowledge base sync after upload"""
    try:
        bedrock_agent = boto3.client('bedrock-agent', region_name=AWS_REGION)
        
        response = bedrock_agent.start_ingestion_job(
            knowledgeBaseId=KNOWLEDGE_BASE_ID,
            dataSourceId=DATA_SOURCE_ID
        )
        return True, response.get('ingestionJob', {}).get('ingestionJobId', 'Unknown')
    except Exception as e:
        st.error(f"Error syncing knowledge base: {str(e)}")
        return False, None

def query_agentcore_runtime(question):
    """Query the knowledge base using retrieve_and_generate"""
    try:
        config = load_bedrock_config()
        bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name=AWS_REGION)
        
        response = bedrock_agent_runtime.retrieve_and_generate(
            input={'text': question},
            retrieveAndGenerateConfiguration={
                'type': 'KNOWLEDGE_BASE',
                'knowledgeBaseConfiguration': {
                    'knowledgeBaseId': KNOWLEDGE_BASE_ID,
                    'modelArn': config['model_arn'],
                    'generationConfiguration': {
                        'inferenceConfig': {
                            'textInferenceConfig': {
                                'temperature': config.get('temperature', 0.1),
                                'maxTokens': config.get('max_tokens', 1000)
                            }
                        },
                        'promptTemplate': {
                            'textPromptTemplate': config.get('prompt_template', config['system_instructions'] + '\n\nQuestion: $query$\n\nAnswer:')
                        }
                    }
                }
            }
        )
        
        answer = response['output']['text']
        
        # Check if we need to add a fallback link
        fallback_link = get_fallback_link(question, answer)
        if fallback_link:
            answer += f"\n\nFor more information, please visit: {fallback_link}"
        
        return answer
        
    except Exception as e:
        return f"Error querying knowledge base: {str(e)}"

def main():
    st.set_page_config(
        page_title="St Mary's Yr5 Class Rep Bot v2.2",
        page_icon="🎓",  # This shows in browser tab
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Remove top padding/margin
    st.markdown("""
        <style>
        .main > div {
            padding-top: 2.5rem;
        }
        .block-container {
            padding-top: 2.5rem;
        }
        .stImage {
            margin-bottom: -1rem;
        }
        </style>
        """, unsafe_allow_html=True)
    
    # Display logo and title aligned to the left
    try:
        st.image("st-marys-logo.png", width=80)
    except:
        st.write("🎓")  # Fallback to emoji if logo not found
    
    st.markdown("# St Mary's Yr5 Class Rep Bot")
    st.markdown("Powered by AWS Bedrock and AgentCore Runtime")
    
    simple_auth()
    
    # Main chat interface
    if st.session_state.authenticated and st.session_state.username == "admin":
        # Two column layout for admin (with document management)
        col1, col2 = st.columns([2, 1])
    else:
        # Single column layout for regular users
        col1 = st.container()
        col2 = None

    with col1:
        st.markdown(
            """
            <style>
            .stTextInput {
                margin-top: -30px;
            }
            </style>
            """, 
            unsafe_allow_html=True
        )
        
        st.subheader("💬 Ask a Question")
        
        # Question input (submits on Enter)
        # Check if we have a selected question to populate
        default_question = st.session_state.get('selected_question', '')
        
        question = st.text_input(
            "",
            value=default_question,
            placeholder="e.g. when are year 5 PE days",
            help="Press Enter to submit or click Ask button"
        )
        
        # Add Ask button
        ask_button = st.button("Ask", type="primary")
        
        # Process question if it exists and is different from last processed, or if button clicked
        if question and (ask_button or question != st.session_state.get('last_processed_question', '')):
            st.session_state.last_processed_question = question
            
            with st.spinner("Searching for answer..."):
                answer = query_agentcore_runtime(question)
                
                # Add to chat history
                st.session_state.chat_history.append((question, answer))
                
                # Store answer to display
                st.session_state.last_qa = (question, answer)
                
                # Clear the selected question and processing state
                if 'selected_question' in st.session_state:
                    st.session_state.selected_question = ''
                if 'processing' in st.session_state:
                    del st.session_state.processing
                
                # Clear the question for next input
                st.rerun()
        
        # Display last answer below the input
        if 'last_qa' in st.session_state:
            question_text, answer = st.session_state.last_qa
            
            # Display in a pale green box
            st.markdown(
                f"""
                <div style="background-color: #e8f5e8; padding: 15px; border-radius: 10px; border-left: 4px solid #4CAF50; margin: 10px 0;">
                    <p><strong>Question:</strong> {question_text}</p>
                    <p><strong>Answer:</strong> {answer}</p>
                </div>
                """, 
                unsafe_allow_html=True
            )
        
        # Suggested questions (only show if not processing)
        if not st.session_state.get('processing', False):
            # Add space before suggested questions
            st.markdown("<br>", unsafe_allow_html=True)
            st.subheader("💡 Suggested Questions")
            sample_questions = [
                "When are 5M PE Days?",
                "What are the term dates for 2025-26?",
                "When is the christmas fair?",
                "When does the autumn term end in 2025?"
            ]
            
            # Add CSS to reduce column gap
            st.markdown(
                """
                <style>
                .row-widget.stHorizontal > div {
                    gap: 0.5rem !important;
                }
                </style>
                """, 
                unsafe_allow_html=True
            )
            
            # Put all suggested questions in one column
            for i, sample_q in enumerate(sample_questions):
                if st.button(sample_q, key=f"sample_{i}"):
                    # Set the question to be populated and auto-submitted
                    st.session_state.selected_question = sample_q
                    st.session_state.processing = True
                    st.rerun()

    if col2 is not None:  # Only show for admin
        with col2:
            st.subheader("📁 Document Management")
            
            st.success(f"Logged in as: {st.session_state.username}")
            
            # File upload
            uploaded_file = st.file_uploader(
                "Upload school documents",
                type=['pdf', 'txt', 'docx'],
                help="Upload PDF, TXT, or DOCX files"
            )
            
            if uploaded_file is not None:
                if st.button("Upload Document"):
                    with st.spinner("Uploading..."):
                        success, error_msg = upload_to_s3(uploaded_file)
                        
                        if success:
                            st.success(f"✅ File uploaded successfully: {uploaded_file.name}")
                        else:
                            st.error(f"❌ Error uploading file: {error_msg}")
            
            # Logout button
            if st.button("Logout"):
                st.session_state.authenticated = False
                st.session_state.username = ""
                st.rerun()
            
            # Clear chat history
            if st.button("Clear Chat History"):
                st.session_state.chat_history = []
                st.session_state.session_id = str(uuid.uuid4())
                st.rerun()

if __name__ == "__main__":
    main()