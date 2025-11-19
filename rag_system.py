import os
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import openai
from databricks_connector import DatabricksConnector
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGSystem:
    def __init__(self, embedding_model_name: str = "all-MiniLM-L6-v2"):
        self.embedding_model = SentenceTransformer(embedding_model_name)
        self.db_connector = DatabricksConnector()
        
        openai.api_key = os.getenv('OPENAI_API_KEY')
        if not openai.api_key:
            logger.warning("OpenAI API key not found. Using fallback response generation.")
        
        self.system_prompt = """You are a helpful assistant that answers questions based on the provided context from a knowledge base.
        
Instructions:
- Use only the information provided in the context to answer questions
- If the context doesn't contain enough information to answer the question, say so clearly
- Provide specific references to source documents when possible
- Be concise but comprehensive in your responses
- If asked about something not in the context, politely explain that you can only answer based on the provided documents
        """
    
    def generate_query_embedding(self, query: str) -> List[float]:
        try:
            embedding = self.embedding_model.encode([query])[0]
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating query embedding: {str(e)}")
            return []
    
    def retrieve_relevant_chunks(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        query_embedding = self.generate_query_embedding(query)
        
        if not query_embedding:
            return []
        
        try:
            results = self.db_connector.search_similar_vectors(query_embedding, top_k)
            logger.info(f"Retrieved {len(results)} relevant chunks for query")
            return results
        except Exception as e:
            logger.error(f"Error retrieving chunks: {str(e)}")
            return []
    
    def format_context(self, chunks: List[Dict[str, Any]]) -> str:
        if not chunks:
            return "No relevant information found in the knowledge base."
        
        context = "Context from knowledge base:\n\n"
        
        for i, chunk in enumerate(chunks, 1):
            context += f"Document {i}: {chunk['file_name']}\n"
            context += f"Content: {chunk['content']}\n"
            context += f"Similarity: {chunk.get('similarity', 'N/A')}\n\n"
        
        return context
    
    def generate_response(self, query: str, context: str) -> str:
        if not openai.api_key:
            return self._fallback_response(query, context)
        
        try:
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
            ]
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=500,
                temperature=0.1
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error generating response with OpenAI: {str(e)}")
            return self._fallback_response(query, context)
    
    def _fallback_response(self, query: str, context: str) -> str:
        if "No relevant information found" in context:
            return "I couldn't find relevant information in the knowledge base to answer your question."
        
        return f"Based on the available documents, here's the relevant information I found:\n\n{context}\n\nPlease note: This is a direct excerpt from the knowledge base. For a more comprehensive answer, please configure OpenAI API access."
    
    def ask_question(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        logger.info(f"Processing query: {query}")
        
        relevant_chunks = self.retrieve_relevant_chunks(query, top_k)
        context = self.format_context(relevant_chunks)
        response = self.generate_response(query, context)
        
        return {
            "query": query,
            "response": response,
            "context": context,
            "sources": [
                {
                    "file_name": chunk["file_name"],
                    "file_path": chunk["file_path"],
                    "similarity": chunk.get("similarity", "N/A")
                }
                for chunk in relevant_chunks
            ],
            "num_sources": len(relevant_chunks)
        }
    
    def get_knowledge_base_stats(self) -> Dict[str, Any]:
        return self.db_connector.get_table_stats()
    
    def update_knowledge_base(self, documents_directory: str):
        from document_processor import DocumentProcessor
        from text_processor import TextProcessor
        
        logger.info(f"Updating knowledge base from directory: {documents_directory}")
        
        doc_processor = DocumentProcessor()
        text_processor = TextProcessor()
        
        documents = doc_processor.process_directory(documents_directory)
        
        if not documents:
            logger.warning("No documents found to process")
            return
        
        chunks = text_processor.process_documents(documents)
        
        if not chunks:
            logger.warning("No chunks generated from documents")
            return
        
        self.db_connector.create_vector_table()
        self.db_connector.insert_vectors(chunks)
        
        logger.info(f"Successfully updated knowledge base with {len(chunks)} chunks from {len(documents)} documents")