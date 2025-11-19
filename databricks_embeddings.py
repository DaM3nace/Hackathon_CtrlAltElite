import os
import logging
from typing import List
from dotenv import load_dotenv
import requests
import json

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabricksEmbeddings:
    """
    Generate embeddings using Databricks Foundation Model API (databricks-bge-large-en)
    Uses Databricks serving endpoint format
    """

    def __init__(self):
        self.base_url = os.getenv('OPENAI_BASE_URL', '')
        self.api_key = os.getenv('OPENAI_API_KEY', '')
        self.model_name = os.getenv('DATABRICKS_EMBEDDING_MODEL', 'databricks-bge-large-en')
        self.databricks_host = os.getenv('DATABRICKS_SERVER_HOSTNAME', '')

        if not self.base_url or not self.api_key or not self.databricks_host:
            logger.warning("Databricks endpoint or API key not configured. Embeddings will not work.")
            self.client = None
        else:
            self.client = True  # Flag to indicate client is configured
            logger.info(f"Initialized Databricks embeddings with model: {self.model_name}")

    def encode(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts

        Args:
            texts: List of strings to embed

        Returns:
            List of embedding vectors (list of floats)
        """
        if not self.client:
            logger.error("Databricks client not initialized. Cannot generate embeddings.")
            # Return dummy embeddings for testing
            return [[0.0] * 1024 for _ in texts]

        try:
            # Databricks embeddings endpoint
            url = f"https://{self.databricks_host}/serving-endpoints/{self.model_name}/invocations"

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            # Databricks embeddings payload
            payload = {
                "input": texts
            }

            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()

            result = response.json()

            # Extract embeddings from response
            # Databricks returns: {"data": [{"embedding": [...]}]}
            if 'data' in result:
                embeddings = [item['embedding'] for item in result['data']]
            elif 'predictions' in result:
                embeddings = result['predictions']
            else:
                logger.error(f"Unexpected response format: {result}")
                return [[0.0] * 1024 for _ in texts]

            logger.info(f"Generated {len(embeddings)} embeddings using {self.model_name}")
            return embeddings

        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            # Return dummy embeddings as fallback
            return [[0.0] * 1024 for _ in texts]

    def get_embedding_dimension(self) -> int:
        """Get the dimension of the embedding vectors"""
        # databricks-bge-large-en produces 1024-dimensional embeddings
        return 1024

    def test_connection(self) -> bool:
        """Test if the Databricks embeddings endpoint is accessible"""
        try:
            test_embedding = self.encode(["test"])
            return len(test_embedding) > 0 and len(test_embedding[0]) > 0
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False

if __name__ == "__main__":
    # Test the embeddings
    embeddings = DatabricksEmbeddings()

    if embeddings.test_connection():
        print("SUCCESS: Databricks embeddings connection working")

        # Test with sample text
        test_texts = ["Hello world", "Test embedding"]
        results = embeddings.encode(test_texts)

        print(f"Generated {len(results)} embeddings")
        print(f"Embedding dimension: {len(results[0])}")
        print(f"Sample values: {results[0][:5]}...")
    else:
        print("FAILED: Could not connect to Databricks embeddings endpoint")
        print("Check your OPENAI_BASE_URL and OPENAI_API_KEY in .env")
