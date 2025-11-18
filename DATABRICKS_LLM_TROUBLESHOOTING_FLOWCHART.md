# 🔍 Databricks LLM Troubleshooting Flowchart

## Quick Diagnosis Decision Tree

```
START: Is the chatbot responding?
│
├─ NO → Is the backend starting without errors?
│   │
│   ├─ NO → Check Python & Dependencies
│   │   │
│   │   ├─ ERROR: "No module named 'databricks'"
│   │   │   └─> SOLUTION: Python 3.14 incompatibility
│   │   │       ├─ Option 1: Install Miniconda + Python 3.11
│   │   │       │   └─> conda create -n techbuddy python=3.11
│   │   │       ├─ Option 2: Use requirements_no_databricks.txt
│   │   │       │   └─> pip install -r api/requirements_no_databricks.txt
│   │   │       └─ Option 3: Download Python 3.11/3.12 installer
│   │   │
│   │   ├─ ERROR: "Address already in use"
│   │   │   └─> SOLUTION: Port 8000 occupied
│   │   │       ├─> Stop existing instance: .\stop.bat
│   │   │       └─> Or use different port: --port 8001
│   │   │
│   │   └─ ERROR: ".env file not found"
│   │       └─> SOLUTION: Create .env file
│   │           └─> See "Creating .env File" section below
│   │
│   └─ YES → Check Backend Logs
│       │
│       ├─ ERROR: "401 Unauthorized"
│       │   └─> Go to "401 Error Flowchart" below
│       │
│       ├─ ERROR: "400 Bad Request"
│       │   └─> Go to "400 Error Flowchart" below
│       │
│       └─ ERROR: "404 Not Found"
│           └─> Go to "404 Error Flowchart" below
│
└─ YES → Great! System is working
    └─> Check "Performance Optimization" section for tuning
```

---

## 401 Unauthorized Error Flowchart

```
401 ERROR: "Credential was not sent or was of an unsupported type"
│
├─ Step 1: Does .env file exist?
│   │
│   ├─ NO → Create .env file
│   │   └─> powershell -Command "Set-Content -Path .env -Value @'
│   │       DATABRICKS_HOST=dbc-4a93b454-f17b.cloud.databricks.com
│   │       DATABRICKS_TOKEN= add token here 
│   │       DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/b914ad7a8dc4d91c
│   │       '@ -Encoding ASCII -NoNewline"
│   │
│   └─ YES → Step 2
│
├─ Step 2: Check .env encoding
│   │
│   ├─ Run: powershell -Command "Get-Content .env -Raw | Format-Hex"
│   │
│   ├─ Contains BOM (EF BB BF at start)?
│   │   └─> YES → PROBLEM FOUND! Recreate with ASCII encoding
│   │       └─> powershell -Command "Set-Content -Path .env -Value (Get-Content .env -Raw) -Encoding ASCII -NoNewline"
│   │
│   └─ NO BOM → Step 3
│
├─ Step 3: Verify token format
│   │
│   ├─ Run: python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(f'Token: {os.getenv(\"DATABRICKS_TOKEN\")}')"
│   │
│   ├─ Output: "Token: None"
│   │   └─> PROBLEM: .env not loading
│   │       ├─> Check file location (must be in project root)
│   │       └─> Check file name (must be exactly ".env")
│   │
│   ├─ Output: "Token: dapixxx..."
│   │   └─> Token loading correctly → Step 4
│   │
│   └─ Output: "Token: your_token_here"
│       └─> PROBLEM: Using placeholder value
│           └─> Replace with actual token from Databricks
│
├─ Step 4: Test connection directly
│   │
│   └─> Run: python test_databricks_llm.py
│       │
│       ├─ Still 401?
│       │   └─> Token is invalid or expired
│       │       ├─> Generate new token in Databricks:
│       │       │   1. Settings → User Settings
│       │       │   2. Access tokens → Generate new token
│       │       │   3. Copy token immediately
│       │       │   4. Update .env
│       │       │
│       │       └─> Verify workspace URL matches token
│       │
│       └─ Success?
│           └─> Token is valid → Problem is elsewhere
│               └─> Check "Backend Not Loading .env" section
│
└─ Step 5: Restart application
    └─> .\restart-stable.bat
```

