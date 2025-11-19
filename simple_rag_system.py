import os
import time
import re
from typing import List, Dict, Any
from local_vector_store import LocalVectorStore
from document_processor import DocumentProcessor
from text_processor import TextProcessor
from conversation_logger import ConversationLogger
import logging
from dotenv import load_dotenv
import requests
import json

# Override=True forces .env file values to override system environment variables
load_dotenv(override=True)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleRAGSystem:
    def __init__(self, embedding_model_name: str = "all-MiniLM-L6-v2",
                 similarity_threshold: float = 0.3,
                 use_databricks_fallback: bool = True,
                 use_databricks_embeddings: bool = False):

        # Initialize embedding model (Databricks or local)
        self.use_databricks_embeddings = use_databricks_embeddings or os.getenv('USE_DATABRICKS_EMBEDDINGS', 'false').lower() == 'true'

        if self.use_databricks_embeddings:
            try:
                from databricks_embeddings import DatabricksEmbeddings
                self.embedding_model = DatabricksEmbeddings()
                logger.info("Using Databricks embeddings (databricks-bge-large-en)")
            except Exception as e:
                logger.warning(f"Could not load Databricks embeddings: {str(e)}. Falling back to local model.")
                self.use_databricks_embeddings = False

        if not self.use_databricks_embeddings:
            try:
                from sentence_transformers import SentenceTransformer
                self.embedding_model = SentenceTransformer(embedding_model_name)
                logger.info(f"Using local embeddings ({embedding_model_name})")
            except Exception as e:
                logger.warning(f"Could not load embedding model: {str(e)}. Using dummy embeddings.")
                self.embedding_model = None

        # Storage configuration
        self.use_databricks_storage = os.getenv('USE_DATABRICKS_STORAGE', 'false').lower() == 'true'

        if self.use_databricks_storage:
            try:
                from databricks_storage import DatabricksStorage
                self.databricks_storage = DatabricksStorage()
                logger.info("Using Databricks storage")
                # Load vectors from Databricks
                vectors = self.databricks_storage.load_all_vectors()
                # Create vector store without local file when using Databricks
                self.vector_store = LocalVectorStore(use_local_file=False)
                if vectors:
                    # Add vectors to local store for fast search (in-memory only)
                    self.vector_store.vectors = vectors
                    logger.info(f"Loaded {len(vectors)} vectors from Databricks")
                else:
                    logger.warning("No vectors found in Databricks storage")
            except Exception as e:
                logger.error(f"Could not load Databricks storage: {str(e)}. Falling back to local storage.")
                self.use_databricks_storage = False
                self.vector_store = LocalVectorStore()
        else:
            self.vector_store = LocalVectorStore()
            logger.info("Using local storage")

        self.conversation_logger = ConversationLogger()

        # Initialize Jobs module for tech job lookups
        try:
            from databricks_jobs import DatabricksJobs
            self.jobs_module = DatabricksJobs()
            logger.info("Databricks Jobs module initialized")
        except Exception as e:
            logger.warning(f"Could not initialize Jobs module: {str(e)}")
            self.jobs_module = None

        # Databricks configuration
        self.similarity_threshold = similarity_threshold
        self.use_databricks_fallback = use_databricks_fallback
        self.databricks_endpoint = os.getenv('DATABRICKS_SERVER_HOSTNAME', '')
        self.databricks_token = os.getenv('DATABRICKS_TOKEN', '')
        self.databricks_model = "databricks-gpt-5-1"  # Databricks Foundation Model

        self.system_prompt = """You are a helpful assistant that answers questions based on the provided context from a knowledge base.

Instructions:
- Use only the information provided in the context to answer questions
- If the context doesn't contain enough information to answer the question, say so clearly
- Provide specific references to source documents when possible
- Be concise but comprehensive in your responses
        """

    def generate_query_embedding(self, query: str) -> List[float]:
        if self.embedding_model is None:
            # Return dummy embedding for testing
            return [0.1] * 384

        if self.use_databricks_embeddings:
            # Databricks embeddings expect list input
            embeddings = self.embedding_model.encode([query])
            return embeddings[0] if embeddings else [0.1] * 1024
        
        try:
            embedding = self.embedding_model.encode([query])[0]
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating query embedding: {str(e)}")
            return [0.1] * 384
    
    def retrieve_relevant_chunks(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        query_embedding = self.generate_query_embedding(query)
        results = self.vector_store.search_similar(query_embedding, top_k)
        logger.info(f"Retrieved {len(results)} relevant chunks for query")
        return results
    
    def format_context(self, chunks: List[Dict[str, Any]]) -> str:
        if not chunks:
            return "No relevant information found in the knowledge base."
        
        context = "Context from knowledge base:\n\n"
        
        for i, chunk in enumerate(chunks, 1):
            file_name = chunk.get('metadata', {}).get('file_name', 'Unknown')
            context += f"Document {i}: {file_name}\n"
            context += f"Content: {chunk['content']}\n"
            if 'similarity' in chunk:
                context += f"Relevance: {chunk['similarity']:.3f}\n\n"
        
        return context
    
    def call_databricks_model(self, query: str, context: str = "") -> Dict[str, Any]:
        """Call Databricks Foundation Model API using direct HTTP requests"""
        try:
            import requests

            databricks_host = os.getenv('DATABRICKS_SERVER_HOSTNAME', self.databricks_endpoint)
            api_key = os.getenv('DATABRICKS_TOKEN', self.databricks_token)
            model_name = os.getenv('DATABRICKS_LLM_MODEL', 'databricks-gpt-5-1')

            # Databricks serving endpoint URL
            url = f"https://{databricks_host}/serving-endpoints/{model_name}/invocations"

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }

            # Build prompt with context if available
            if context and "No relevant information found" not in context:
                prompt = f"""Based on the following context from our knowledge base, please answer the user's question. If the context doesn't fully answer the question, you may supplement with your general knowledge but clearly indicate which parts come from the provided context.

Context:
{context}

User Question: {query}

Please provide a clear, helpful answer:"""
            else:
                prompt = f"""The following question could not be answered using our knowledge base documents. Please provide a helpful, accurate answer based on your general knowledge.

User Question: {query}

Answer:"""

            # Databricks API payload
            payload = {
                "messages": [
                    {"role": "system", "content": "You are a helpful AI assistant that provides accurate, clear answers to questions."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 1000,
                "temperature": 0.7
            }

            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()

            result = response.json()

            # Extract answer from response
            if 'choices' in result:
                answer = result['choices'][0]['message']['content']
            elif 'predictions' in result:
                answer = result['predictions'][0] if result['predictions'] else "No response generated"
            else:
                logger.error(f"Unexpected response format: {result}")
                answer = "AI model returned unexpected format"

            return {
                "success": True,
                "response": answer,
                "model": model_name,
                "used_context": bool(context and "No relevant information found" not in context)
            }

        except Exception as e:
            logger.error(f"Error calling Databricks model: {str(e)}")
            return {
                "success": False,
                "response": None,
                "error": str(e)
            }

    def check_similarity_threshold(self, chunks: List[Dict[str, Any]]) -> bool:
        """Check if any retrieved chunks meet the similarity threshold"""
        if not chunks:
            return False

        max_similarity = max(chunk.get('similarity', 0) for chunk in chunks)
        return max_similarity >= self.similarity_threshold

    def generate_response(self, query: str, context: str, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate response using RAG or fallback to Databricks model"""

        # Check if we have good enough document matches
        has_good_match = self.check_similarity_threshold(chunks)

        # If no relevant docs found or similarity too low, use Databricks fallback
        if not has_good_match and self.use_databricks_fallback and self.databricks_token:
            logger.info(f"Low similarity score (max: {max([c.get('similarity', 0) for c in chunks]) if chunks else 0:.3f}), using Databricks model fallback")

            db_result = self.call_databricks_model(query, context if has_good_match else "")

            if db_result["success"]:
                response_text = db_result["response"]
                if db_result["used_context"]:
                    response_text += "\n\n[Source: RAG + Databricks AI Model]"
                else:
                    response_text += "\n\n[Source: Databricks AI Model - No relevant documents found]"

                return {
                    "text": response_text,
                    "model_used": self.databricks_model,
                    "used_fallback": True,
                    "used_context": db_result["used_context"]
                }
            else:
                # Fallback failed, return basic response
                return {
                    "text": "I couldn't find relevant information in the knowledge base, and the AI model is currently unavailable. Please try again later or rephrase your question.",
                    "model_used": "none",
                    "used_fallback": False,
                    "error": db_result.get("error")
                }

        # Use standard RAG response with context from documents
        if "No relevant information found" in context:
            response_text = "I couldn't find relevant information in the knowledge base to answer your question."
        else:
            response_text = f"Based on the available documents, here's what I found:\n\n{context}"

        return {
            "text": response_text,
            "model_used": "rag_local",
            "used_fallback": False,
            "used_context": True
        }
    
    def extract_tech_id(self, query: str) -> str:
        """Extract tech ID from query (e.g., TECH001, tech123, etc.)"""
        # Pattern to match tech IDs like TECH001, tech123, T001, etc.
        patterns = [
            r'\bTECH\d+\b',  # TECH001, TECH123
            r'\btech\d+\b',  # tech001, tech123
            r'\bT\d{3,}\b',  # T001, T0001
        ]

        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(0).upper()

        return None

    def is_job_query(self, query: str) -> bool:
        """Check if query is asking about tech jobs"""
        job_keywords = [
            'job', 'jobs', 'schedule', 'appointment', 'work order',
            'assignment', 'task', 'ticket', 'service call'
        ]

        tech_keywords = [
            'tech', 'technician', 'my jobs', 'my schedule', 'my appointments'
        ]

        query_lower = query.lower()

        # Check if query contains both job-related and tech-related keywords
        has_job_keyword = any(keyword in query_lower for keyword in job_keywords)
        has_tech_keyword = any(keyword in query_lower for keyword in tech_keywords)

        # Or if it contains tech ID
        has_tech_id = self.extract_tech_id(query) is not None

        return (has_job_keyword and has_tech_keyword) or (has_job_keyword and has_tech_id)

    def handle_job_query(self, query: str) -> Dict[str, Any]:
        """Handle job-related queries"""
        tech_id = self.extract_tech_id(query)

        if not tech_id:
            return {
                "success": False,
                "message": "Please provide a tech ID to look up jobs. Example: 'Show jobs for TECH001'"
            }

        if not self.jobs_module:
            return {
                "success": False,
                "message": "Jobs module is not available."
            }

        try:
            # Get tech info
            tech_info = self.jobs_module.get_tech_info(tech_id)

            # Get jobs for tech
            jobs = self.jobs_module.get_jobs_for_tech(tech_id)

            response = ""

            if tech_info:
                response += self.jobs_module.format_tech_info(tech_info)
                response += "\n\n"
            else:
                response += f"Tech ID '{tech_id}' not found in system.\n\n"

            response += self.jobs_module.format_jobs_for_display(jobs)

            return {
                "success": True,
                "message": response,
                "tech_id": tech_id,
                "job_count": len(jobs)
            }

        except Exception as e:
            logger.error(f"Error handling job query: {str(e)}")
            return {
                "success": False,
                "message": f"Error retrieving jobs: {str(e)}"
            }

    def ask_question(self, query: str, top_k: int = 5, session_id: str = None, user_id: str = "anonymous") -> Dict[str, Any]:
        start_time = time.time()
        logger.info(f"Processing query: {query}")

        # Generate session ID if not provided
        if session_id is None:
            import uuid
            session_id = str(uuid.uuid4())

        # Check if this is a job query and handle it separately
        if self.is_job_query(query):
            logger.info("Detected job query, routing to jobs module")
            job_result = self.handle_job_query(query)

            response_time_ms = (time.time() - start_time) * 1000

            if job_result["success"]:
                response = job_result["message"]

                # Log the conversation
                conversation_id = self.conversation_logger.log_conversation(
                    session_id=session_id,
                    user_query=query,
                    bot_response=response,
                    sources=[],
                    response_time_ms=response_time_ms,
                    user_id=user_id,
                    metadata={
                        "query_type": "job_lookup",
                        "tech_id": job_result.get("tech_id"),
                        "job_count": job_result.get("job_count", 0)
                    }
                )

                return {
                    "query": query,
                    "response": response,
                    "context": "Job lookup from Databricks",
                    "sources": [],
                    "num_sources": 0,
                    "conversation_id": conversation_id,
                    "session_id": session_id,
                    "response_time_ms": response_time_ms,
                    "model_used": "databricks_jobs",
                    "used_fallback": False
                }
            else:
                # Job query failed, return error message
                response = job_result["message"]

                conversation_id = self.conversation_logger.log_conversation(
                    session_id=session_id,
                    user_query=query,
                    bot_response=response,
                    sources=[],
                    response_time_ms=response_time_ms,
                    user_id=user_id,
                    metadata={"query_type": "job_lookup_failed"}
                )

                return {
                    "query": query,
                    "response": response,
                    "context": "",
                    "sources": [],
                    "num_sources": 0,
                    "conversation_id": conversation_id,
                    "session_id": session_id,
                    "response_time_ms": response_time_ms,
                    "model_used": "none",
                    "used_fallback": False
                }

        # Regular RAG query processing
        relevant_chunks = self.retrieve_relevant_chunks(query, top_k)
        context = self.format_context(relevant_chunks)

        # Generate response with potential fallback to Databricks model
        response_data = self.generate_response(query, context, relevant_chunks)
        response = response_data["text"]

        # Calculate response time
        response_time_ms = (time.time() - start_time) * 1000

        # Prepare sources for logging
        sources = [
            {
                "file_name": chunk.get('metadata', {}).get('file_name', 'Unknown'),
                "file_path": chunk.get('metadata', {}).get('file_path', 'Unknown'),
                "similarity": chunk.get("similarity", "N/A")
            }
            for chunk in relevant_chunks
        ]

        # Log the conversation
        conversation_id = self.conversation_logger.log_conversation(
            session_id=session_id,
            user_query=query,
            bot_response=response,
            sources=sources,
            response_time_ms=response_time_ms,
            user_id=user_id,
            metadata={
                "top_k": top_k,
                "context_length": len(context),
                "model_used": response_data.get("model_used", "simple_rag_local"),
                "used_fallback": response_data.get("used_fallback", False),
                "similarity_threshold": self.similarity_threshold,
                "max_similarity": max([c.get('similarity', 0) for c in relevant_chunks]) if relevant_chunks else 0
            }
        )

        return {
            "query": query,
            "response": response,
            "context": context,
            "sources": sources,
            "num_sources": len(relevant_chunks),
            "conversation_id": conversation_id,
            "session_id": session_id,
            "response_time_ms": response_time_ms,
            "model_used": response_data.get("model_used"),
            "used_fallback": response_data.get("used_fallback", False)
        }
    
    def get_knowledge_base_stats(self) -> Dict[str, Any]:
        kb_stats = self.vector_store.get_stats()
        conv_stats = self.conversation_logger.get_conversation_stats()
        
        # Combine stats
        combined_stats = {**kb_stats, **conv_stats}
        return combined_stats
    
    def get_conversation_history(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get conversation history for a session"""
        return self.conversation_logger.get_session_history(session_id, limit)
    
    def update_knowledge_base(self, documents_directory: str):
        logger.info(f"Updating knowledge base from directory: {documents_directory}")

        # Get chunk settings from environment
        chunk_size = int(os.getenv('CHUNK_SIZE', 512))
        chunk_overlap = int(os.getenv('CHUNK_OVERLAP', 50))
        logger.info(f"Using chunk settings: size={chunk_size} tokens, overlap={chunk_overlap} tokens")

        doc_processor = DocumentProcessor()
        text_processor = TextProcessor(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

        documents = doc_processor.process_directory(documents_directory)
        
        if not documents:
            logger.warning("No documents found to process")
            return
        
        chunks = text_processor.process_documents(documents)
        
        if not chunks:
            logger.warning("No chunks generated from documents")
            return
        
        self.vector_store.add_vectors(chunks)
        
        logger.info(f"Successfully updated knowledge base with {len(chunks)} chunks from {len(documents)} documents")