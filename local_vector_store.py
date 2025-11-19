import json
import os
from typing import List, Dict, Any
import numpy as np
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LocalVectorStore:
    def __init__(self, storage_file: str = "local_vectors.json", use_local_file: bool = True):
        self.storage_file = storage_file
        self.vectors = []
        self.use_local_file = use_local_file
        if self.use_local_file:
            self.load_vectors()

    def load_vectors(self):
        if not self.use_local_file:
            logger.info("Local file storage disabled - skipping load")
            return

        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.vectors = data.get('vectors', [])
                logger.info(f"Loaded {len(self.vectors)} vectors from {self.storage_file}")
            except Exception as e:
                logger.error(f"Error loading vectors: {str(e)}")
                self.vectors = []

    def save_vectors(self):
        if not self.use_local_file:
            logger.info("Local file storage disabled - skipping save")
            return

        try:
            data = {'vectors': self.vectors}
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(self.vectors)} vectors to {self.storage_file}")
        except Exception as e:
            logger.error(f"Error saving vectors: {str(e)}")
    
    def add_vectors(self, chunks: List[Dict[str, Any]]):
        for chunk in chunks:
            self.vectors.append(chunk)
        self.save_vectors()
        logger.info(f"Added {len(chunks)} new vectors")
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0:
            return 0
        return dot_product / (norm1 * norm2)
    
    def search_similar(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        if not self.vectors:
            return []
        
        # Calculate similarities
        similarities = []
        for i, vector_data in enumerate(self.vectors):
            if 'embedding' in vector_data:
                similarity = self.cosine_similarity(query_embedding, vector_data['embedding'])
                similarities.append((similarity, i))
        
        # Sort by similarity (descending)
        similarities.sort(reverse=True)
        
        # Return top_k results
        results = []
        for similarity, idx in similarities[:top_k]:
            result = self.vectors[idx].copy()
            result['similarity'] = similarity
            results.append(result)
        
        return results
    
    def clear_all(self):
        self.vectors = []
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)
        logger.info("Cleared all vectors")
    
    def get_stats(self) -> Dict[str, Any]:
        if not self.vectors:
            return {}
        
        files = set()
        total_tokens = 0
        
        for vector in self.vectors:
            if 'metadata' in vector:
                files.add(vector['metadata'].get('file_name', ''))
            # Convert token_count to int (may be string from Databricks)
            token_count = vector.get('token_count', 0)
            total_tokens += int(token_count) if token_count else 0
        
        return {
            'total_chunks': len(self.vectors),
            'unique_files': len(files),
            'avg_token_count': total_tokens / len(self.vectors) if self.vectors else 0,
            'last_updated': 'Local storage'
        }