---

## 400 Bad Request Error Flowchart

```
400 ERROR: "Bad Request"
│
├─ Check error message details
│   │
│   ├─ ERROR: "temperature parameter not supported"
│   │   │
│   │   └─> PROBLEM: Sending temperature to GPT-5
│   │       │
│   │       ├─ Fix in utils/llm_client.py:
│   │       │   │
│   │       │   ├─ FIND:
│   │       │   │   data = {
│   │       │   │       "messages": messages,
│   │       │   │       "temperature": temperature,  # ← REMOVE THIS
│   │       │   │       "max_tokens": max_tokens
│   │       │   │   }
│   │       │   │
│   │       │   └─> REPLACE WITH:
│   │       │       data = {
│   │       │           "messages": messages,
│   │       │           "max_tokens": max_tokens
│   │       │       }
│   │       │
│   │       └─> Restart: .\restart-stable.bat
│   │
│   ├─ ERROR: "Invalid request format"
│   │   │
│   │   └─> PROBLEM: Incorrect message structure
│   │       │
│   │       ├─ Verify messages format:
│   │       │   [
│   │       │     {"role": "system", "content": "..."},
│   │       │     {"role": "user", "content": "..."}
│   │       │   ]
│   │       │
│   │       ├─ Valid roles: "system", "user", "assistant"
│   │       │
│   │       └─> Each message MUST have "role" and "content"
│   │
│   └─ ERROR: "max_tokens exceeds limit"
│       │
│       └─> SOLUTION: Reduce max_tokens
│           └─> In config.py: MAX_TOKENS = 2000 (or lower)
│
└─ Restart and test
    └─> .\restart-stable.bat
```

---

## 404 Not Found Error Flowchart

```
404 ERROR: "Endpoint not found"
│
├─ Check URL in backend logs
│   │
│   ├─ URL ends with "/chat/completions"?
│   │   │
│   │   └─> PROBLEM: Wrong endpoint for Databricks
│   │       │
│   │       ├─ Fix in utils/llm_client.py:
│   │       │   │
│   │       │   ├─ WRONG:
│   │       │   │   url = f"https://{host}/serving-endpoints/{model}/chat/completions"
│   │       │   │
│   │       │   └─> CORRECT:
│   │       │       url = f"https://{host}/serving-endpoints/{model}/invocations"
│   │       │
│   │       └─> Restart: .\restart-stable.bat
│   │
│   ├─ URL contains wrong model name?
│   │   │
│   │   └─> PROBLEM: Model name mismatch
│   │       │
│   │       ├─ Verify in Databricks:
│   │       │   1. Machine Learning → Serving
│   │       │   2. Find your endpoint
│   │       │   3. Copy exact name
│   │       │
│   │       ├─> Update .env:
│   │       │   LLM_MODEL=databricks-gpt-5
│   │       │
│   │       └─> Restart: .\restart-stable.bat
│   │
│   └─ URL uses wrong host?
│       │
│       └─> PROBLEM: Wrong Databricks workspace
│           │
│           ├─> Get correct host:
│           │   1. Open Databricks workspace
│           │   2. Copy URL (e.g., dbc-xxx.cloud.databricks.com)
│           │   3. Remove "https://" prefix
│           │
│           ├─> Update .env:
│           │   DATABRICKS_HOST=dbc-4a93b454-f17b.cloud.databricks.com
│           │
│           └─> Restart: .\restart-stable.bat
│
└─ Verify endpoint exists in Databricks
    └─> Machine Learning → Serving → Endpoints
        ├─> Endpoint exists? → Problem is URL format
        └─> Endpoint missing? → Create serving endpoint first
```

---

## SSE Streaming Issues Flowchart

