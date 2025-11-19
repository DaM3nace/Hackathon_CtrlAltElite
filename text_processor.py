import tiktoken
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TextProcessor:
    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50, model_name: str = "all-MiniLM-L6-v2"):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
        self.embedding_model = SentenceTransformer(model_name)
        
    def count_tokens(self, text: str) -> int:
        return len(self.encoding.encode(text))
    
    def chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        if not text.strip():
            return []
        
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""
        current_tokens = 0
        
        for paragraph in paragraphs:
            paragraph_tokens = self.count_tokens(paragraph)
            
            if current_tokens + paragraph_tokens <= self.chunk_size:
                current_chunk += paragraph + "\n\n"
                current_tokens += paragraph_tokens
            else:
                if current_chunk.strip():
                    chunks.append({
                        'content': current_chunk.strip(),
                        'metadata': metadata.copy(),
                        'token_count': current_tokens
                    })
                
                if paragraph_tokens <= self.chunk_size:
                    current_chunk = paragraph + "\n\n"
                    current_tokens = paragraph_tokens
                else:
                    sub_chunks = self._split_long_paragraph(paragraph, metadata)
                    chunks.extend(sub_chunks)
                    current_chunk = ""
                    current_tokens = 0
        
        if current_chunk.strip():
            chunks.append({
                'content': current_chunk.strip(),
                'metadata': metadata.copy(),
                'token_count': current_tokens
            })
        
        return chunks
    
    def _split_long_paragraph(self, paragraph: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        sentences = paragraph.split('. ')
        chunks = []
        current_chunk = ""
        current_tokens = 0
        
        for sentence in sentences:
            sentence = sentence.strip() + '. ' if not sentence.endswith('.') else sentence + ' '
            sentence_tokens = self.count_tokens(sentence)
            
            if current_tokens + sentence_tokens <= self.chunk_size:
                current_chunk += sentence
                current_tokens += sentence_tokens
            else:
                if current_chunk.strip():
                    chunks.append({
                        'content': current_chunk.strip(),
                        'metadata': metadata.copy(),
                        'token_count': current_tokens
                    })
                
                current_chunk = sentence
                current_tokens = sentence_tokens
        
        if current_chunk.strip():
            chunks.append({
                'content': current_chunk.strip(),
                'metadata': metadata.copy(),
                'token_count': current_tokens
            })
        
        return chunks
    
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        try:
            embeddings = self.embedding_model.encode(texts, convert_to_tensor=False)
            logger.info(f"Generated embeddings for {len(texts)} text chunks")
            return embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            return np.array([])
    
    def process_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        all_chunks = []
        
        for doc in documents:
            if not doc.get('content'):
                continue
                
            metadata = {
                'file_name': doc['file_name'],
                'file_path': doc['file_path'],
                'file_extension': doc['file_extension']
            }
            
            chunks = self.chunk_text(doc['content'], metadata)
            all_chunks.extend(chunks)
        
        if not all_chunks:
            logger.warning("No chunks generated from documents")
            return []
        
        texts = [chunk['content'] for chunk in all_chunks]
        embeddings = self.generate_embeddings(texts)
        
        if len(embeddings) > 0:
            for i, chunk in enumerate(all_chunks):
                chunk['embedding'] = embeddings[i].tolist()
                chunk['chunk_id'] = f"{chunk['metadata']['file_name']}_{i}"
        
        logger.info(f"Processed {len(all_chunks)} chunks with embeddings")
        return all_chunks