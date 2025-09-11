import streamlit as st
import boto3
import uuid
from config import AWS_REGION, S3_BUCKET, DATA_SOURCE_ID, KNOWLEDGE_BASE_ID

# Page config
st.set_page_config(
    page_title="St Marys Year5 Class Rep Bot",
    page_icon="🏫",
    layout="wide"
)

# Simple authentication
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🏫 St Marys Year5 Class Rep Bot")
    st.markdown("### Access Required")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        access_code = st.text_input("Enter school access code:", type="password", placeholder="Ask your class rep for the code")
        
        if st.button("Access Q&A System", type="primary"):
            if access_code == "stmarys2025":
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Invalid access code. Please contact your class representative.")
        
        st.info("💡 This system is for St Marys Year 5 families only. Contact your class rep for access.")
    st.stop()

# Rest of your existing app code here...
st.title("🏫 St Marys Year5 Class Rep Bot")
st.markdown("Ask questions about school information, events, and policies")

# Your existing Q&A functionality
def query_knowledge_base(question):
    """Query the Bedrock Knowledge Base"""
    try:
        from datetime import datetime
        
        bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name=AWS_REGION)
        
        current_date = datetime.now().strftime("%B %Y")
        enhanced_question = f"Current date context: {current_date}. Question: {question}"
        
        response = bedrock_agent_runtime.retrieve_and_generate(
            input={'text': enhanced_question},
            retrieveAndGenerateConfiguration={
                'type': 'KNOWLEDGE_BASE',
                'knowledgeBaseConfiguration': {
                    'knowledgeBaseId': KNOWLEDGE_BASE_ID,
                    'modelArn': f'arn:aws:bedrock:{AWS_REGION}::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0'
                }
            }
        )
        
        return response['output']['text']
    except Exception as e:
        return f"Error querying knowledge base: {str(e)}"

# Main interface
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Ask a Question")
    
    # Suggested questions
    st.markdown("**Popular Questions:**")
    suggestions = [
        "When are the Year 5 PE days?",
        "What time does school start and finish?",
        "When is the next school holiday?",
        "What's the homework policy?",
        "How do I contact the school office?"
    ]
    
    for suggestion in suggestions:
        if st.button(suggestion, key=f"suggest_{suggestion}"):
            st.session_state.current_question = suggestion
    
    # Question input
    question = st.text_input("Or type your own question:", 
                           value=st.session_state.get('current_question', ''),
                           placeholder="e.g., When is the next parent-teacher conference?")
    
    if st.button("Ask Question", type="primary") and question:
        with st.spinner("Searching school information..."):
            answer = query_knowledge_base(question)
            st.markdown("### Answer:")
            st.markdown(answer)

with col2:
    st.subheader("ℹ️ About")
    st.markdown("""
    This bot helps Year 5 families find information about:
    - School schedules and events
    - Policies and procedures  
    - Contact information
    - Important dates
    
    **Need help?** Contact your class representative.
    """)
    
    # Admin section (existing code)
    with st.expander("📁 Admin - Document Upload"):
        admin_password = st.text_input("Admin Password:", type="password", key="admin_pass")
        
        if admin_password == "admin123":
            uploaded_file = st.file_uploader("Upload school document:", type=['pdf', 'docx', 'txt'])
            
            if uploaded_file and st.button("Upload Document"):
                with st.spinner("Uploading and processing..."):
                    # Your existing upload code
                    st.success("Document uploaded successfully!")
        elif admin_password:
            st.error("Invalid admin password")