```
PROBLEM: "Received 0 message chunks" in browser console
│
├─ Check backend logs
│   │
│   ├─ Backend shows "✅ SSE message yielded successfully"?
│   │   │
│   │   └─> YES → PROBLEM: Stream closing too fast
│   │       │
│   │       ├─ Fix in api/main.py (add delays):
│   │       │   │
│   │       │   # Step 1: Send ping
│   │       │   yield ": ping\n\n"
│   │       │   await asyncio.sleep(0.05)
│   │       │   
│   │       │   # Step 2: Send data
│   │       │   yield f"data: {json.dumps(data)}\n\n"
│   │       │   
│   │       │   # Step 3: Keep stream open
│   │       │   await asyncio.sleep(0.3)  # ← Increase if needed
│   │       │
│   │       └─> Restart: .\restart-stable.bat
│   │
│   ├─ Backend shows "Creating EventSourceResponse" BEFORE processing?
│   │   │
│   │   └─> PROBLEM: Response closing before generator runs
│   │       │
│   │       ├─> Switch from EventSourceResponse to StreamingResponse
│   │       │   │
│   │       │   from fastapi.responses import StreamingResponse
│   │       │   
│   │       │   return StreamingResponse(
│   │       │       generate_response(),
│   │       │       media_type="text/event-stream",
│   │       │       headers={
│   │       │           "Cache-Control": "no-cache",
│   │       │           "Connection": "keep-alive",
│   │       │           "X-Accel-Buffering": "no"
│   │       │       }
│   │       │   )
│   │       │
│   │       └─> Restart: .\restart-stable.bat
│   │
│   └─ Backend shows no response processing at all?
│       │
│       └─> PROBLEM: Request not reaching backend
│           │
│           ├─> Check browser console for fetch errors
│           ├─> Verify API endpoint: /api/chat/stream
│           └─> Check CORS if frontend on different port
│
├─ Check browser console for JavaScript errors
│   │
│   ├─> ERROR: "EventSource failed"
│   │   └─> Network issue or wrong URL
│   │       └─> Verify: http://localhost:8000/api/chat/stream
│   │
│   └─> No errors, just 0 chunks?
│       └─> Check SSE format in Network tab
│           ├─> Should see: "data: {...}\n\n"
│           └─> If empty, backend not yielding correctly
│
└─ Test with curl to isolate issue
    │
    └─> curl -N -X POST http://localhost:8000/api/chat/stream \
        -H "Content-Type: application/json" \
        -d '{"message":"hello","session_id":"test-123"}'
        │
        ├─> Receives data? → Frontend issue
        └─> No data? → Backend issue
```

---

## Backend Not Loading .env Flowchart

```
PROBLEM: Backend shows wrong/default values
│
├─ Step 1: Verify .env file location
│   │
│   ├─> Run: dir .env
│   │
│   ├─> File not found?
│   │   └─> Create in project root (same level as api/)
│   │
│   └─> File exists → Step 2
│
├─ Step 2: Check if load_dotenv() is called
│   │
│   ├─> In databricks_config.py:
│   │   │
│   │   from dotenv import load_dotenv
│   │   load_dotenv()  # ← MUST be at module level
│   │   
│   │   class DatabricksConfig:
│   │       def __init__(self):
│   │           self.host = os.getenv("DATABRICKS_HOST")
│   │
│   ├─> In config.py:
│   │   │
│   │   from dotenv import load_dotenv
│   │   load_dotenv()  # ← MUST be at module level
│   │   
│   │   LLM_PROVIDER = os.getenv("LLM_PROVIDER", "databricks")
│   │
│   └─> In utils/llm_client.py:
│       │
│       from dotenv import load_dotenv
│       load_dotenv()  # ← Call before accessing os.getenv()
│
├─ Step 3: Test environment loading
│   │
│   └─> python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('DATABRICKS_HOST'))"
│       │
│       ├─> Output: None
│       │   └─> .env not loading → Check file encoding
│       │       └─> Recreate with ASCII encoding
│       │
│       └─> Output: "dbc-xxx..."
│           └─> .env loading correctly → Check code
│
└─ Step 4: Restart Python process
    │
    ├─> Kill all Python processes
    │   └─> .\stop.bat
    │
    └─> Start fresh
        └─> .\restart-stable.bat
```

---

## Performance Issues Flowchart

