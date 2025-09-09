import streamlit as st
import boto3
import uuid
from config import AWS_REGION, S3_BUCKET, DATA_SOURCE_ID, KNOWLEDGE_BASE_ID

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
    """Upload file to S3 bucket"""
    try:
        s3_client = boto3.client('s3', region_name=AWS_REGION)
        file_key = f"documents/{file.name}"
        
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
        return True, response.get('ingestionJob', {}).get('ingestionJobId', 'Unknown')
    except Exception as e:
        st.error(f"Error syncing knowledge base: {str(e)}")
        return False, None

def query_agentcore_runtime(question):
    """Query AgentCore Runtime"""
    try:
        # AgentCore Runtime ARN
        runtime_arn = "arn:aws:bedrock-agentcore:us-east-1:185749752590:runtime/school_qa_agent-0BI6caDueE"
        
        bedrock_agentcore = boto3.client('bedrock-agentcore', region_name=AWS_REGION)
        
        response = bedrock_agentcore.invoke_runtime(
            runtimeArn=runtime_arn,
            inputText=question,
            sessionId=st.session_state.session_id
        )
        
        # Extract the response text
        answer = response.get('outputText', "I couldn't find an answer to your question.")
        
        return answer
        
    except Exception as e:
        return f"Error querying AgentCore Runtime: {str(e)}"

def main():
    st.set_page_config(
        page_title="St Marys Year5 Class Rep Bot",
        page_icon="🎓",  # This shows in browser tab
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Display logo and title aligned to the left
    try:
        st.image("St Marys Logo.png", width=80)
    except:
        st.write("🎓")  # Fallback to emoji if logo not found
    
    st.markdown("# St Marys Year5 Class Rep Bot")
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
        
        st.markdown("**💬 Ask a Question**")
        
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
                        success, file_key = upload_to_s3(uploaded_file)
                        
                        if success:
                            st.success(f"✅ Uploaded: {uploaded_file.name}")
                            
                            # Sync knowledge base
                            with st.spinner("Updating knowledge base..."):
                                sync_success, job_id = sync_knowledge_base()
                                
                                if sync_success:
                                    st.info(f"🔄 Knowledge base sync started (Job: {job_id})")
                                    st.info("New documents will be available for questions in a few minutes.")
            
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
