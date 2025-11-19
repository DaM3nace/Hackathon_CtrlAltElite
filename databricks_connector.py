import os
from typing import List, Dict, Any, Optional
from databricks import sql
import pandas as pd
import logging
from dotenv import load_dotenv
import json

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabricksConnector:
    def __init__(self):
        self.server_hostname = os.getenv('DATABRICKS_SERVER_HOSTNAME')
        self.http_path = os.getenv('DATABRICKS_HTTP_PATH')
        self.token = os.getenv('DATABRICKS_TOKEN')
        self.catalog = os.getenv('DATABRICKS_CATALOG', 'main')
        self.schema = os.getenv('DATABRICKS_SCHEMA', 'default')
        self.vector_table = f"{self.catalog}.{self.schema}.knowledge_base_vectors"
        
        if not all([self.server_hostname, self.http_path, self.token]):
            raise ValueError("Missing required Databricks credentials in environment variables")
    
    def get_connection(self):
        try:
            connection = sql.connect(
                server_hostname=self.server_hostname,
                http_path=self.http_path,
                access_token=self.token
            )
            return connection
        except Exception as e:
            logger.error(f"Failed to connect to Databricks: {str(e)}")
            raise
    
    def create_vector_table(self):
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {self.vector_table} (
            chunk_id STRING,
            content STRING,
            embedding ARRAY<DOUBLE>,
            file_name STRING,
            file_path STRING,
            file_extension STRING,
            token_count INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
        )
        USING DELTA
        TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true')
        """
        
        try:
            with self.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(create_table_sql)
                    logger.info(f"Vector table {self.vector_table} created or already exists")
        except Exception as e:
            logger.error(f"Error creating vector table: {str(e)}")
            raise
    
    def insert_vectors(self, chunks: List[Dict[str, Any]]):
        if not chunks:
            logger.warning("No chunks to insert")
            return
        
        insert_sql = f"""
        INSERT INTO {self.vector_table} 
        (chunk_id, content, embedding, file_name, file_path, file_extension, token_count)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        try:
            with self.get_connection() as connection:
                with connection.cursor() as cursor:
                    for chunk in chunks:
                        cursor.execute(insert_sql, (
                            chunk['chunk_id'],
                            chunk['content'],
                            chunk['embedding'],
                            chunk['metadata']['file_name'],
                            chunk['metadata']['file_path'],
                            chunk['metadata']['file_extension'],
                            chunk['token_count']
                        ))
                    
                    logger.info(f"Inserted {len(chunks)} vectors into {self.vector_table}")
        except Exception as e:
            logger.error(f"Error inserting vectors: {str(e)}")
            raise
    
    def search_similar_vectors(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        search_sql = f"""
        SELECT 
            chunk_id,
            content,
            file_name,
            file_path,
            file_extension,
            ai.dot_product(embedding, array({','.join(map(str, query_embedding))})) as similarity
        FROM {self.vector_table}
        ORDER BY similarity DESC
        LIMIT {top_k}
        """
        
        try:
            with self.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(search_sql)
                    results = cursor.fetchall()
                    
                    columns = [desc[0] for desc in cursor.description]
                    return [dict(zip(columns, row)) for row in results]
        except Exception as e:
            logger.error(f"Error searching vectors: {str(e)}")
            return []
    
    def get_table_stats(self) -> Dict[str, Any]:
        stats_sql = f"""
        SELECT 
            COUNT(*) as total_chunks,
            COUNT(DISTINCT file_name) as unique_files,
            AVG(token_count) as avg_token_count,
            MAX(created_at) as last_updated
        FROM {self.vector_table}
        """
        
        try:
            with self.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(stats_sql)
                    result = cursor.fetchone()
                    columns = [desc[0] for desc in cursor.description]
                    return dict(zip(columns, result)) if result else {}
        except Exception as e:
            logger.error(f"Error getting table stats: {str(e)}")
            return {}
    
    def delete_file_vectors(self, file_name: str):
        delete_sql = f"DELETE FROM {self.vector_table} WHERE file_name = ?"
        
        try:
            with self.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(delete_sql, (file_name,))
                    logger.info(f"Deleted vectors for file: {file_name}")
        except Exception as e:
            logger.error(f"Error deleting vectors for file {file_name}: {str(e)}")
            raise
    
    def clear_all_vectors(self):
        try:
            with self.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(f"DELETE FROM {self.vector_table}")
                    logger.info("Cleared all vectors from the table")
        except Exception as e:
            logger.error(f"Error clearing vectors: {str(e)}")
            raise