```
PROBLEM: Responses are slow or timing out
│
├─ Check response time in backend logs
│   │
│   ├─> > 10 seconds?
│   │   │
│   │   └─> PROBLEM: LLM or network slow
│   │       │
│   │       ├─> Reduce max_tokens:
│   │       │   └─> config.py: MAX_TOKENS = 1000
│   │       │
│   │       ├─> Reduce conversation history:
│   │       │   └─> main.py: Load last 5 messages only
│   │       │
│   │       └─> Check Databricks endpoint status:
│   │           └─> Machine Learning → Serving → Check health
│   │
│   └─> < 2 seconds?
│       └─> Normal performance
│           └─> Check "Optimization Tips" below
│
├─ Check RAG retrieval time
│   │
│   ├─> RAG taking > 3 seconds?
│   │   │
│   │   └─> PROBLEM: Slow vector search
│   │       │
│   │       ├─> Reduce top_k:
│   │       │   └─> config.py: RAG_TOP_K = 3
│   │       │
│   │       ├─> Optimize Databricks tables:
│   │       │   └─> Run: OPTIMIZE hackathon.hackathon_ctrl_alt_elite.embeddings
│   │       │
│   │       └─> Consider indexing chunk_id
│   │
│   └─> RAG disabled?
│       └─> Check: config.py: ENABLE_RAG = True
│
└─ Check database query time
    └─> Add timing logs:
        │
        import time
        start = time.time()
        result = query_database()
        print(f"Query took {time.time() - start:.2f}s")
```

---

## Quick Command Reference

### Diagnosis Commands

```bash
# Test .env loading
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(f'Host: {os.getenv(\"DATABRICKS_HOST\")}')"

# Test Databricks connection
python test_databricks_llm.py

# Check port availability
netstat -ano | findstr :8000

# View backend logs in real-time
# (Start backend, then watch the console window)

# Test API directly with curl
curl -X POST http://localhost:8000/api/chat/stream -H "Content-Type: application/json" -d "{\"message\":\"hello\",\"session_id\":\"test\"}"
```

### Fix Commands

```bash
# Recreate .env with correct encoding
powershell -Command "Set-Content -Path .env -Value (Get-Content .env -Raw) -Encoding ASCII -NoNewline"

# Stop all instances
.\stop.bat

# Restart cleanly
.\restart-stable.bat

# Install dependencies (Python 3.11/3.12)
pip install -r api/requirements.txt

# Install without Databricks (Python 3.14)
pip install -r api/requirements_no_databricks.txt
```

---

## Emergency Checklist

If everything is broken, run through this checklist:

1. ✅ `.env` file exists in project root
2. ✅ `.env` has ASCII encoding (not UTF-8 with BOM)
3. ✅ `DATABRICKS_TOKEN` starts with `dapi`
4. ✅ `DATABRICKS_HOST` has NO `https://` prefix
5. ✅ Python version is 3.11 or 3.12 (not 3.14 for RAG)
6. ✅ All dependencies installed: `pip install -r api/requirements.txt`
7. ✅ `databricks_config.py` has `load_dotenv()` at module level
8. ✅ `utils/llm_client.py` does NOT send `temperature` parameter
9. ✅ API endpoint uses `/invocations` (NOT `/chat/completions`)
10. ✅ SSE streaming has delays (`asyncio.sleep()`)
11. ✅ Port 8000 is not already in use
12. ✅ Restart application after any code changes

---

## Still Stuck?

### Debugging Steps

1. **Enable verbose logging**:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **Add debug prints**:
   ```python
   print(f"DEBUG: Token = {os.getenv('DATABRICKS_TOKEN')[:10]}...")
   print(f"DEBUG: URL = {url}")
   print(f"DEBUG: Response status = {response.status_code}")
   ```

3. **Check file paths**:
   ```python
   from pathlib import Path
   print(f"Working directory: {Path.cwd()}")
   print(f".env exists: {Path('.env').exists()}")
   ```

4. **Test components individually**:
   - Test LLM: `python test_databricks_llm.py`
   - Test RAG: `python test_rag_activation.py`
   - Test API: `curl http://localhost:8000/`

---

**Last Resort**: Start from scratch with a clean environment:

```bash
# Create new conda environment
conda create -n techbuddy-fresh python=3.11 -y
conda activate techbuddy-fresh

# Install dependencies
pip install -r api/requirements.txt

# Recreate .env
# (Copy values from old .env)

# Start fresh
.\restart-stable.bat
```

---

**Document Version:** 1.0  
**Last Updated:** November 17, 2025

