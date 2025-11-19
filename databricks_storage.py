"""
Databricks Storage Module for Documents and Chunks
Handles storing and retrieving documents, chunks, and vectors from Databricks tables
"""
import os
import json
import hashlib
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv
import requests

# Don't load .env here - let parent module handle it
# This allows parent to set environment variables before importing this module
# load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabricksStorage:
    """
    Manages document and chunk storage in Databricks tables
    """

    def __init__(self):
        self.server_hostname = os.getenv('DATABRICKS_SERVER_HOSTNAME')
        self.http_path = os.getenv('DATABRICKS_HTTP_PATH')
        self.token = os.getenv('DATABRICKS_TOKEN')
        self.catalog = os.getenv('DATABRICKS_CATALOG', 'hackathon')
        self.schema = os.getenv('DATABRICKS_SCHEMA', 'hackathon_ctrl_alt_elite')

        # Table names
        self.documents_table = f"{self.catalog}.{self.schema}.{os.getenv('DOCUMENTS_TABLE', 'DG_DOCUMENTS')}"
        self.chunks_table = f"{self.catalog}.{self.schema}.{os.getenv('CHUNKS_TABLE', 'DG_CHUNKS')}"
        self.vectors_table = f"{self.catalog}.{self.schema}.{os.getenv('VECTORS_TABLE', 'DG_VECTORS')}"

        self.api_url = f"https://{self.server_hostname}/api/2.0/sql/statements"

        logger.info(f"Initialized Databricks storage")
        logger.info(f"  Documents: {self.documents_table}")
        logger.info(f"  Chunks: {self.chunks_table}")
        logger.info(f"  Vectors: {self.vectors_table}")

    def execute_sql(self, sql_query: str, wait_timeout: str = "30s") -> Dict[str, Any]:
        """Execute SQL query via Databricks SQL API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }

            payload = {
                "statement": sql_query,
                "warehouse_id": self.http_path.split('/')[-1],
                "wait_timeout": wait_timeout
            }

            response = requests.post(self.api_url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()

            result = response.json()
            return result

        except Exception as e:
            logger.error(f"Error executing SQL: {str(e)}")
            return {"status": "error", "message": str(e)}

    def generate_document_id(self, file_name: str, content: str) -> str:
        """Generate unique document ID based on filename and content hash"""
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        return f"doc_{content_hash}"

    def generate_chunk_id(self, document_id: str, chunk_index: int) -> str:
        """Generate unique chunk ID"""
        return f"{document_id}_chunk_{chunk_index}"

    def calculate_content_hash(self, content: str) -> str:
        """Calculate SHA-256 hash of content"""
        return hashlib.sha256(content.encode()).hexdigest()

    def save_document(self, document: Dict[str, Any]) -> bool:
        """Save document to Databricks"""
        try:
            document_id = self.generate_document_id(
                document['file_name'],
                document['content']
            )

            content_hash = self.calculate_content_hash(document['content'])

            # Escape single quotes in content
            content = document['content'].replace("'", "''")
            file_name = document['file_name'].replace("'", "''")
            file_path = document.get('file_path', '').replace("'", "''")

            sql = f"""
            INSERT INTO {self.documents_table}
            (document_id, file_name, file_path, file_extension, file_size, content, content_hash, status)
            VALUES
            ('{document_id}',
             '{file_name}',
             '{file_path}',
             '{document.get('file_extension', '')}',
             {document.get('file_size', 0)},
             '{content}',
             '{content_hash}',
             'active')
            """

            result = self.execute_sql(sql)

            if result.get('status') != 'error':
                logger.info(f"Saved document: {document['file_name']}")
                return True
            else:
                logger.error(f"Failed to save document: {result.get('message')}")
                return False

        except Exception as e:
            logger.error(f"Error saving document: {str(e)}")
            return False

    def save_chunks(self, chunks: List[Dict[str, Any]], document_id: str) -> bool:
        """Save chunks to Databricks"""
        try:
            for i, chunk in enumerate(chunks):
                chunk_id = self.generate_chunk_id(document_id, i)

                # Escape single quotes
                content = chunk['content'].replace("'", "''")
                file_name = chunk['metadata']['file_name'].replace("'", "''")

                # Convert embedding to JSON string
                embedding_json = json.dumps(chunk.get('embedding', [])).replace("'", "''")

                sql = f"""
                INSERT INTO {self.chunks_table}
                (chunk_id, document_id, chunk_index, content, content_length, token_count,
                 embedding, embedding_model, embedding_dimension, file_name, file_extension)
                VALUES
                ('{chunk_id}',
                 '{document_id}',
                 {i},
                 '{content}',
                 {len(chunk['content'])},
                 {chunk.get('token_count', 0)},
                 '{embedding_json}',
                 'all-MiniLM-L6-v2',
                 {len(chunk.get('embedding', []))},
                 '{file_name}',
                 '{chunk['metadata'].get('file_extension', '')}')
                """

                result = self.execute_sql(sql)

                if result.get('status') == 'error':
                    logger.error(f"Failed to save chunk {i}: {result.get('message')}")
                    return False

            # Also save to vectors table for fast retrieval
            self.save_vectors(chunks, document_id)

            logger.info(f"Saved {len(chunks)} chunks for document {document_id}")
            return True

        except Exception as e:
            logger.error(f"Error saving chunks: {str(e)}")
            return False

    def save_vectors(self, chunks: List[Dict[str, Any]], document_id: str) -> bool:
        """Save vectors to optimized search table"""
        try:
            for i, chunk in enumerate(chunks):
                chunk_id = self.generate_chunk_id(document_id, i)
                vector_id = chunk_id

                content = chunk['content'].replace("'", "''")
                file_name = chunk['metadata']['file_name'].replace("'", "''")
                embedding_json = json.dumps(chunk.get('embedding', [])).replace("'", "''")

                sql = f"""
                INSERT INTO {self.vectors_table}
                (vector_id, chunk_id, document_id, content, embedding, embedding_dimension,
                 file_name, file_extension, token_count)
                VALUES
                ('{vector_id}',
                 '{chunk_id}',
                 '{document_id}',
                 '{content}',
                 '{embedding_json}',
                 {len(chunk.get('embedding', []))},
                 '{file_name}',
                 '{chunk['metadata'].get('file_extension', '')}',
                 {chunk.get('token_count', 0)})
                """

                result = self.execute_sql(sql)

                if result.get('status') == 'error':
                    logger.error(f"Failed to save vector {i}: {result.get('message')}")
                    return False

            logger.info(f"Saved {len(chunks)} vectors for document {document_id}")
            return True

        except Exception as e:
            logger.error(f"Error saving vectors: {str(e)}")
            return False

    def load_all_vectors(self) -> List[Dict[str, Any]]:
        """Load all vectors from Databricks"""
        try:
            sql = f"""
            SELECT
                vector_id,
                chunk_id,
                document_id,
                content,
                embedding,
                embedding_dimension,
                file_name,
                file_extension,
                token_count,
                created_timestamp
            FROM {self.vectors_table}
            ORDER BY created_timestamp DESC
            """

            result = self.execute_sql(sql)

            if result.get('status') == 'error':
                logger.error(f"Failed to load vectors: {result.get('message')}")
                return []

            # Parse result
            vectors = []
            if 'result' in result and 'data_array' in result['result']:
                for row in result['result']['data_array']:
                    vector = {
                        'chunk_id': row[1],
                        'content': row[3],
                        'embedding': json.loads(row[4]) if row[4] else [],
                        'metadata': {
                            'file_name': row[6],
                            'file_extension': row[7]
                        },
                        'token_count': row[8]
                    }
                    vectors.append(vector)

            logger.info(f"Loaded {len(vectors)} vectors from Databricks")
            return vectors

        except Exception as e:
            logger.error(f"Error loading vectors: {str(e)}")
            return []

    def get_document_count(self) -> int:
        """Get count of active documents"""
        try:
            sql = f"SELECT COUNT(*) FROM {self.documents_table} WHERE status = 'active'"
            result = self.execute_sql(sql)

            if 'result' in result and 'data_array' in result['result']:
                count = result['result']['data_array'][0][0]
                return int(count) if count is not None else 0

            return 0

        except Exception as e:
            logger.error(f"Error getting document count: {str(e)}")
            return 0

    def get_chunk_count(self) -> int:
        """Get count of chunks"""
        try:
            sql = f"SELECT COUNT(*) FROM {self.chunks_table}"
            result = self.execute_sql(sql)

            if 'result' in result and 'data_array' in result['result']:
                count = result['result']['data_array'][0][0]
                return int(count) if count is not None else 0

            return 0

        except Exception as e:
            logger.error(f"Error getting chunk count: {str(e)}")
            return 0

    def clear_all_data(self) -> bool:
        """Clear all data from storage tables"""
        try:
            logger.warning("Clearing all data from Databricks storage tables")

            # Delete in reverse order of dependencies
            for table in [self.vectors_table, self.chunks_table, self.documents_table]:
                sql = f"DELETE FROM {table}"
                result = self.execute_sql(sql)

                if result.get('status') == 'error':
                    logger.error(f"Failed to clear {table}: {result.get('message')}")
                    return False

            logger.info("Cleared all data from Databricks storage")
            return True

        except Exception as e:
            logger.error(f"Error clearing data: {str(e)}")
            return False


if __name__ == "__main__":
    # Test Databricks storage
    storage = DatabricksStorage()

    print("\nDatabricks Storage Test")
    print("=" * 60)

    # Test document count
    doc_count = storage.get_document_count()
    chunk_count = storage.get_chunk_count()

    print(f"Current Documents: {doc_count}")
    print(f"Current Chunks: {chunk_count}")

    # Test saving a document
    test_doc = {
        'file_name': 'test_document.txt',
        'file_path': '/test/test_document.txt',
        'file_extension': '.txt',
        'file_size': 100,
        'content': 'This is a test document for Databricks storage.'
    }

    print("\nTesting document save...")
    if storage.save_document(test_doc):
        print("SUCCESS: Document saved")
    else:
        print("FAILED: Could not save document")

    print("\n" + "=" * 60)
