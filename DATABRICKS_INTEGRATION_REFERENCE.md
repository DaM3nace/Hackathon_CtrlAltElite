# Complete Databricks Integration Reference Guide
## For LLM (GPT-5) and RAG Systems

**Version**: 1.0  
**Date**: November 17, 2025  
**Status**: Production-Tested ✅  
**Source**: Working implementation from Frontier AI Assistant

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Configuration Setup](#configuration-setup)
4. [LLM Integration (GPT-5)](#llm-integration-gpt-5)
5. [RAG Integration](#rag-integration)
6. [Critical Fixes & Gotchas](#critical-fixes--gotchas)
7. [Testing & Verification](#testing--verification)
8. [Troubleshooting](#troubleshooting)
9. [Quick Start Checklist](#quick-start-checklist)

---

## Overview

This guide provides everything needed to integrate Databricks as both an LLM provider (GPT-5) and RAG backend into any chatbot project, replacing traditional providers like OpenAI or Anthropic and local storage like SQLite.

### What This Integration Provides

- **LLM**: GPT-5 via Databricks serving endpoints
- **RAG Storage**: Databricks tables (documents, chunks, embeddings)
- **Document Storage**: Databricks Volumes (optional)
- **Embeddings**: GPT-5 or Databricks embedding models
- **Search**: Hybrid (FTS + vector similarity)

### Architecture

```
┌─────────────────┐
│   Your App      │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼──────────┐
│ GPT-5 │ │ Databricks  │
│  LLM  │ │  RAG System │
└───────┘ └──┬──────────┘
             │
    ┌────────┴────────┐
    │                 │
┌───▼────┐    ┌──────▼──────┐
│ Tables │    │   Volumes   │
│ (Meta) │    │ (Documents) │
└────────┘    └─────────────┘
```

---

## Prerequisites

### 1. Databricks Account Setup

**Required Information**:
- Workspace URL: `your-workspace.cloud.databricks.com`
- Personal Access Token (PAT)
- SQL Warehouse HTTP path
- Catalog and schema names

**Get Your Credentials**:

1. **Host**: From your Databricks workspace URL
   ```
   https://dbc-858eb1c5-0fa9.cloud.databricks.com
   → Extract: dbc-858eb1c5-0fa9.cloud.databricks.com
   ```

2. **Token**: User Settings → Developer → Access Tokens → Generate New Token

3. **HTTP Path**: SQL Warehouses → Your Warehouse → Connection Details
   ```
   Example: /sql/1.0/warehouses/7b2c2e50d3c1dd61
   ```

4. **Catalog/Schema**: Use existing or create new
   ```sql
   CREATE CATALOG IF NOT EXISTS field;
   CREATE SCHEMA IF NOT EXISTS field.user_data_enrique;
   ```

### 2. Required Python Packages

Add to your `requirements.txt`:

```txt
# Databricks Connection
databricks-sql-connector>=3.0.0

# LLM Access (for Databricks GPT-5)
openai>=1.0.0

# Configuration
python-dotenv>=0.19.0

# Optional: For better performance
pyarrow>=10.0.0
```

Install:
```bash
pip install -r requirements.txt
```

---

## Configuration Setup

### Step 1: Environment Variables

Create or update your `.env` file:

```bash
# ==============================================
# Databricks Connection
# ==============================================
DATABRICKS_HOST=dbc-858eb1c5-0fa9.cloud.databricks.com
DATABRICKS_TOKEN=dapi...your-personal-access-token...
DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/7b2c2e50d3c1dd61

# ==============================================
# Databricks Database
# ==============================================
DATABRICKS_CATALOG=hackthon
DATABRICKS_SCHEMA=hackathon_

# ==============================================
# LLM Configuration
# ==============================================
LLM_PROVIDER=databricks
LLM_MODEL=databricks-gpt-5

# ==============================================
# RAG Configuration (Optional)
# ==============================================
ENABLE_RAG=true
RAG_TOP_K=5
RAG_FTS_WEIGHT=0.4

# ==============================================
# Legacy Keys (Keep for Rollback)
# ==============================================
# ANTHROPIC_API_KEY=sk-ant-...
# OPENAI_API_KEY=sk-...
```

### Step 2: Configuration Module

Create `databricks_config.py` in your project root:

```python
"""
Databricks Configuration Management

Handles Databricks connection configuration using environment variables.
Provides validation and connection parameter generation.
"""

import os
from typing import Dict, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class DatabricksConfig:
    """Databricks connection configuration"""
    
    def __init__(self):
        """Initialize configuration from environment variables"""
        self.host = os.getenv('DATABRICKS_HOST')
        self.token = os.getenv('DATABRICKS_TOKEN')
        self.http_path = os.getenv('DATABRICKS_HTTP_PATH')
        self.catalog = os.getenv('DATABRICKS_CATALOG', 'hive_metastore')
        self.schema = os.getenv('DATABRICKS_SCHEMA', 'default')
        
        # Optional: Volume configuration
        self.volume = os.getenv('DATABRICKS_VOLUME', 'sop_documents')
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """
        Validate that all required configuration is present.
        
        Returns:
            tuple: (is_valid, error_message)
        """
        if not self.host:
            return False, "DATABRICKS_HOST environment variable is not set"
        
        if not self.token:
            return False, "DATABRICKS_TOKEN environment variable is not set"
        
        if not self.http_path:
            return False, "DATABRICKS_HTTP_PATH environment variable is not set"
        
        # Validate host format
        valid_suffixes = [
            '.cloud.databricks.com',
            '.azuredatabricks.net',
            '.gcp.databricks.com'
        ]
        if not any(self.host.endswith(suffix) for suffix in valid_suffixes):
            return False, f"Invalid DATABRICKS_HOST format: {self.host}"
        
        # Validate http_path format
        if not self.http_path.startswith('/sql/'):
            return False, f"Invalid DATABRICKS_HTTP_PATH format: {self.http_path}"
        
        return True, None
    
    def get_connection_params(self) -> Dict[str, str]:
        """
        Get connection parameters for databricks-sql-connector.
        
        Returns:
            dict: Connection parameters ready for sql.connect()
        """
        return {
            'server_hostname': self.host,
            'http_path': self.http_path,
            'access_token': self.token,
            'catalog': self.catalog,
            'schema': self.schema
        }
    
    def get_volume_path(self, filename: str = '') -> str:
        """
        Get full Databricks Volume path.
        
        Args:
            filename: Optional filename to append
        
        Returns:
            str: Full volume path
        """
        base_path = f"/Volumes/{self.catalog}/{self.schema}/{self.volume}"
        if filename:
            return f"{base_path}/{filename}"
        return base_path
    
    def __repr__(self) -> str:
        """String representation (hiding sensitive data)"""
        return (
            f"DatabricksConfig("
            f"host={self.host}, "
            f"http_path={self.http_path}, "
            f"token={'*' * 10 if self.token else None}, "
            f"catalog={self.catalog}, "
            f"schema={self.schema})"
        )


def get_config() -> DatabricksConfig:
    """
    Get Databricks configuration.
    
    Returns:
        DatabricksConfig: Configuration object
    """
    return DatabricksConfig()


def check_config() -> bool:
    """
    Check if Databricks configuration is valid.
    Prints helpful error messages if invalid.
    
    Returns:
        bool: True if valid, False otherwise
    """
    config = get_config()
    is_valid, error = config.validate()
    
    if not is_valid:
        print(f"❌ Configuration error: {error}")
        print("\nPlease set the following environment variables in .env:")
        print("  DATABRICKS_HOST=your-workspace.cloud.databricks.com")
        print("  DATABRICKS_TOKEN=your-personal-access-token")
        print("  DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/your-warehouse-id")
        print("\nOptional:")
        print("  DATABRICKS_CATALOG=hive_metastore (default)")
        print("  DATABRICKS_SCHEMA=default (default)")
        return False
    
    print("✅ Databricks configuration is valid")
    return True


if __name__ == '__main__':
    """Test configuration when run directly"""
    print("=== Databricks Configuration Test ===\n")
    
    config = get_config()
    print(f"Configuration: {config}\n")
    
    is_valid, error = config.validate()
    
    if is_valid:
        print("✓ Configuration is valid!")
        print("\nConnection parameters:")
        params = config.get_connection_params()
        for key, value in params.items():
            if key == 'access_token':
                print(f"  {key}: {'*' * 20}")
            else:
                print(f"  {key}: {value}")
    else:
        print(f"✗ Configuration error: {error}")
        print("\nPlease check your environment variables.")
```

### Step 3: Application Config

Update your `config.py`:

```python
"""Configuration for the chatbot agent"""

# ==============================================
# LLM Provider Configuration
# ==============================================
LLM_PROVIDER = "databricks"  # Options: "openai", "anthropic", "databricks"

# ==============================================
# API Keys (use .env file for sensitive data)
# ==============================================
OPENAI_API_KEY = ""      # Not used when using Databricks
ANTHROPIC_API_KEY = ""   # Backup if needed
DATABRICKS_TOKEN = ""    # Set in .env file

# ==============================================
# Model Configuration
# ==============================================
OPENAI_MODEL = "gpt-4-turbo-preview"
ANTHROPIC_MODEL = "claude-sonnet-4-20250514"
DATABRICKS_MODEL = "databricks-gpt-5"  # GPT-5 via Databricks

# ==============================================
# Chatbot Configuration
# ==============================================
CHATBOT_NAME = "Your Bot Name"
CHATBOT_DESCRIPTION = "An AI assistant"

# ==============================================
# LLM Parameters
# ==============================================
# NOTE: GPT-5 via Databricks only supports default temperature (1.0)
# The temperature parameter will be ignored for Databricks provider
TEMPERATURE = 0.7
MAX_TOKENS = 2000

# ==============================================
# RAG Configuration
# ==============================================
ENABLE_RAG = True
RAG_TOP_K = 5
```

---

## LLM Integration (GPT-5)

### Step 1: Update LLM Provider Enum

In `utils/llm_client.py`, add Databricks to your provider enum:

```python
from enum import Enum

class LLMProvider(Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    DATABRICKS = "databricks"  # ✨ ADD THIS
    LOCAL = "local"
```

### Step 2: Update API Key Retrieval

```python
def _get_api_key_from_env(self) -> Optional[str]:
    """Get API key from environment variables."""
    if self.provider == LLMProvider.OPENAI:
        return os.getenv("OPENAI_API_KEY")
    elif self.provider == LLMProvider.ANTHROPIC:
        return os.getenv("ANTHROPIC_API_KEY")
    elif self.provider == LLMProvider.DATABRICKS:
        return os.getenv("DATABRICKS_TOKEN")  # ✨ ADD THIS
    return None
```

### Step 3: Update Default Model

```python
def _get_default_model(self) -> str:
    """Get default model for the provider."""
    if self.provider == LLMProvider.OPENAI:
        return "gpt-4-turbo-preview"
    elif self.provider == LLMProvider.ANTHROPIC:
        return "claude-3-sonnet-20240229"
    elif self.provider == LLMProvider.DATABRICKS:
        return "databricks-gpt-5"  # ✨ ADD THIS
    return "local-model"
```

### Step 4: Initialize Databricks Client

```python
def _initialize_client(self) -> Any:
    """Initialize the appropriate client based on provider."""
    
    # ... existing OpenAI/Anthropic code ...
    
    elif self.provider == LLMProvider.DATABRICKS:
        try:
            if not self.api_key:
                print("ℹ️  No Databricks token found - using mock responses")
                return None
            
            databricks_host = os.getenv("DATABRICKS_HOST")
            if not databricks_host:
                print("ℹ️  No DATABRICKS_HOST found - using mock responses")
                return None
            
            # Use OpenAI SDK with Databricks endpoint
            from openai import OpenAI
            return OpenAI(
                api_key=self.api_key,
                base_url=f"https://{databricks_host}/serving-endpoints"
            )
        except ImportError:
            print("Warning: OpenAI package not installed (needed for Databricks)")
            return None
        except Exception as e:
            print(f"Warning: Could not initialize Databricks client: {e}")
            return None
    
    return None
```

### Step 5: Update Chat Method

**⚠️ CRITICAL**: This is where the most important fix is needed!

```python
def chat(self, messages: List[Dict[str, str]], 
         temperature: float = 0.7,
         max_tokens: int = 2000,
         tools: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """
    Send chat messages to the LLM.
    
    Args:
        messages: List of message dictionaries
        temperature: Temperature (ignored for Databricks)
        max_tokens: Maximum tokens in response
        tools: Optional tool definitions
    
    Returns:
        dict: Response with 'content' key
    """
    
    if not self.client:
        return {"content": self._mock_response()}
    
    try:
        # ... existing OpenAI/Anthropic code ...
        
        elif self.provider == LLMProvider.DATABRICKS:
            # ⚠️ CRITICAL FIX: Databricks GPT-5 does NOT support temperature parameter!
            # Only default temperature (1.0) is supported
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                # temperature=temperature,  # ❌ DO NOT INCLUDE THIS
                max_tokens=max_tokens
            )
            
            # Debug output (optional but helpful)
            print(f"\n🤖 [Databricks GPT-5 API Call]")
            print(f"   Model: {self.model}")
            print(f"   Messages: {len(messages)}")
            print(f"   Temperature: default (1.0)")
            print(f"   Max tokens: {max_tokens}")
            
            content = response.choices[0].message.content
            
            print(f"\n✓ [Databricks Response]")
            print(f"   Response length: {len(content)} chars")
            
            return {"content": content}
        
        # ... rest of code ...
    
    except Exception as e:
        print(f"Error calling LLM: {e}")
        import traceback
        traceback.print_exc()
        return {"content": "I'm sorry, I'm having trouble processing that right now."}
```

---

## RAG Integration

### Part 1: Databricks RAG Manager

Create `database/databricks_rag_manager.py`:

```python
"""
Databricks RAG Manager

Manages Databricks tables for RAG system:
- documents: Document metadata
- chunks: Text chunks from documents
- embeddings: Vector embeddings for chunks

Also handles Databricks Volume operations for document storage.
"""

from databricks import sql
import json
from typing import List, Dict, Optional
from datetime import datetime
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from databricks_config import DatabricksConfig


class DatabricksRAGManager:
    """Manages Databricks tables and Volume for RAG system"""
    
    def __init__(self, config: DatabricksConfig):
        """
        Initialize RAG manager.
        
        Args:
            config: DatabricksConfig instance
        """
        self.config = config
        self.connection = None
        self.cursor = None
        
        # Table names with full catalog.schema qualification
        self.documents_table = f"{config.catalog}.{config.schema}.documents"
        self.chunks_table = f"{config.catalog}.{config.schema}.chunks"
        self.embeddings_table = f"{config.catalog}.{config.schema}.embeddings"
    
    def connect(self) -> bool:
        """
        Connect to Databricks.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            conn_params = self.config.get_connection_params()
            self.connection = sql.connect(**conn_params)
            self.cursor = self.connection.cursor()
            return True
        except Exception as e:
            print(f"Error connecting to Databricks: {e}")
            return False
    
    def disconnect(self):
        """Close Databricks connection"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
    
    def create_tables(self):
        """Create RAG tables if they don't exist"""
        
        # Documents table
        documents_sql = f"""
        CREATE TABLE IF NOT EXISTS {self.documents_table} (
            id STRING,
            filename STRING,
            volume_path STRING,
            file_type STRING,
            file_size BIGINT,
            status STRING,
            last_modified TIMESTAMP,
            PRIMARY KEY(id)
        )
        COMMENT 'RAG document metadata'
        """
        
        # Chunks table
        chunks_sql = f"""
        CREATE TABLE IF NOT EXISTS {self.chunks_table} (
            id STRING,
            document_id STRING,
            chunk_index INT,
            text STRING,
            token_count INT,
            created_at TIMESTAMP,
            PRIMARY KEY(id),
            FOREIGN KEY(document_id) REFERENCES {self.documents_table}(id)
        )
        COMMENT 'Document text chunks for RAG'
        """
        
        # Embeddings table
        # ⚠️ CRITICAL: Store embeddings as STRING (JSON) not ARRAY
        embeddings_sql = f"""
        CREATE TABLE IF NOT EXISTS {self.embeddings_table} (
            id STRING,
            chunk_id STRING,
            embedding STRING,
            created_at TIMESTAMP,
            PRIMARY KEY(id),
            FOREIGN KEY(chunk_id) REFERENCES {self.chunks_table}(id)
        )
        COMMENT 'Vector embeddings for chunks'
        """
        
        print(f"Creating tables in {self.config.catalog}.{self.config.schema}...")
        self.cursor.execute(documents_sql)
        self.cursor.execute(chunks_sql)
        self.cursor.execute(embeddings_sql)
        print("✓ Tables created successfully")
    
    def add_document(self, document_id: str, filename: str, volume_path: str,
                     file_type: str, file_size: int, status: str = 'pending',
                     last_modified: str = None) -> bool:
        """
        Add a document record.
        
        Args:
            document_id: Unique document ID
            filename: Original filename
            volume_path: Path in Databricks Volume
            file_type: File extension
            file_size: Size in bytes
            status: Processing status
            last_modified: Modification timestamp
        
        Returns:
            bool: True if successful
        """
        try:
            if last_modified is None:
                last_modified = datetime.now().isoformat()
            
            sql_query = f"""
            INSERT INTO {self.documents_table}
            (id, filename, volume_path, file_type, file_size, status, last_modified)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            self.cursor.execute(sql_query, (
                document_id, filename, volume_path, file_type,
                file_size, status, last_modified
            ))
            return True
        except Exception as e:
            print(f"Error adding document: {e}")
            return False
    
    def add_chunk(self, chunk_id: str, document_id: str, chunk_index: int,
                  text: str, token_count: int) -> bool:
        """
        Add a text chunk.
        
        Args:
            chunk_id: Unique chunk ID
            document_id: Parent document ID
            chunk_index: Index in document
            text: Chunk text
            token_count: Number of tokens
        
        Returns:
            bool: True if successful
        """
        try:
            sql_query = f"""
            INSERT INTO {self.chunks_table}
            (id, document_id, chunk_index, text, token_count, created_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP())
            """
            self.cursor.execute(sql_query, (
                chunk_id, document_id, chunk_index, text, token_count
            ))
            return True
        except Exception as e:
            print(f"Error adding chunk: {e}")
            return False
    
    def add_embedding(self, embedding_id: str, chunk_id: str,
                      embedding: List[float]) -> bool:
        """
        Add an embedding vector.
        
        ⚠️ CRITICAL: Embeddings are stored as JSON strings, not native arrays.
        This is because Databricks SQL connector has issues with array types.
        
        Args:
            embedding_id: Unique embedding ID
            chunk_id: Parent chunk ID
            embedding: Vector as list of floats
        
        Returns:
            bool: True if successful
        """
        try:
            # ⚠️ CRITICAL FIX: Convert list to JSON string
            embedding_json = json.dumps(embedding)
            
            sql_query = f"""
            INSERT INTO {self.embeddings_table}
            (id, chunk_id, embedding, created_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP())
            """
            self.cursor.execute(sql_query, (
                embedding_id, chunk_id, embedding_json
            ))
            return True
        except Exception as e:
            print(f"Error adding embedding: {e}")
            return False
    
    def search_by_text(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Full-text search in chunks.
        
        Args:
            query: Search query
            top_k: Number of results
        
        Returns:
            List of matching chunks
        """
        try:
            # Simple text search (can be enhanced with FTS index)
            sql_query = f"""
            SELECT c.id, c.document_id, c.chunk_index, c.text,
                   c.token_count, d.filename, d.volume_path
            FROM {self.chunks_table} c
            JOIN {self.documents_table} d ON c.document_id = d.id
            WHERE LOWER(c.text) LIKE LOWER(?)
            LIMIT ?
            """
            
            search_term = f"%{query}%"
            self.cursor.execute(sql_query, (search_term, top_k))
            
            results = []
            for row in self.cursor.fetchall():
                results.append({
                    'chunk_id': row[0],
                    'document_id': row[1],
                    'chunk_index': row[2],
                    'text': row[3],
                    'token_count': row[4],
                    'filename': row[5],
                    'volume_path': row[6]
                })
            
            return results
        except Exception as e:
            print(f"Error in text search: {e}")
            return []
    
    def search_by_vector(self, query_embedding: List[float],
                        top_k: int = 5) -> List[Dict]:
        """
        Semantic search using vector similarity.
        
        ⚠️ CRITICAL: Embeddings are stored as JSON strings and must be parsed.
        
        Args:
            query_embedding: Query vector
            top_k: Number of results
        
        Returns:
            List of chunks with similarity scores
        """
        try:
            # Note: This is a basic implementation
            # For production, use Databricks Vector Search or compute similarity in SQL
            
            sql_query = f"""
            SELECT c.id, c.document_id, c.chunk_index, c.text, c.token_count,
                   d.filename, d.volume_path, e.embedding
            FROM {self.chunks_table} c
            JOIN {self.documents_table} d ON c.document_id = d.id
            JOIN {self.embeddings_table} e ON c.id = e.chunk_id
            LIMIT ?
            """
            
            self.cursor.execute(sql_query, (top_k * 2,))
            
            results = []
            for row in self.cursor.fetchall():
                # ⚠️ CRITICAL FIX: Parse embedding from JSON string
                embedding = row[7]
                
                if isinstance(embedding, str):
                    try:
                        embedding = json.loads(embedding)
                    except:
                        # Fallback to eval for legacy formats
                        try:
                            embedding = eval(embedding) if embedding else []
                        except:
                            embedding = []
                elif not isinstance(embedding, list):
                    embedding = list(embedding) if embedding else []
                
                # Calculate cosine similarity
                similarity = self._cosine_similarity(query_embedding, embedding)
                
                results.append({
                    'chunk_id': row[0],
                    'document_id': row[1],
                    'chunk_index': row[2],
                    'text': row[3],
                    'token_count': row[4],
                    'filename': row[5],
                    'volume_path': row[6],
                    'similarity': similarity
                })
            
            # Sort by similarity (descending)
            results.sort(key=lambda x: x['similarity'], reverse=True)
            
            return results[:top_k]
            
        except Exception as e:
            print(f"Error in vector search: {e}")
            return []
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
        
        Returns:
            float: Cosine similarity (-1 to 1)
        """
        import math
        
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def get_stats(self) -> Dict:
        """
        Get RAG system statistics.
        
        Returns:
            dict: Statistics including document, chunk, and embedding counts
        """
        try:
            stats = {}
            
            # Document count
            self.cursor.execute(f"SELECT COUNT(*) FROM {self.documents_table}")
            stats['total_documents'] = self.cursor.fetchone()[0]
            
            # Chunk count
            self.cursor.execute(f"SELECT COUNT(*) FROM {self.chunks_table}")
            stats['total_chunks'] = self.cursor.fetchone()[0]
            
            # Embedding count
            self.cursor.execute(f"SELECT COUNT(*) FROM {self.embeddings_table}")
            stats['total_embeddings'] = self.cursor.fetchone()[0]
            
            return stats
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {}
    
    def update_document_status(self, doc_id: str, status: str) -> bool:
        """
        Update document processing status.
        
        Args:
            doc_id: Document ID
            status: New status ('processing', 'processed', 'error')
        
        Returns:
            bool: True if successful
        """
        try:
            sql_query = f"""
            UPDATE {self.documents_table}
            SET status = ?
            WHERE id = ?
            """
            self.cursor.execute(sql_query, (status, doc_id))
            return True
        except Exception as e:
            print(f"Error updating document status: {e}")
            return False
```

### Part 2: Databricks Embeddings

Create `rag/databricks_embeddings.py`:

```python
"""
Databricks Embeddings Client

Generates embeddings using Databricks serving endpoints.
Can use GPT-5 embeddings or Databricks-hosted embedding models.
"""

import os
import numpy as np
from typing import List, Optional
from openai import OpenAI
from dotenv import load_dotenv


class DatabricksEmbeddings:
    """Generate embeddings using Databricks serving endpoints"""
    
    def __init__(self, api_key: Optional[str] = None, 
                 model: str = "databricks-gte-large"):
        """
        Initialize embeddings client.
        
        Args:
            api_key: Databricks token (optional, reads from env)
            model: Embedding model name
        """
        load_dotenv()
        
        self.api_key = api_key or os.getenv('DATABRICKS_TOKEN')
        self.model = model
        self.client = None
        self._embedding_dim = 1024  # Default for databricks-gte-large
        
        if self.api_key:
            try:
                databricks_host = os.getenv('DATABRICKS_HOST')
                if not databricks_host:
                    print("Warning: DATABRICKS_HOST not found for embeddings.")
                    self.client = None
                    return
                
                # Use OpenAI SDK with Databricks endpoint
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url=f"https://{databricks_host}/serving-endpoints"
                )
            except Exception as e:
                print(f"Warning: Could not initialize Databricks Embeddings: {e}")
                self.client = None
    
    def get_embedding(self, text: str) -> List[float]:
        """
        Get embedding for a single text.
        
        Args:
            text: Input text
        
        Returns:
            List[float]: Embedding vector
        """
        if not self.client:
            print("Warning: Embeddings client not initialized. Using mock embedding.")
            return self._generate_mock_embedding(text)
        
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=[text]
            )
            # Return as list (already in correct format)
            return response.data[0].embedding
        except Exception as e:
            print(f"Error generating Databricks embedding: {e}")
            print("Falling back to mock embedding.")
            return self._generate_mock_embedding(text)
    
    def get_embeddings(self, texts: List[str], 
                       batch_size: int = 10) -> List[List[float]]:
        """
        Get embeddings for multiple texts.
        
        Args:
            texts: List of input texts
            batch_size: Batch size for API calls
        
        Returns:
            List[List[float]]: List of embedding vectors
        """
        if not self.client:
            return [self._generate_mock_embedding(text) for text in texts]
        
        embeddings = []
        
        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            try:
                response = self.client.embeddings.create(
                    model=self.model,
                    input=batch
                )
                batch_embeddings = [item.embedding for item in response.data]
                embeddings.extend(batch_embeddings)
            except Exception as e:
                print(f"Error in batch {i//batch_size}: {e}")
                # Use mock embeddings for failed batch
                mock_batch = [self._generate_mock_embedding(text) 
                             for text in batch]
                embeddings.extend(mock_batch)
        
        return embeddings
    
    def _generate_mock_embedding(self, text: str) -> List[float]:
        """
        Generate deterministic mock embedding for testing/fallback.
        
        Args:
            text: Input text
        
        Returns:
            List[float]: Mock embedding vector
        """
        import hashlib
        
        # Generate deterministic hash
        hash_obj = hashlib.md5(text.encode())
        hash_int = int(hash_obj.hexdigest(), 16)
        
        # Use hash as seed for reproducibility
        np.random.seed(hash_int % (2**32))
        
        # Generate random normalized vector
        embedding = np.random.randn(self._embedding_dim)
        embedding = embedding / np.linalg.norm(embedding)
        
        return embedding.tolist()
    
    @property
    def embedding_dimension(self) -> int:
        """Get embedding dimension"""
        return self._embedding_dim
```

### Part 3: Databricks Retriever

Create `rag/databricks_retriever.py`:

```python
"""
Databricks RAG Retriever

Performs hybrid search (text + vector) using Databricks tables.
Maintains same interface as original SQLite retriever for compatibility.
"""

import sys
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.databricks_rag_manager import DatabricksRAGManager
from databricks_config import DatabricksConfig


@dataclass
class RetrievedChunk:
    """Container for retrieved chunk data"""
    chunk_id: str
    content: str
    score: float
    filename: str
    chunk_index: int
    doc_id: str


class DatabricksRAGRetriever:
    """Retrieve relevant chunks from Databricks"""
    
    def __init__(self, 
                 config: Optional[DatabricksConfig] = None,
                 embeddings_client=None):
        """
        Initialize Databricks RAG retriever.
        
        Args:
            config: DatabricksConfig instance
            embeddings_client: Embeddings client (DatabricksEmbeddings)
        """
        self.config = config or DatabricksConfig()
        self.rag_manager = DatabricksRAGManager(self.config)
        self.embeddings = embeddings_client
        self._connected = False
    
    def connect(self) -> bool:
        """Connect to Databricks"""
        self._connected = self.rag_manager.connect()
        return self._connected
    
    def disconnect(self):
        """Disconnect from Databricks"""
        self.rag_manager.disconnect()
        self._connected = False
    
    def retrieve(self, query: str, top_k: int = 5,
                 fts_weight: float = 0.4) -> List[RetrievedChunk]:
        """
        Retrieve relevant chunks using hybrid search.
        
        Args:
            query: User query
            top_k: Number of chunks to retrieve
            fts_weight: Weight for FTS score (0-1), semantic gets (1-fts_weight)
        
        Returns:
            List of RetrievedChunk objects
        """
        if not self._connected:
            if not self.connect():
                return []
        
        try:
            print(f"\n🔍 [Databricks RAG Retrieval]")
            print(f"   Query: {query[:50]}...")
            print(f"   Top-K: {top_k}")
            print(f"   FTS Weight: {fts_weight}")
            
            # 1. Full-text search
            fts_results = self.rag_manager.search_by_text(query, top_k=top_k * 2)
            print(f"   FTS results: {len(fts_results)}")
            
            # 2. Semantic search
            semantic_results = []
            if self.embeddings:
                try:
                    query_embedding = self.embeddings.get_embedding(query)
                    semantic_results = self.rag_manager.search_by_vector(
                        query_embedding, 
                        top_k=top_k * 2
                    )
                    print(f"   Semantic results: {len(semantic_results)}")
                except Exception as e:
                    print(f"Error in vector search: {e}")
                    print(f"   Semantic results: 0")
            
            # 3. Merge results
            merged_results = self._merge_results(
                fts_results,
                semantic_results,
                fts_weight=fts_weight
            )
            
            # 4. Take top-K
            top_results = merged_results[:top_k]
            
            # 5. Convert to RetrievedChunk objects
            retrieved_chunks = []
            for result in top_results:
                chunk = RetrievedChunk(
                    chunk_id=result['chunk_id'],
                    content=result['text'],
                    score=result.get('score', 0.0),
                    filename=result.get('filename', ''),
                    chunk_index=result.get('chunk_index', 0),
                    doc_id=result.get('document_id', '')
                )
                retrieved_chunks.append(chunk)
            
            print(f"   ✓ Retrieved {len(retrieved_chunks)} chunks")
            
            return retrieved_chunks
        
        except Exception as e:
            print(f"❌ RAG retrieval failed: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _merge_results(self, fts_results: List[Dict], 
                       semantic_results: List[Dict],
                       fts_weight: float) -> List[Dict]:
        """
        Merge FTS and semantic search results with weighted scoring.
        
        Args:
            fts_results: Full-text search results
            semantic_results: Semantic search results
            fts_weight: Weight for FTS score (0-1)
        
        Returns:
            List of merged results with scores
        """
        semantic_weight = 1.0 - fts_weight
        
        # Combine results
        all_chunks = {}
        
        # Add FTS results
        for i, result in enumerate(fts_results):
            chunk_id = result['chunk_id']
            fts_score = 1.0 / (i + 1)  # Rank-based score
            all_chunks[chunk_id] = {
                **result,
                'fts_score': fts_score,
                'semantic_score': 0.0
            }
        
        # Add semantic results
        for result in semantic_results:
            chunk_id = result['chunk_id']
            semantic_score = result.get('similarity', 0.0)
            
            if chunk_id in all_chunks:
                all_chunks[chunk_id]['semantic_score'] = semantic_score
            else:
                all_chunks[chunk_id] = {
                    **result,
                    'fts_score': 0.0,
                    'semantic_score': semantic_score
                }
        
        # Calculate combined scores
        results = []
        for chunk_id, chunk_data in all_chunks.items():
            combined_score = (
                fts_weight * chunk_data['fts_score'] +
                semantic_weight * chunk_data['semantic_score']
            )
            results.append({
                **chunk_data,
                'score': combined_score
            })
        
        # Sort by combined score
        results.sort(key=lambda x: x['score'], reverse=True)
        
        return results
    
    def format_chunks_for_prompt(self, chunks: List[RetrievedChunk],
                                 max_chunks: int = 5,
                                 include_sources: bool = True) -> str:
        """
        Format retrieved chunks for inclusion in LLM prompt.
        
        ⚠️ CRITICAL: This method signature MUST match the expected interface!
        Do not change the parameter names or order.
        
        Args:
            chunks: List of RetrievedChunk objects
            max_chunks: Maximum number of chunks to include
            include_sources: Whether to include source filenames
        
        Returns:
            Formatted string with chunks
        """
        if not chunks:
            return ""
        
        # Limit to max_chunks
        chunks_to_format = chunks[:max_chunks]
        
        formatted = "Retrieved context from documents:\n\n"
        
        for i, chunk in enumerate(chunks_to_format):
            if include_sources:
                chunk_text = f"[Document: {chunk.filename}, Chunk {chunk.chunk_index}]\n"
            else:
                chunk_text = ""
            chunk_text += f"{chunk.content}\n\n"
            formatted += chunk_text
        
        return formatted
    
    def get_stats(self) -> Dict:
        """
        Get RAG system statistics.
        
        Returns:
            Dictionary with system stats
        """
        if not self._connected:
            if not self.connect():
                return {}
        
        stats = self.rag_manager.get_stats()
        return stats
```

---

## Critical Fixes & Gotchas

### ⚠️ Fix #1: Temperature Parameter

**Error**: `Unsupported value: 'temperature' does not support 0.7 with this model`

**Cause**: GPT-5 via Databricks only supports default temperature (1.0)

**Solution**:
```python
# ❌ WRONG - Will cause 400 error
response = client.chat.completions.create(
    model="databricks-gpt-5",
    messages=messages,
    temperature=0.7  # DO NOT INCLUDE THIS
)

# ✅ CORRECT
response = client.chat.completions.create(
    model="databricks-gpt-5",
    messages=messages,
    max_tokens=2000
    # No temperature parameter
)
```

### ⚠️ Fix #2: Embedding Storage

**Error**: `can't multiply sequence by non-int of type 'float'`

**Cause**: Embeddings stored as strings instead of float arrays

**Solution**:
```python
# ✅ When storing embeddings:
embedding_json = json.dumps(embedding_list)

# ✅ When retrieving embeddings:
if isinstance(embedding, str):
    try:
        embedding = json.loads(embedding)
    except:
        embedding = eval(embedding) if embedding else []
elif not isinstance(embedding, list):
    embedding = list(embedding) if embedding else []
```

### ⚠️ Fix #3: Method Signatures

**Error**: `format_chunks_for_prompt() got an unexpected keyword argument 'max_chunks'`

**Cause**: Method signature doesn't match expected interface

**Solution**:
```python
# ✅ MUST have these exact parameters:
def format_chunks_for_prompt(self, chunks: List[RetrievedChunk],
                             max_chunks: int = 5,
                             include_sources: bool = True) -> str:
    """Format chunks for prompt"""
    # Implementation
```

### ⚠️ Fix #4: Session Handling (Flask)

**Error**: `'NoneType' object is not subscriptable`

**Cause**: API endpoint tries to access session that doesn't exist

**Solution**:
```python
# ✅ In Flask API endpoint:
session_id = data.get('session_id') or session.get('session_id')
if not session_id:
    session_id = str(uuid.uuid4())
    session['session_id'] = session_id
```

### ⚠️ Fix #5: NumPy Warnings

**Issue**: Lots of NumPy compatibility warnings in console

**Solution**: Suppress at app startup
```python
import os
import warnings

# At top of app.py
os.environ['PYTHONWARNINGS'] = 'ignore'
warnings.filterwarnings('ignore')
```

---

## Testing & Verification

### Test 1: Configuration

```python
"""Test Databricks configuration"""
from databricks_config import DatabricksConfig

config = DatabricksConfig()
is_valid, error = config.validate()

if is_valid:
    print("✅ Configuration valid")
    print(f"Host: {config.host}")
    print(f"Catalog.Schema: {config.catalog}.{config.schema}")
else:
    print(f"❌ Configuration error: {error}")
```

### Test 2: LLM Connection

```python
"""Test GPT-5 via Databricks"""
from utils.llm_client import LLMClient, LLMProvider

client = LLMClient(provider=LLMProvider.DATABRICKS)

response = client.chat([
    {"role": "user", "content": "Hello! Can you confirm you're working?"}
])

print("Response:", response['content'])
```

### Test 3: RAG System

```python
"""Test complete RAG pipeline"""
from rag.databricks_retriever import DatabricksRAGRetriever
from rag.databricks_embeddings import DatabricksEmbeddings
from databricks_config import DatabricksConfig

# Initialize
config = DatabricksConfig()
embeddings = DatabricksEmbeddings()
retriever = DatabricksRAGRetriever(
    config=config,
    embeddings_client=embeddings
)

# Connect and test
if retriever.connect():
    print("✅ Connected to Databricks")
    
    # Get stats
    stats = retriever.get_stats()
    print(f"Documents: {stats.get('total_documents', 0)}")
    print(f"Chunks: {stats.get('total_chunks', 0)}")
    
    # Test retrieval
    chunks = retriever.retrieve("How do I install an ONT?", top_k=3)
    print(f"\n✅ Retrieved {len(chunks)} chunks")
    
    for i, chunk in enumerate(chunks):
        print(f"\nChunk {i+1}:")
        print(f"  File: {chunk.filename}")
        print(f"  Score: {chunk.score:.3f}")
        print(f"  Content: {chunk.content[:100]}...")
else:
    print("❌ Failed to connect")
```

---

## Troubleshooting

### Common Issues

| Issue | Possible Cause | Solution |
|-------|---------------|----------|
| Connection refused | Wrong credentials | Verify `.env` file |
| 404 model not found | Wrong provider in config | Set `LLM_PROVIDER=databricks` |
| Temperature error | Passing temperature to GPT-5 | Remove temperature parameter |
| Embedding error | Embeddings stored as strings | Parse with `json.loads()` |
| Method signature error | Wrong parameters | Match exact interface |
| NumPy warnings | Version incompatibility | Suppress warnings (non-fatal) |
| Table not found | Tables not created | Run setup script |
| No results from RAG | No documents ingested | Run ingestion script |

### Debug Checklist

1. **Verify Configuration**
   ```bash
   python databricks_config.py
   ```

2. **Check Environment Variables**
   ```bash
   cat .env | grep DATABRICKS
   ```

3. **Test Connectivity**
   ```python
   from databricks import sql
   from databricks_config import DatabricksConfig
   
   config = DatabricksConfig()
   conn = sql.connect(**config.get_connection_params())
   print("✅ Connected!")
   conn.close()
   ```

4. **Verify Tables Exist**
   ```python
   from database.databricks_rag_manager import DatabricksRAGManager
   from databricks_config import DatabricksConfig
   
   manager = DatabricksRAGManager(DatabricksConfig())
   manager.connect()
   stats = manager.get_stats()
   print(f"Tables exist: {stats}")
   ```

---

## Quick Start Checklist

### Phase 1: Setup (15 minutes)
- [ ] Get Databricks credentials (host, token, http_path)
- [ ] Create `.env` file with credentials
- [ ] Install packages: `pip install databricks-sql-connector openai python-dotenv`
- [ ] Create `databricks_config.py`
- [ ] Test configuration: `python databricks_config.py`

### Phase 2: LLM Integration (30 minutes)
- [ ] Add `DATABRICKS` to `LLMProvider` enum
- [ ] Update `_get_api_key_from_env()`
- [ ] Update `_get_default_model()`
- [ ] Add Databricks client initialization
- [ ] Update `chat()` method (⚠️ NO temperature!)
- [ ] Update `config.py` to use databricks provider
- [ ] Test LLM: Send test query

### Phase 3: RAG Integration (1-2 hours)
- [ ] Create `database/databricks_rag_manager.py`
- [ ] Create `rag/databricks_embeddings.py`
- [ ] Create `rag/databricks_retriever.py`
- [ ] Fix `format_chunks_for_prompt()` signature
- [ ] Create RAG tables in Databricks
- [ ] Test retrieval

### Phase 4: Application Integration (30 minutes)
- [ ] Update `app.py` imports
- [ ] Initialize Databricks components
- [ ] Update session handling
- [ ] Add warning suppression (optional)
- [ ] Test end-to-end

### Phase 5: Verification (15 minutes)
- [ ] Test configuration
- [ ] Test LLM responses
- [ ] Test RAG retrieval
- [ ] Verify all features work
- [ ] Check performance

---

## Success Criteria

✅ **Your integration is successful when:**

1. GPT-5 responds to queries without errors
2. Databricks connection established
3. Tables created and accessible
4. RAG retrieval returns relevant chunks
5. Responses include document-specific information
6. All existing features still work
7. Performance is acceptable (<5s response time)
8. No critical errors in logs

---

## Additional Resources

- **Databricks SQL Connector**: https://docs.databricks.com/dev-tools/python-sql-connector.html
- **OpenAI Python SDK**: https://github.com/openai/openai-python
- **Databricks Model Serving**: https://docs.databricks.com/machine-learning/model-serving/index.html
- **This Implementation**: Tested in production Frontier AI Assistant

---

## Appendix: File Structure

```
your_project/
├── .env                              # Environment variables
├── requirements.txt                  # Python dependencies
├── databricks_config.py              # ✨ NEW: Configuration
├── config.py                         # Updated: Use databricks
│
├── utils/
│   └── llm_client.py                # Updated: Add Databricks provider
│
├── database/
│   ├── databricks_rag_manager.py    # ✨ NEW: RAG table manager
│   └── setup_databricks_rag.py      # ✨ NEW: Setup script
│
├── rag/
│   ├── databricks_retriever.py      # ✨ NEW: Retriever
│   ├── databricks_embeddings.py     # ✨ NEW: Embeddings
│   └── ingestion.py                 # Updated: Use Databricks
│
├── app.py                           # Updated: Databricks integration
│
└── tests/
    ├── test_databricks_config.py   # ✨ NEW: Config tests
    ├── test_databricks_llm.py       # ✨ NEW: LLM tests
    └── test_databricks_rag.py       # ✨ NEW: RAG tests
```

---

**Document Status**: ✅ Complete and Production-Ready  
**Last Updated**: November 16, 2025  
**Version**: 1.0

**Changelog**:
- v1.0 (2025-11-16): Initial release with all fixes and best practices

---

**Need Help?** Refer to the troubleshooting section or check the examples in the working implementation.


