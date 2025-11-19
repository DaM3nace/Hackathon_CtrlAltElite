import streamlit as st
import os
from pathlib import Path
from rag_system import RAGSystem
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_session_state():
    if 'rag_system' not in st.session_state:
        st.session_state.rag_system = RAGSystem()
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

def display_chat_history():
    for i, (query, response) in enumerate(st.session_state.chat_history):
        with st.container():
            st.markdown(f"**You:** {query}")
            st.markdown(f"**Assistant:** {response}")
            st.divider()

def main():
    st.set_page_config(
        page_title="Knowledge Base Chatbot",
        page_icon="🤖",
        layout="wide"
    )
    
    st.title("🤖 Knowledge Base Chatbot")
    st.markdown("Ask questions about your documents stored in Databricks!")
    
    initialize_session_state()
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("📊 Knowledge Base Stats")
        
        if st.button("Refresh Stats"):
            try:
                stats = st.session_state.rag_system.get_knowledge_base_stats()
                if stats:
                    st.metric("Total Chunks", stats.get('total_chunks', 0))
                    st.metric("Unique Files", stats.get('unique_files', 0))
                    st.metric("Avg Token Count", f"{stats.get('avg_token_count', 0):.1f}")
                    st.write(f"Last Updated: {stats.get('last_updated', 'N/A')}")
                else:
                    st.info("No data in knowledge base yet")
            except Exception as e:
                st.error(f"Error fetching stats: {str(e)}")
        
        st.header("📁 Document Management")
        
        default_path = os.getenv('DOCUMENTS_DIRECTORY', './SOP')
        documents_path = st.text_input(
            "Documents Directory Path",
            value=default_path,
            placeholder="Enter path to your documents folder"
        )
        
        if st.button("Update Knowledge Base"):
            if documents_path and Path(documents_path).exists():
                try:
                    with st.spinner("Processing documents..."):
                        st.session_state.rag_system.update_knowledge_base(documents_path)
                    st.success("Knowledge base updated successfully!")
                except Exception as e:
                    st.error(f"Error updating knowledge base: {str(e)}")
            else:
                st.error("Please provide a valid directory path")
        
        st.header("⚙️ Settings")
        top_k = st.slider("Number of relevant chunks to retrieve", 1, 10, 5)
    
    # Main chat interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("💬 Chat")
        
        # Display chat history
        if st.session_state.chat_history:
            st.subheader("Chat History")
            display_chat_history()
        
        # Query input
        query = st.text_input(
            "Ask a question about your documents:",
            placeholder="What would you like to know?",
            key="query_input"
        )
        
        col_ask, col_clear = st.columns([1, 1])
        
        with col_ask:
            if st.button("Ask Question", type="primary"):
                if query.strip():
                    try:
                        with st.spinner("Searching knowledge base..."):
                            result = st.session_state.rag_system.ask_question(query, top_k)
                        
                        # Add to chat history
                        st.session_state.chat_history.append((query, result['response']))
                        
                        # Display current response
                        st.success("Response generated!")
                        st.markdown(f"**Question:** {query}")
                        st.markdown(f"**Answer:** {result['response']}")
                        
                        # Clear the input
                        st.session_state.query_input = ""
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Error processing query: {str(e)}")
                else:
                    st.warning("Please enter a question")
        
        with col_clear:
            if st.button("Clear Chat"):
                st.session_state.chat_history = []
                st.rerun()
    
    with col2:
        if st.session_state.chat_history:
            st.header("📄 Sources")
            
            # Show sources for the last query
            if st.session_state.chat_history:
                try:
                    last_query = st.session_state.chat_history[-1][0]
                    result = st.session_state.rag_system.ask_question(last_query, top_k)
                    
                    if result['sources']:
                        st.subheader("Relevant Documents:")
                        for i, source in enumerate(result['sources'], 1):
                            with st.expander(f"Source {i}: {source['file_name']}"):
                                st.write(f"**File:** {source['file_name']}")
                                st.write(f"**Path:** {source['file_path']}")
                                st.write(f"**Similarity:** {source['similarity']}")
                    else:
                        st.info("No sources found for the last query")
                except Exception as e:
                    st.error(f"Error displaying sources: {str(e)}")

if __name__ == "__main__":
    main()