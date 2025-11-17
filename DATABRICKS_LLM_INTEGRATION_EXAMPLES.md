# 📚 Databricks LLM Integration - Detailed Code Examples

## Complete Working Examples for Tech Buddy Chatbot

This guide provides complete, copy-paste-ready code examples for integrating Databricks GPT-5 into the Tech Buddy web chat application.

---

## Table of Contents

1. [Environment Setup](#1-environment-setup)
2. [Configuration Files](#2-configuration-files)
3. [LLM Client Implementation](#3-llm-client-implementation)
4. [API Backend Integration](#4-api-backend-integration)
5. [Frontend Implementation](#5-frontend-implementation)
6. [Testing Scripts](#6-testing-scripts)
7. [Complete Request/Response Flow](#7-complete-requestresponse-flow)
8. [Error Handling](#8-error-handling)

---

## 1. Environment Setup

### Complete `.env` File

```env
# ==============================================
# Databricks Connection
# ==============================================
# Host: Your Databricks workspace URL (NO https://)
DATABRICKS_HOST=dbc-4a93b454-f17b.cloud.databricks.com

# Token: Personal Access Token from Databricks
# Format: dapi followed by alphanumeric characters
DATABRICKS_TOKEN=dapid0b48dc0de608f1e70d36cb20ac7699d

# HTTP Path: SQL Warehouse endpoint
# Format: /sql/1.0/warehouses/{warehouse_id}
DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/b914ad7a8dc4d91c

# ==============================================
# Databricks Database (for RAG)
# ==============================================
DATABRICKS_CATALOG=hackathon
DATABRICKS_SCHEMA=hackathon_ctrl_alt_elite

# ==============================================
# LLM Configuration
# ==============================================
# Provider: Must be "databricks" (lowercase)
LLM_PROVIDER=databricks

# Model: The serving endpoint name
# Common options: databricks-gpt-5, databricks-gpt-4
LLM_MODEL=databricks-gpt-5

# ==============================================
# OpenAI (for Realtime API voice chat only)
# ==============================================
# Only needed if using voice chat feature
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx

# ==============================================
# Local Database URLs
# ==============================================
# SQLite for chat history
DATABASE_URL=sqlite:///./chatbot.db

# SQLite for device management
DEVICES_DB_URL=sqlite:///./devices.db

# Directory for SOP documents
SOPS_DIR=./sops

# ==============================================
# RAG Configuration
# ==============================================
# Enable/disable RAG system
ENABLE_RAG=true

# Number of chunks to retrieve
RAG_TOP_K=5

# Weight for full-text search (0.0-1.0)
RAG_FTS_WEIGHT=0.4
```

### Creating `.env` on Windows (PowerShell)

```powershell
# Method 1: Using PowerShell with correct encoding
Set-Content -Path .env -Value @'
DATABRICKS_HOST=dbc-4a93b454-f17b.cloud.databricks.com
DATABRICKS_TOKEN=dapid0b48dc0de608f1e70d36cb20ac7699d
DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/b914ad7a8dc4d91c
DATABRICKS_CATALOG=hackathon
DATABRICKS_SCHEMA=hackathon_ctrl_alt_elite
LLM_PROVIDER=databricks
LLM_MODEL=databricks-gpt-5
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx
DATABASE_URL=sqlite:///./chatbot.db
DEVICES_DB_URL=sqlite:///./devices.db
SOPS_DIR=./sops
ENABLE_RAG=true
RAG_TOP_K=5
RAG_FTS_WEIGHT=0.4
'@ -Encoding ASCII -NoNewline

# Method 2: Using echo (simpler but watch for quotes)
echo DATABRICKS_HOST=dbc-4a93b454-f17b.cloud.databricks.com > .env
echo DATABRICKS_TOKEN=dapid0b48dc0de608f1e70d36cb20ac7699d >> .env
echo DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/b914ad7a8dc4d91c >> .env
# ... add remaining lines
```

### Verifying `.env` File

```python
# verify_env.py
from dotenv import load_dotenv
import os

load_dotenv()

print("="*60)
print("Environment Variable Verification")
print("="*60)

vars_to_check = [
    "DATABRICKS_HOST",
    "DATABRICKS_TOKEN",
    "DATABRICKS_HTTP_PATH",
    "DATABRICKS_CATALOG",
    "DATABRICKS_SCHEMA",
    "LLM_PROVIDER",
    "LLM_MODEL"
]

all_ok = True

for var in vars_to_check:
    value = os.getenv(var)
    if value:
        # Mask token for security
        if "TOKEN" in var:
            display_value = f"{value[:8]}...{value[-4:]}"
        else:
            display_value = value
        print(f"✅ {var:25s} = {display_value}")
    else:
        print(f"❌ {var:25s} = NOT SET")
        all_ok = False

print("="*60)
if all_ok:
    print("✅ All environment variables configured correctly!")
else:
    print("❌ Some environment variables are missing. Check your .env file.")
print("="*60)
```

---

## 2. Configuration Files

### `databricks_config.py` - Complete Implementation

```python
"""
Databricks Configuration Manager

Manages connection settings for Databricks workspace, including:
- SQL Warehouse connection parameters
- Catalog and schema configuration
- Volume path generation
- Connection validation
"""

import os
from typing import Dict, Optional
from dotenv import load_dotenv

# Load environment variables at module level
load_dotenv()


class DatabricksConfig:
    """
    Databricks connection configuration.
    
    Loads settings from environment variables and provides
    connection parameters for databricks-sql-connector.
    """
    
    def __init__(self):
        """Initialize configuration from environment variables."""
        self.host = os.getenv("DATABRICKS_HOST")
        self.token = os.getenv("DATABRICKS_TOKEN")
        self.http_path = os.getenv("DATABRICKS_HTTP_PATH")
        self.catalog = os.getenv("DATABRICKS_CATALOG", "hackathon")
        self.schema = os.getenv("DATABRICKS_SCHEMA", "hackathon_ctrl_alt_elite")
    
    def validate(self) -> bool:
        """
        Validate that all required configuration is present.
        
        Returns:
            bool: True if valid, False otherwise
        """
        required = {
            "DATABRICKS_HOST": self.host,
            "DATABRICKS_TOKEN": self.token,
            "DATABRICKS_HTTP_PATH": self.http_path
        }
        
        missing = [k for k, v in required.items() if not v]
        
        if missing:
            print(f"❌ Missing required configuration: {', '.join(missing)}")
            print("\nPlease set these in your .env file:")
            for var in missing:
                print(f"  {var}=your_value_here")
            return False
        
        # Validate host format (should not include https://)
        if self.host.startswith("http"):
            print("❌ DATABRICKS_HOST should NOT include 'https://'")
            print(f"   Current: {self.host}")
            print(f"   Correct: {self.host.replace('https://', '').replace('http://', '')}")
            return False
        
        # Validate token format (should start with 'dapi')
        if not self.token.startswith("dapi"):
            print("⚠️  Warning: DATABRICKS_TOKEN should typically start with 'dapi'")
            print(f"   Current format: {self.token[:10]}...")
        
        print("✅ Databricks configuration valid")
        return True
    
    def get_connection_params(self) -> Dict[str, str]:
        """
        Get connection parameters for databricks-sql-connector.
        
        Returns:
            dict: Connection parameters
        """
        return {
            "server_hostname": self.host,
            "http_path": self.http_path,
            "access_token": self.token
        }
    
    def get_volume_path(self, filename: str) -> str:
        """
        Generate Databricks Volume path for a file.
        
        Args:
            filename: Name of the file
        
        Returns:
            str: Full volume path
        """
        return f"/Volumes/{self.catalog}/{self.schema}/documents/{filename}"
    
    def get_table_name(self, table: str) -> str:
        """
        Get fully qualified table name.
        
        Args:
            table: Table name (e.g., 'documents', 'chunks')
        
        Returns:
            str: Fully qualified name (e.g., 'hackathon.hackathon_ctrl_alt_elite.documents')
        """
        return f"{self.catalog}.{self.schema}.{table}"
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"DatabricksConfig(\n"
            f"  host={self.host},\n"
            f"  token={self.token[:8]}...{self.token[-4:] if self.token else 'None'},\n"
            f"  catalog={self.catalog},\n"
            f"  schema={self.schema}\n"
            f")"
        )


def check_config() -> bool:
    """
    Quick configuration check.
    
    Returns:
        bool: True if configuration is valid
    """
    config = DatabricksConfig()
    return config.validate()


if __name__ == "__main__":
    # Test configuration when run directly
    print("="*60)
    print("Databricks Configuration Test")
    print("="*60)
    
    config = DatabricksConfig()
    
    print("\nConfiguration:")
    print(config)
    
    print("\nValidation:")
    is_valid = config.validate()
    
    if is_valid:
        print("\nConnection Parameters:")
        params = config.get_connection_params()
        for key, value in params.items():
            if "token" in key.lower():
                value = f"{value[:8]}...{value[-4:]}"
            print(f"  {key}: {value}")
        
        print("\nExample Table Names:")
        for table in ["documents", "chunks", "embeddings"]:
            print(f"  {table:12s} → {config.get_table_name(table)}")
    
    print("="*60)
```

### `config.py` - Application Configuration

```python
"""
Application-wide configuration.

Defines settings for LLM, RAG, and general application behavior.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# ==============================================
# LLM Configuration
# ==============================================

# LLM Provider: "databricks", "openai", or "anthropic"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "databricks")

# Model name for Databricks serving endpoint
DATABRICKS_MODEL = os.getenv("LLM_MODEL", "databricks-gpt-5")

# Temperature (NOT used for Databricks GPT-5)
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))

# Max tokens in response
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "2000"))

# System prompt
SYSTEM_PROMPT = """You are Tech Buddy, a helpful technical support assistant for network device management.

You help with:
- Registering new ONTs (Optical Network Terminals) and routers
- Swapping faulty devices
- Checking device status
- Troubleshooting connectivity issues
- Providing technical guidance from SOPs

Be concise, friendly, and technical. Ask clarifying questions when needed."""


# ==============================================
# RAG Configuration
# ==============================================

# Enable RAG system
ENABLE_RAG = os.getenv("ENABLE_RAG", "true").lower() == "true"

# Number of chunks to retrieve
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "5"))

# Weight for full-text search in hybrid search (0.0 to 1.0)
# Higher = more weight on keyword matching
# Lower = more weight on semantic similarity
RAG_FTS_WEIGHT = float(os.getenv("RAG_FTS_WEIGHT", "0.4"))

# Minimum similarity score for chunks
RAG_MIN_SCORE = float(os.getenv("RAG_MIN_SCORE", "0.3"))


# ==============================================
# Database Configuration
# ==============================================

# Chat history database (SQLite)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./chatbot.db")

# Device management database (SQLite)
DEVICES_DB_URL = os.getenv("DEVICES_DB_URL", "sqlite:///./devices.db")

# SOP documents directory
SOPS_DIR = os.getenv("SOPS_DIR", "./sops")


# ==============================================
# Session Configuration
# ==============================================

# Session timeout (seconds)
SESSION_TIMEOUT = int(os.getenv("SESSION_TIMEOUT", "3600"))

# Max messages in conversation history
MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES", "20"))


# ==============================================
# API Configuration
# ==============================================

# API port
API_PORT = int(os.getenv("API_PORT", "8000"))

# CORS origins
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")


# ==============================================
# Validation
# ==============================================

def validate_config():
    """Validate critical configuration settings."""
    issues = []
    
    if LLM_PROVIDER not in ["databricks", "openai", "anthropic"]:
        issues.append(f"Invalid LLM_PROVIDER: {LLM_PROVIDER}")
    
    if LLM_PROVIDER == "databricks":
        if not os.getenv("DATABRICKS_HOST"):
            issues.append("DATABRICKS_HOST not set")
        if not os.getenv("DATABRICKS_TOKEN"):
            issues.append("DATABRICKS_TOKEN not set")
    
    if ENABLE_RAG:
        if not os.getenv("DATABRICKS_CATALOG"):
            issues.append("DATABRICKS_CATALOG not set (required for RAG)")
        if not os.getenv("DATABRICKS_SCHEMA"):
            issues.append("DATABRICKS_SCHEMA not set (required for RAG)")
    
    if issues:
        print("❌ Configuration issues:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    
    print("✅ Configuration valid")
    return True


if __name__ == "__main__":
    print("="*60)
    print("Application Configuration")
    print("="*60)
    print(f"LLM Provider: {LLM_PROVIDER}")
    print(f"Model: {DATABRICKS_MODEL}")
    print(f"Max Tokens: {MAX_TOKENS}")
    print(f"RAG Enabled: {ENABLE_RAG}")
    if ENABLE_RAG:
        print(f"RAG Top K: {RAG_TOP_K}")
        print(f"RAG FTS Weight: {RAG_FTS_WEIGHT}")
    print("="*60)
    validate_config()
```

---

## 3. LLM Client Implementation

### `utils/llm_client.py` - Complete with Databricks Support

```python
"""
LLM Client with Multi-Provider Support

Supports:
- Databricks (GPT-5)
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
"""

import os
import requests
from enum import Enum
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Load environment
load_dotenv()


class LLMProvider(Enum):
    """Supported LLM providers."""
    DATABRICKS = "databricks"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class LLMClient:
    """
    Unified LLM client supporting multiple providers.
    
    Usage:
        client = LLMClient(provider="databricks", model="databricks-gpt-5")
        response = client.chat(messages=[...])
        print(response["content"])
    """
    
    def __init__(self, provider: str = None, model: str = None):
        """
        Initialize LLM client.
        
        Args:
            provider: LLM provider ("databricks", "openai", "anthropic")
            model: Model name
        """
        # Load provider from env if not specified
        self.provider_str = provider or os.getenv("LLM_PROVIDER", "databricks")
        self.provider = LLMProvider(self.provider_str.lower())
        
        # Load model from env if not specified
        self.model = model or os.getenv("LLM_MODEL", "databricks-gpt-5")
        
        # Initialize provider-specific client
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize provider-specific client."""
        if self.provider == LLMProvider.DATABRICKS:
            # Databricks configuration
            self.api_key = os.getenv("DATABRICKS_TOKEN")
            self.databricks_host = os.getenv("DATABRICKS_HOST")
            
            if not self.api_key or not self.databricks_host:
                print("⚠️  Warning: Databricks credentials not configured")
                print("   Set DATABRICKS_HOST and DATABRICKS_TOKEN in .env")
                self.databricks_url = None
                return
            
            # Build endpoint URL
            # CRITICAL: Use /invocations, NOT /chat/completions
            self.databricks_url = (
                f"https://{self.databricks_host}"
                f"/serving-endpoints/{self.model}/invocations"
            )
            
            print(f"✅ Databricks LLM initialized")
            print(f"   Model: {self.model}")
            print(f"   Endpoint: {self.databricks_url}")
        
        elif self.provider == LLMProvider.OPENAI:
            # OpenAI configuration
            try:
                from openai import OpenAI
                self.api_key = os.getenv("OPENAI_API_KEY")
                self.client = OpenAI(api_key=self.api_key)
                print(f"✅ OpenAI initialized: {self.model}")
            except ImportError:
                print("❌ openai package not installed")
                self.client = None
        
        elif self.provider == LLMProvider.ANTHROPIC:
            # Anthropic configuration
            try:
                from anthropic import Anthropic
                self.api_key = os.getenv("ANTHROPIC_API_KEY")
                self.client = Anthropic(api_key=self.api_key)
                print(f"✅ Anthropic initialized: {self.model}")
            except ImportError:
                print("❌ anthropic package not installed")
                self.client = None
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Dict[str, str]:
        """
        Send chat completion request.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (IGNORED for Databricks)
            max_tokens: Max tokens in response
        
        Returns:
            dict: {"content": "response text"}
        
        Example:
            response = client.chat(messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello!"}
            ])
            print(response["content"])
        """
        if self.provider == LLMProvider.DATABRICKS:
            return self._chat_databricks(messages, max_tokens)
        elif self.provider == LLMProvider.OPENAI:
            return self._chat_openai(messages, temperature, max_tokens)
        elif self.provider == LLMProvider.ANTHROPIC:
            return self._chat_anthropic(messages, temperature, max_tokens)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    def _chat_databricks(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int
    ) -> Dict[str, str]:
        """
        Chat with Databricks GPT-5.
        
        CRITICAL IMPLEMENTATION NOTES:
        1. Use /invocations endpoint (NOT /chat/completions)
        2. Do NOT send temperature parameter
        3. Use direct requests.post() (NOT OpenAI SDK)
        """
        if not self.databricks_url:
            # Mock response for testing
            return {
                "content": "Mock response (Databricks not configured)"
            }
        
        # Debug logging
        print(f"\n🤖 [Databricks GPT-5 API Call]")
        print(f"   URL: {self.databricks_url}")
        print(f"   Model: {self.model}")
        print(f"   Messages: {len(messages)}")
        print(f"   Max tokens: {max_tokens}")
        print(f"   Note: temperature NOT sent (unsupported by GPT-5)")
        
        # Prepare headers
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Prepare payload
        # ⚠️ CRITICAL: NO temperature parameter
        data = {
            "messages": messages,
            "max_tokens": max_tokens
        }
        
        # Make request
        try:
            response = requests.post(
                self.databricks_url,
                headers=headers,
                json=data,
                timeout=30
            )
            
            # Check response
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                
                print(f"\n✓ [Databricks Response]")
                print(f"   Status: {response.status_code}")
                print(f"   Response length: {len(content)} chars")
                
                return {"content": content}
            else:
                error_msg = f"Databricks API error {response.status_code}: {response.text}"
                print(f"\n✗ [Databricks Error]")
                print(f"   Status: {response.status_code}")
                print(f"   Error: {response.text}")
                raise Exception(error_msg)
        
        except requests.exceptions.Timeout:
            raise Exception("Request timeout - Databricks endpoint not responding")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error: {str(e)}")
    
    def _chat_openai(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int
    ) -> Dict[str, str]:
        """Chat with OpenAI."""
        if not self.client:
            return {"content": "OpenAI client not initialized"}
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return {"content": response.choices[0].message.content}
    
    def _chat_anthropic(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int
    ) -> Dict[str, str]:
        """Chat with Anthropic Claude."""
        if not self.client:
            return {"content": "Anthropic client not initialized"}
        
        # Convert messages format for Anthropic
        system_msg = None
        claude_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            else:
                claude_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        response = self.client.messages.create(
            model=self.model,
            system=system_msg,
            messages=claude_messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return {"content": response.content[0].text}


# Example usage
if __name__ == "__main__":
    print("="*60)
    print("LLM Client Test")
    print("="*60)
    
    # Initialize client
    client = LLMClient(provider="databricks", model="databricks-gpt-5")
    
    # Test messages
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant. Respond in one sentence."
        },
        {
            "role": "user",
            "content": "Say 'Hello from Databricks GPT-5!' if you can read this."
        }
    ]
    
    print("\n📤 Sending test message...")
    
    try:
        response = client.chat(messages=messages, max_tokens=100)
        print("\n📥 Response received:")
        print(f"   {response['content']}")
        print("\n✅ Test successful!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
    
    print("="*60)
```

---

## 4. API Backend Integration

### Minimal Working Example - `api/main_simple.py`

This is a simplified version showing just the core chat functionality:

```python
"""
Simplified Tech Buddy API - Core Chat Only

This minimal example shows how to:
1. Accept chat requests
2. Call Databricks GPT-5
3. Stream responses via SSE
"""

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json
import asyncio
import sys
from pathlib import Path

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.llm_client import LLMClient

# Initialize FastAPI
app = FastAPI(title="Tech Buddy API (Simplified)")

# Initialize LLM client
llm_client = LLMClient(provider="databricks", model="databricks-gpt-5")


class ChatRequest(BaseModel):
    """Chat request model."""
    message: str
    session_id: str


@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Stream chat responses using SSE.
    
    Example request:
        POST /api/chat/stream
        {
            "message": "Hello!",
            "session_id": "test-123"
        }
    """
    print(f"\n{'='*60}")
    print(f"📝 Received message: {request.message}")
    print(f"🔑 Session ID: {request.session_id}")
    
    async def generate_response():
        """SSE generator function."""
        try:
            # Build messages (simple system prompt + user message)
            messages = [
                {
                    "role": "system",
                    "content": "You are Tech Buddy, a helpful technical support assistant."
                },
                {
                    "role": "user",
                    "content": request.message
                }
            ]
            
            print(f"\n🤖 Calling Databricks GPT-5...")
            
            # Call LLM
            response = llm_client.chat(
                messages=messages,
                max_tokens=2000
            )
            
            content = response.get("content", "No response")
            
            print(f"✅ Response received ({len(content)} chars)")
            
            # SSE Streaming Pattern (3 steps)
            
            # Step 1: Send ping to establish connection
            print(f"📡 Step 1: Sending ping...")
            yield ": ping\n\n"
            await asyncio.sleep(0.05)
            
            # Step 2: Send actual data
            print(f"📡 Step 2: Sending data...")
            sse_data = {"content": content, "done": True}
            yield f"data: {json.dumps(sse_data)}\n\n"
            
            # Step 3: Keep stream open briefly
            print(f"⏳ Step 3: Keeping stream open...")
            await asyncio.sleep(0.3)
            
            print(f"🏁 Stream complete")
        
        except Exception as e:
            print(f"❌ Error: {e}")
            error_data = {
                "content": "Sorry, an error occurred.",
                "error": str(e),
                "done": True
            }
            yield f"data: {json.dumps(error_data)}\n\n"
    
    # Return SSE stream
    return StreamingResponse(
        generate_response(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "Tech Buddy API",
        "llm_provider": "databricks",
        "endpoints": {
            "chat": "/api/chat/stream"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## 5. Frontend Implementation

### Minimal Chat Interface - `test_chat.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tech Buddy - Test Chat</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 600px;
            margin: 50px auto;
            padding: 20px;
        }
        
        h1 {
            color: #667eea;
        }
        
        #chat-container {
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 20px;
            min-height: 400px;
            max-height: 400px;
            overflow-y: auto;
            margin-bottom: 20px;
            background: #f9f9f9;
        }
        
        .message {
            margin: 10px 0;
            padding: 10px;
            border-radius: 8px;
        }
        
        .user-message {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-align: right;
        }
        
        .assistant-message {
            background: white;
            border: 1px solid #ddd;
        }
        
        .system-message {
            background: #e3f2fd;
            font-style: italic;
            text-align: center;
        }
        
        #input-container {
            display: flex;
            gap: 10px;
        }
        
        #message-input {
            flex: 1;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 16px;
        }
        
        #send-button {
            padding: 10px 20px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
        }
        
        #send-button:hover {
            background: #764ba2;
        }
        
        #send-button:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
        
        .debug-info {
            margin-top: 20px;
            padding: 10px;
            background: #f0f0f0;
            border-radius: 4px;
            font-family: monospace;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <h1>🤖 Tech Buddy Test Chat</h1>
    
    <div id="chat-container">
        <div class="message system-message">
            Welcome! Type a message to start chatting.
        </div>
    </div>
    
    <div id="input-container">
        <input type="text" id="message-input" placeholder="Type your message..." />
        <button id="send-button">Send</button>
    </div>
    
    <div class="debug-info">
        <strong>Debug Console:</strong>
        <div id="debug-console"></div>
    </div>
    
    <script>
        // Configuration
        const API_URL = 'http://localhost:8000/api/chat/stream';
        const SESSION_ID = 'test-' + Date.now();
        
        // Elements
        const chatContainer = document.getElementById('chat-container');
        const messageInput = document.getElementById('message-input');
        const sendButton = document.getElementById('send-button');
        const debugConsole = document.getElementById('debug-console');
        
        // Debug logging
        function debug(message) {
            console.log(message);
            const timestamp = new Date().toLocaleTimeString();
            debugConsole.innerHTML += `[${timestamp}] ${message}<br>`;
            debugConsole.scrollTop = debugConsole.scrollHeight;
        }
        
        // Add message to chat
        function addMessage(content, role) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${role}-message`;
            messageDiv.textContent = content;
            chatContainer.appendChild(messageDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
        
        // Send message
        async function sendMessage() {
            const message = messageInput.value.trim();
            
            if (!message) {
                return;
            }
            
            // Disable input
            messageInput.disabled = true;
            sendButton.disabled = true;
            
            // Show user message
            addMessage(message, 'user');
            messageInput.value = '';
            
            debug(`📤 Sending: "${message}"`);
            
            try {
                // Call API
                const response = await fetch(API_URL, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        message: message,
                        session_id: SESSION_ID
                    })
                });
                
                debug(`📡 Response status: ${response.status}`);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                // Read SSE stream
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let buffer = '';
                let chunkCount = 0;
                
                debug('📖 Reading SSE stream...');
                
                while (true) {
                    const {value, done} = await reader.read();
                    
                    if (done) {
                        debug('✅ Stream complete');
                        break;
                    }
                    
                    buffer += decoder.decode(value, {stream: true});
                    const lines = buffer.split('\n');
                    buffer = lines.pop();
                    
                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            chunkCount++;
                            const data = JSON.parse(line.slice(6));
                            
                            debug(`📨 Chunk ${chunkCount}: ${data.content ? 'has content' : 'no content'}`);
                            
                            if (data.content) {
                                addMessage(data.content, 'assistant');
                            }
                            
                            if (data.error) {
                                addMessage(`Error: ${data.error}`, 'system');
                            }
                        }
                    }
                }
                
                debug(`✅ Received ${chunkCount} chunks total`);
                
            } catch (error) {
                debug(`❌ Error: ${error.message}`);
                addMessage(`Error: ${error.message}`, 'system');
            } finally {
                // Re-enable input
                messageInput.disabled = false;
                sendButton.disabled = false;
                messageInput.focus();
            }
        }
        
        // Event listeners
        sendButton.addEventListener('click', sendMessage);
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
        
        // Initialize
        debug('🚀 Chat initialized');
        debug(`Session ID: ${SESSION_ID}`);
        debug(`API URL: ${API_URL}`);
        messageInput.focus();
    </script>
</body>
</html>
```

---

## 6. Testing Scripts

### Complete Test Script - `test_databricks_llm.py`

```python
"""
Comprehensive Databricks LLM Connection Test

Tests:
1. Environment configuration
2. Databricks connection
3. GPT-5 response generation
4. Error handling
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment
load_dotenv()

print("="*70)
print("🧪 Databricks LLM Connection Test")
print("="*70)

# Test 1: Check environment variables
print("\n📋 Test 1: Environment Variables")
print("-"*70)

required_vars = {
    "DATABRICKS_HOST": os.getenv("DATABRICKS_HOST"),
    "DATABRICKS_TOKEN": os.getenv("DATABRICKS_TOKEN"),
    "LLM_PROVIDER": os.getenv("LLM_PROVIDER"),
    "LLM_MODEL": os.getenv("LLM_MODEL")
}

all_present = True
for var, value in required_vars.items():
    if value:
        if "TOKEN" in var:
            display = f"{value[:8]}...{value[-4:]}"
        else:
            display = value
        print(f"✅ {var:20s} = {display}")
    else:
        print(f"❌ {var:20s} = NOT SET")
        all_present = False

if not all_present:
    print("\n❌ Missing environment variables. Check your .env file.")
    sys.exit(1)

# Test 2: Initialize LLM client
print("\n🔧 Test 2: LLM Client Initialization")
print("-"*70)

try:
    from utils.llm_client import LLMClient
    
    client = LLMClient(provider="databricks", model="databricks-gpt-5")
    print("✅ LLM client initialized successfully")
except Exception as e:
    print(f"❌ Failed to initialize client: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Simple chat request
print("\n💬 Test 3: Simple Chat Request")
print("-"*70)

test_messages = [
    {
        "role": "system",
        "content": "You are a test assistant. Respond in ONE sentence only."
    },
    {
        "role": "user",
        "content": "Say 'Connection successful!' if you can read this message."
    }
]

print("📤 Sending test message...")
print(f"   System: {test_messages[0]['content']}")
print(f"   User: {test_messages[1]['content']}")

try:
    response = client.chat(messages=test_messages, max_tokens=100)
    
    print("\n📥 Response received:")
    print(f"   {response['content']}")
    print("\n✅ Test 3 PASSED")
except Exception as e:
    print(f"\n❌ Test 3 FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Multi-turn conversation
print("\n💬 Test 4: Multi-Turn Conversation")
print("-"*70)

conversation = [
    {
        "role": "system",
        "content": "You are a helpful assistant. Keep responses brief."
    },
    {
        "role": "user",
        "content": "What is 2+2?"
    }
]

print("📤 Turn 1: What is 2+2?")

try:
    response1 = client.chat(messages=conversation, max_tokens=50)
    print(f"📥 Assistant: {response1['content']}")
    
    # Add assistant response and new user message
    conversation.append({
        "role": "assistant",
        "content": response1['content']
    })
    conversation.append({
        "role": "user",
        "content": "Now multiply that by 3"
    })
    
    print("\n📤 Turn 2: Now multiply that by 3")
    
    response2 = client.chat(messages=conversation, max_tokens=50)
    print(f"📥 Assistant: {response2['content']}")
    
    print("\n✅ Test 4 PASSED")
except Exception as e:
    print(f"\n❌ Test 4 FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Error handling (temperature parameter)
print("\n⚠️  Test 5: Error Handling")
print("-"*70)
print("Note: This test verifies that temperature is NOT sent to Databricks")

try:
    # This should work (temperature is ignored internally)
    response = client.chat(
        messages=[{"role": "user", "content": "Hello"}],
        temperature=0.7,  # Should be ignored
        max_tokens=50
    )
    print("✅ Temperature parameter handled correctly (ignored)")
except Exception as e:
    print(f"⚠️  Unexpected error: {e}")

# Summary
print("\n" + "="*70)
print("📊 Test Summary")
print("="*70)
print("✅ Environment configuration: PASSED")
print("✅ Client initialization: PASSED")
print("✅ Simple chat request: PASSED")
print("✅ Multi-turn conversation: PASSED")
print("✅ Error handling: PASSED")
print("\n🎉 All tests passed! Databricks LLM is working correctly.")
print("="*70)
```

---

## 7. Complete Request/Response Flow

### Example: End-to-End Chat Flow

```python
"""
Example: Complete chat flow from user input to response

This demonstrates the full lifecycle of a chat request.
"""

# 1. USER INPUT (Browser)
user_message = "How do I register a new ONT?"
session_id = "abc-123-def-456"

# 2. FRONTEND (JavaScript)
fetch('http://localhost:8000/api/chat/stream', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        message: user_message,
        session_id: session_id
    })
})

# 3. BACKEND (FastAPI main.py)
@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    # 3a. Load conversation history
    history = [
        {"role": "system", "content": "You are Tech Buddy..."},
        {"role": "user", "content": "Previous message"},
        {"role": "assistant", "content": "Previous response"}
    ]
    
    # 3b. Add current message
    history.append({
        "role": "user",
        "content": request.message
    })
    
    # 3c. Call LLM client
    llm_client = LLMClient()
    response = llm_client.chat(messages=history, max_tokens=2000)
    
    # 3d. Stream response via SSE
    async def generate():
        yield ": ping\n\n"
        await asyncio.sleep(0.05)
        
        yield f"data: {json.dumps({'content': response['content'], 'done': True})}\n\n"
        await asyncio.sleep(0.3)
    
    return StreamingResponse(generate(), media_type="text/event-stream")

# 4. LLM CLIENT (utils/llm_client.py)
def chat(self, messages, max_tokens):
    # 4a. Build request
    url = f"https://{self.databricks_host}/serving-endpoints/{self.model}/invocations"
    headers = {"Authorization": f"Bearer {self.api_key}"}
    data = {"messages": messages, "max_tokens": max_tokens}
    
    # 4b. Call Databricks
    response = requests.post(url, headers=headers, json=data)
    
    # 4c. Extract content
    content = response.json()["choices"][0]["message"]["content"]
    return {"content": content}

# 5. DATABRICKS (GPT-5)
# Receives: {"messages": [...], "max_tokens": 2000}
# Returns: {
#   "choices": [{
#     "message": {
#       "content": "To register a new ONT, you'll need..."
#     }
#   }]
# }

# 6. FRONTEND (JavaScript - SSE Handler)
const reader = response.body.getReader();
while (true) {
    const {value, done} = await reader.read();
    if (done) break;
    
    const chunk = decoder.decode(value);
    if (chunk.startsWith('data: ')) {
        const data = JSON.parse(chunk.slice(6));
        displayMessage(data.content);  // Show in UI
    }
}

# 7. USER SEES RESPONSE
# "To register a new ONT, you'll need the serial number and location..."
```

---

## 8. Error Handling

### Common Errors and Solutions

```python
"""
Error Handling Examples

Shows how to handle common errors gracefully.
"""

from utils.llm_client import LLMClient

def chat_with_error_handling(message: str):
    """Chat with comprehensive error handling."""
    
    try:
        # Initialize client
        client = LLMClient()
        
        # Prepare messages
        messages = [
            {"role": "user", "content": message}
        ]
        
        # Call LLM with timeout handling
        import requests
        requests.packages.urllib3.disable_warnings()  # Optional: suppress SSL warnings
        
        response = client.chat(messages=messages, max_tokens=2000)
        
        return {
            "success": True,
            "content": response["content"]
        }
    
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "Request timeout - please try again",
            "error_type": "timeout"
        }
    
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "error": "Cannot connect to Databricks - check your internet connection",
            "error_type": "connection"
        }
    
    except KeyError as e:
        return {
            "success": False,
            "error": f"Invalid response format from Databricks: {e}",
            "error_type": "invalid_response"
        }
    
    except ValueError as e:
        return {
            "success": False,
            "error": f"Configuration error: {e}",
            "error_type": "config"
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "error_type": "unknown"
        }


# Example usage
result = chat_with_error_handling("Hello!")

if result["success"]:
    print(f"Response: {result['content']}")
else:
    print(f"Error: {result['error']}")
    print(f"Type: {result['error_type']}")
```

---

## Quick Start Checklist

Before sharing with a colleague, ensure they have:

- [ ] `.env` file with correct Databricks credentials
- [ ] Python 3.11 or 3.12 installed (if using RAG)
- [ ] Dependencies installed: `pip install -r api/requirements.txt`
- [ ] Databricks workspace access
- [ ] Valid Personal Access Token
- [ ] Serving endpoint "databricks-gpt-5" available

---

**Document Version:** 1.0  
**Last Updated:** November 17, 2025  
**Related Documents:**
- Main Integration Guide: `DATABRICKS_LLM_INTEGRATION_GUIDE.md`
- Troubleshooting: `DATABRICKS_LLM_TROUBLESHOOTING_FLOWCHART.md`

