# 🚀 Tech Buddy Chatbot - Complete Build Prompt

**Purpose:** Use this prompt to rebuild the entire Tech Buddy Chatbot project from scratch in a new Cursor workspace.

---

## 📋 PROJECT OVERVIEW

Build a **local-first technical support chatbot** with these capabilities:

### **Core Features:**
1. **Text Chat Interface** - Browser-based chat with streaming responses
2. **Voice Chat Interface** - Real-time voice interaction using OpenAI Realtime API
3. **RAG System** - Retrieval-Augmented Generation over SOP documents
4. **MCP Tools** - Device management tools (register ONT/router, swap ONT, check status, push config)
5. **Conversational Flows** - Multi-step guided interactions for device management
6. **SQLite Databases** - Separate databases for chat history and device management
7. **Test Data Generation** - Generate mock analytics data and retrospective reports
8. **Document Ingestion** - Automatic ingestion of .txt and .docx files from sops/ directory

---

## 🏗️ TECHNOLOGY STACK

### **Backend:**
- **Python 3.9+**
- **FastAPI** - Web framework with SSE streaming
- **SQLAlchemy** - ORM for database operations
- **SQLite** - File-based databases (no external DB server needed)
- **OpenAI Python SDK** - For GPT-4o-mini, embeddings, Realtime API
- **python-docx** - For reading .docx files

### **Frontend:**
- **HTML/CSS/JavaScript** - Native web technologies (no frameworks)
- **Server-Sent Events (SSE)** - For streaming chat responses
- **WebRTC** - For Realtime API voice chat

### **Development:**
- **Windows Batch Scripts** - For easy startup/shutdown
- **dotenv** - Environment variable management

---

## 📁 PROJECT STRUCTURE

```
project_root/
├── api/
│   ├── main.py                 # FastAPI application (1200+ lines)
│   ├── models.py               # SQLAlchemy models
│   ├── database_sqlite.py      # Database connection for chatbot.db
│   ├── rag_sqlite.py           # RAG system with embeddings
│   ├── requirements.txt        # Python dependencies
│   └── static/
│       ├── index.html          # Text chat UI (620+ lines)
│       └── voice.html          # Voice chat UI (900+ lines)
│
├── mcp_server/
│   ├── simple_server.py        # MCP tool implementations (250+ lines)
│   └── mcp_database.py         # Device database operations (500+ lines)
│
├── sops/                       # SOP documents (.txt, .docx)
│
├── .env                        # Environment variables (API keys)
├── chatbot.db                  # Main chat database (SQLite)
├── devices.db                  # Device management database (SQLite)
│
├── start-conda-sqlite.bat      # Start all services (Conda users)
├── stop-conda-sqlite.bat       # Stop all services (Conda users)
├── start.bat                   # Start services (non-Conda)
├── stop.bat                    # Stop services (non-Conda)
│
├── ingest_documents.py         # Manual document ingestion
├── ingest-documents.bat        # Batch file for ingestion
│
├── generate_test_data.py       # Generate test analytics data
├── generate-test-data.bat      # Batch file for test data
├── generate_report.py          # Generate retrospective reports
├── generate-report.bat         # Batch file for reports
│
└── Documentation/
    ├── ARCHITECTURE.md         # System architecture (1500+ lines)
    ├── END_CHAT_FEATURE.md     # End chat button docs
    ├── TEST_DATA_ANALYTICS.md  # Test data generation docs
    └── [20+ other feature docs]
```

---

## 🎯 DETAILED FEATURE SPECIFICATIONS

### **1. TEXT CHAT INTERFACE (api/static/index.html)**

**Requirements:**
- Clean, modern UI with gradient header (purple/blue)
- Message bubbles (user on right, assistant on left)
- Auto-scrolling chat window
- Typing indicator (3 animated dots) during response generation
- Markdown formatting support (bold, italic, code)
- Citations display for RAG responses
- "End Chat" button to reset session (red, next to Send button)
- Welcome message explaining capabilities

**Styling:**
- Purple/blue gradient: `linear-gradient(135deg, #667eea 0%, #764ba2 100%)`
- User messages: Purple gradient background, white text
- Assistant messages: White background, dark text
- System messages: Light blue background
- Rounded corners, smooth animations, modern font

**JavaScript Features:**
- Session ID management (localStorage)
- SSE streaming for responses
- Message history
- Auto-reconnect on server disconnect
- Error handling with user-friendly messages

---

### **2. VOICE CHAT INTERFACE (api/static/voice.html)**

**Requirements:**
- OpenAI Realtime API integration
- Wake word detection: "Hey Buddy"
- Server-side VAD (Voice Activity Detection)
- Function calling for MCP tools
- Two-step activation:
  1. Say "Hey Buddy" to activate
  2. Say anything to hear menu
- Menu-driven approach: "Option 1: Device Management, Option 2: General Help"
- Visual transcript display
- Status indicators (listening, speaking, processing)

**Configuration:**
- Model: `gpt-4o-realtime-preview-2024-10-01`
- Modalities: `['text', 'audio']`
- Voice: `alloy`
- Turn detection: Server VAD with 1200ms silence threshold
- Input audio transcription: Whisper-1

**Session Configuration (Critical):**
- Send `session.update` AFTER receiving `session.created` event
- Include `modalities: ['text', 'audio']` for transcription
- Include all MCP tools in `tools` array
- Use "ON THE FIRST USER TURN" pattern in instructions

---

### **3. RAG SYSTEM (api/rag_sqlite.py)**

**Requirements:**
- Chunk SOP documents into 500-character chunks with 100-char overlap
- Generate embeddings using `text-embedding-3-small`
- Store embeddings as BLOBs in SQLite
- Cosine similarity search for retrieval
- Top-K retrieval (default: 3 chunks)
- Support both .txt and .docx files
- Auto-ingestion on server startup
- Store document metadata (filename, chunk index, text)

**Database Schema (chatbot.db):**
```sql
CREATE TABLE documents (
    id INTEGER PRIMARY KEY,
    filename TEXT,
    content TEXT,
    ingested_at TIMESTAMP
);

CREATE TABLE chunks (
    id INTEGER PRIMARY KEY,
    document_id INTEGER,
    chunk_index INTEGER,
    text TEXT,
    embedding BLOB,
    FOREIGN KEY (document_id) REFERENCES documents(id)
);
```

**Search Process:**
1. Generate query embedding
2. Calculate cosine similarity with all chunk embeddings
3. Return top-K chunks sorted by similarity
4. Include chunk metadata (document, chunk index, similarity score)

---

### **4. MCP TOOLS (mcp_server/)**

**Tool 1: register_ont**
- **Purpose:** Register a new ONT device
- **Required:** serial_number, location
- **Optional:** speed (default: "1000Mbps")
- **Database:** devices.db → ont table
- **Check:** If serial already exists, return "already registered" message
- **Conversational Flow:**
  1. User: "register ONT"
  2. Bot: "What's the serial number?"
  3. User: "ONT-12345"
  4. Bot checks if exists → if not, asks for location
  5. Bot: "Where is it located?"
  6. User: "Building A"
  7. Bot: "What speed?" (or uses default)
  8. Bot: "✅ ONT registered successfully"

**Tool 2: register_router**
- **Purpose:** Register a new router device
- **Required:** serial_number, location
- **Database:** devices.db → router table
- **Similar conversational flow to register_ont**

**Tool 3: swap_ont**
- **Purpose:** Replace faulty ONT with new one
- **Required:** old_serial, new_serial
- **Optional:** new_speed, reason (default: "Device replacement")
- **Process:**
  1. Get old ONT configuration
  2. Mark old ONT status as "replaced"
  3. Register new ONT with same location
  4. Optionally upgrade speed
  5. Log reason in notes
- **Conversational Flow:**
  1. Ask for old serial → validate exists
  2. Ask for new serial → validate not exists
  3. Display both ONT details
  4. Ask if speed change needed
  5. Ask for reason
  6. Execute swap

**Tool 4: device_status**
- **Purpose:** Check device status
- **Required:** serial_number
- **Returns:** Device type, location, status, config

**Tool 5: push_config**
- **Purpose:** Push configuration to device
- **Required:** serial_number
- **Optional:** config (JSON)

---

### **5. DATABASE SCHEMAS**

**chatbot.db (Chat History):**
```sql
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    meta_data TEXT  -- JSON for conversational state
);

CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    role TEXT,
    content TEXT,
    created_at TIMESTAMP
);

CREATE TABLE tool_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    tool_name TEXT,
    arguments TEXT,
    result TEXT,
    timestamp TIMESTAMP
);
```

**devices.db (Device Management):**
```sql
CREATE TABLE ont (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    serial_number TEXT UNIQUE,
    location TEXT,
    status TEXT,
    vlan TEXT,
    speed TEXT,
    port TEXT,
    ont_type TEXT,
    fiber_type TEXT,
    wireless_backup TEXT,
    technician TEXT,
    notes TEXT,
    registered_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE router (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    serial_number TEXT UNIQUE,
    location TEXT,
    status TEXT,
    ip_address TEXT,
    subnet_mask TEXT,
    gateway TEXT,
    dns_primary TEXT,
    dns_secondary TEXT,
    wifi_ssid TEXT,
    wifi_password TEXT,
    notes TEXT,
    registered_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

---

### **6. CONVERSATIONAL STATE MANAGEMENT**

**State Storage:**
- Store in `sessions.meta_data` as JSON
- Example state: `{"flow": "ont_registration", "step": "awaiting_serial", "data": {...}}`

**ONT Registration Flow:**
```python
States:
- "awaiting_serial" → User provides serial, bot checks if exists
- "awaiting_location" → User provides location
- "awaiting_speed" → User provides speed (or default)
- Complete → Execute register_ont tool

Special handling:
- If user types "cancel" at any step → clear state, show cancel message
- Check for duplicates before asking for location
```

**ONT Swap Flow:**
```python
States:
- "awaiting_old_serial" → Validate old ONT exists
- "awaiting_new_serial" → Validate new ONT doesn't exist
- "awaiting_speed" → Ask if speed change needed
- "awaiting_reason" → Get reason for swap
- Complete → Execute swap_ont tool
```

**State Functions:**
```python
def get_session_state(session_id: str, db: Session) -> Dict[str, Any]:
    # Retrieve and parse JSON from sessions.meta_data

def update_session_state(session_id: str, state: Dict[str, Any], db: Session):
    # Store state as JSON in sessions.meta_data

def clear_session_state(session_id: str, db: Session):
    # Set meta_data to empty JSON {}
```

---

### **7. END CHAT FEATURE**

**Frontend:**
- Red button next to Send button: "End Chat"
- Confirmation dialog before execution
- JavaScript handler:
  ```javascript
  1. Call /api/sessions/{session_id}/end
  2. Generate new UUID session ID
  3. Clear localStorage
  4. Clear message UI (keep welcome message)
  5. Show success message
  ```

**Backend:**
- Endpoint: `POST /api/sessions/{session_id}/end`
- Action: Call `clear_session_state()` to reset conversational flows
- Returns: `{"success": true, "message": "Session ended"}`

**Purpose:** Fixes errors when switching between device management and SOP questions by clearing conversational state.

---

### **8. TEST DATA GENERATION**

**generate_test_data.py:**
- Generate 50 user sessions with 10-50 messages each
- Span October 1-31, 2024
- Include realistic tool executions (30% of sessions)
- Tools: register_ont, register_router, swap_ont, device_status, push_config
- Output: test_analytics.db

**generate_report.py:**
- Analyze test_analytics.db
- Generate retrospective report with:
  - Executive summary (sessions, messages, tool usage)
  - Tool usage breakdown with success rates
  - Daily/weekly activity
  - Hourly distribution with ASCII bar charts
  - Top 5 busiest days
  - Key insights and recommendations
- Output: retrospective_report_october_2024.md (Markdown) + .json (JSON)

---

## 🔧 IMPLEMENTATION STEPS

### **STEP 1: Project Setup**

```bash
# Create project structure
mkdir tech_buddy_chatbot
cd tech_buddy_chatbot
mkdir api api/static mcp_server sops

# Create Conda environment
conda create -n techbuddy python=3.9
conda activate techbuddy
```

### **STEP 2: Create .env File**

```env
# .env
OPENAI_API_KEY=your_openai_api_key_here
DATABASE_URL=sqlite:///./chatbot.db
DEVICES_DB_URL=sqlite:///./devices.db
SOPS_DIR=./sops
```

### **STEP 3: Create requirements.txt**

```txt
fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
openai==1.3.5
python-dotenv==1.0.0
sse-starlette==1.8.2
python-docx==1.1.0
numpy==1.24.3
```

Install: `pip install -r api/requirements.txt`

### **STEP 4: Build Core Files**

**Priority Order:**
1. `api/models.py` - SQLAlchemy models (sessions, messages, tool_logs, documents, chunks)
2. `api/database_sqlite.py` - Database connection, init_db() for chatbot.db
3. `mcp_server/mcp_database.py` - Device database operations for devices.db
4. `mcp_server/simple_server.py` - MCP tool implementations
5. `api/rag_sqlite.py` - RAG system with embeddings
6. `api/main.py` - FastAPI application (1200+ lines):
   - Session management
   - Conversational flows (handle_ont_registration_flow, handle_swap_ont_flow)
   - Tool intent detection
   - RAG response generation
   - SSE streaming endpoint
   - Realtime API token endpoint
   - Session end endpoint
7. `api/static/index.html` - Text chat UI (620+ lines)
8. `api/static/voice.html` - Voice chat UI (900+ lines)

### **STEP 5: Create Batch Scripts**

**start-conda-sqlite.bat:**
```batch
@echo off
echo Starting Tech Buddy Chatbot...

REM Activate conda environment
call conda activate techbuddy

REM Start API server
cd api
start "Tech Buddy API" cmd /k "python -m uvicorn main:app --reload --port 8000"

echo.
echo ✓ Tech Buddy Chatbot is running!
echo   • Text Chat: http://localhost:8000/
echo   • Voice Chat: http://localhost:8000/voice
pause
```

**stop-conda-sqlite.bat:**
```batch
@echo off
echo Stopping Tech Buddy Chatbot...

REM Kill Python processes on port 8000
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8000" ^| find "LISTENING"') do taskkill /F /PID %%a

echo ✓ Services stopped
pause
```

### **STEP 6: Document Ingestion**

**ingest_documents.py:**
- Scan sops/ directory for .txt and .docx files
- Chunk documents (500 chars, 100 overlap)
- Generate embeddings
- Store in chatbot.db (documents and chunks tables)
- Skip already ingested files

**ingest-documents.bat:**
- Activate conda
- Run ingest_documents.py
- Show statistics

### **STEP 7: Test Data Generation**

**generate_test_data.py:**
- Configuration: NUM_SESSIONS, MESSAGES_PER_SESSION_RANGE, date range
- Generate realistic conversations
- Simulate tool executions with success/failure
- Output: test_analytics.db

**generate_report.py:**
- Analyze test_analytics.db
- Calculate statistics, trends, success rates
- Generate Markdown report with tables and charts
- Export JSON for programmatic access

---

## 🎨 CRITICAL IMPLEMENTATION DETAILS

### **Voice Chat Session Configuration (MUST GET RIGHT):**

```javascript
// api/static/voice.html

// Wait for session.created before configuring
dataChannel.addEventListener('message', (event) => {
    const message = JSON.parse(event.data);
    
    if (message.type === 'session.created') {
        // NOW configure session
        configureSession();
    }
});

function configureSession() {
    sendRealtimeEvent({
        type: 'session.update',
        session: {
            modalities: ['text', 'audio'],  // CRITICAL for transcription
            turn_detection: {
                type: 'server_vad',
                threshold: 0.5,
                prefix_padding_ms: 300,
                silence_duration_ms: 1200  // Longer pause before response
            },
            voice: 'alloy',
            input_audio_transcription: {
                model: 'whisper-1'
            },
            instructions: `You are Tech Buddy...
            
ON THE FIRST USER TURN (when user says anything after activation):
Read this exact menu:
"Hello! I can help you with two things: Option 1 - Device Management..."`,
            tools: [
                {
                    type: 'function',
                    name: 'register_ont',
                    description: 'Register a new ONT device...',
                    parameters: { /* ... */ }
                },
                // ... other tools
            ],
            tool_choice: 'auto'
        }
    });
}
```

**Wake Word Handling:**
```javascript
// Detect "Hey Buddy" but DON'T process as a turn
if (transcript.includes('hey buddy')) {
    updateStatus('Tech Buddy activated!');
    // Don't add to conversation
    return;  // Let NEXT input be "first user turn"
}
```

### **Tool Parameter Flexibility:**

Both text and voice chatbots should accept:
- `serial_number` (conversational, voice chat)
- `device_id` (legacy, direct tool calls)

```python
# mcp_server/simple_server.py
async def register_ont(args: dict) -> dict:
    # Accept both parameter names
    device_id = args.get("serial_number") or args.get("device_id")
    if not device_id:
        return {"success": False, "error": "Missing serial_number or device_id"}
    # ...
```

### **Conversational Flow Cancel Handling:**

```python
# api/main.py
async def handle_ont_registration_flow(...):
    # Check for cancel BEFORE converting to uppercase
    if message.strip().lower() == "cancel":
        response = "❌ ONT registration cancelled."
        yield {"event": "message", "data": json.dumps({"content": response})}
        update_session_state(session_id, None, db)
        return
    
    # Then continue with normal processing
    serial = message.strip().upper()
    # ...
```

### **RAG Embedding Storage:**

```python
# api/rag_sqlite.py

# Store embeddings as bytes (BLOB)
embedding_bytes = np.array(embedding_vector, dtype=np.float32).tobytes()

chunk = Chunk(
    document_id=doc.id,
    chunk_index=i,
    text=chunk_text,
    embedding=embedding_bytes  # Store as bytes
)

# Retrieve and convert back
chunk_embedding = np.frombuffer(chunk.embedding, dtype=np.float32)
similarity = cosine_similarity(query_embedding, chunk_embedding)
```

---

## 🚨 COMMON PITFALLS TO AVOID

### **1. Voice Chat Transcription Not Working**
- **Problem:** `input_audio_transcription: null` received from OpenAI
- **Solution:** Must include `modalities: ['text', 'audio']` AND send `session.update` AFTER `session.created` event

### **2. State Confusion Between Topics**
- **Problem:** User switches from device management to SOP questions, gets errors
- **Solution:** Implement "End Chat" button that calls `clear_session_state()`

### **3. Cancel Command Not Working**
- **Problem:** "CANCEL" searched in database as serial number
- **Solution:** Check `message.strip().lower() == "cancel"` BEFORE uppercase conversion

### **4. Voice Chat Responding Too Fast**
- **Problem:** Interrupts user mid-sentence (serial numbers)
- **Solution:** Increase `silence_duration_ms` to 1200 and remove manual `response.create` calls

### **5. Embeddings Storage Error**
- **Problem:** SQLite complains about string vs BLOB
- **Solution:** Convert numpy arrays to bytes: `np.array(...).tobytes()`

### **6. Voice Parameter Mismatch**
- **Problem:** Voice sends `serial_number`, backend expects `device_id`
- **Solution:** Accept both parameter names in all MCP tool functions

---

## ✅ TESTING CHECKLIST

### **Text Chat:**
- [ ] Can send messages and receive streaming responses
- [ ] RAG retrieves relevant SOP information
- [ ] "register ONT" starts conversational flow
- [ ] Can cancel mid-flow with "cancel" command
- [ ] "End Chat" button clears state and starts new session
- [ ] Tool executions log to database
- [ ] Citations display correctly

### **Voice Chat:**
- [ ] "Hey Buddy" activates assistant
- [ ] Menu reads on first user input after activation
- [ ] Can register ONT via voice commands
- [ ] Transcription appears in UI
- [ ] Tool functions are called correctly
- [ ] Serial numbers captured fully (1200ms pause works)

### **Device Management:**
- [ ] ONT registration stores in devices.db → ont table
- [ ] Router registration stores in devices.db → router table
- [ ] ONT swap updates old (replaced) and creates new (registered)
- [ ] Speed can be changed during swap
- [ ] Duplicate serial numbers are detected
- [ ] Device status retrieval works

### **Database:**
- [ ] chatbot.db created with correct schema
- [ ] devices.db created with correct schema
- [ ] Sessions, messages, tool_logs populate correctly
- [ ] Embeddings stored as BLOBs
- [ ] Conversational state persists in meta_data

### **Test Data:**
- [ ] generate_test_data.py creates test_analytics.db
- [ ] generate_report.py creates Markdown and JSON reports
- [ ] Reports show realistic statistics

---

## 📚 DOCUMENTATION TO CREATE

After building, create these documentation files:

1. **README.md** - Project overview, quick start, features
2. **ARCHITECTURE.md** - System architecture, components, data flow
3. **END_CHAT_FEATURE.md** - End chat button documentation
4. **TEST_DATA_ANALYTICS.md** - Test data generation guide
5. **VOICE_*.md** - Voice chat implementation details and fixes
6. **SETUP_*.md** - Setup guides for different environments

---

## 🎯 SUCCESS CRITERIA

The project is complete when:

✅ **Text chat works** - Send message, get streaming RAG response  
✅ **Voice chat works** - Say "Hey Buddy", hear menu, use tools  
✅ **Device tools work** - Register ONT/router, swap ONT, check status  
✅ **Conversational flows work** - Multi-step ONT registration and swap  
✅ **End chat resets state** - No errors switching topics  
✅ **Documents ingest** - .txt and .docx files from sops/ directory  
✅ **Test data generates** - Creates analytics and reports  
✅ **Batch scripts work** - Start/stop services easily  
✅ **Databases created** - chatbot.db and devices.db with correct schemas  

---

## 💡 ADDITIONAL NOTES

### **OpenAI API Requirements:**
- GPT-4o-mini for LLM (or gpt-4)
- text-embedding-3-small for embeddings
- gpt-4o-realtime-preview for voice chat
- Ensure Realtime API access is enabled on your account

### **Environment:**
- Tested on Windows 10/11
- Python 3.9+
- Anaconda recommended (but not required)
- Cursor IDE for development

### **Performance:**
- SQLite handles thousands of messages without issues
- Embeddings are fast with small document sets
- Voice chat requires stable internet connection
- Local deployment = no cloud costs except OpenAI API

### **Future Enhancements (Optional):**
- Multi-user support with authentication
- File upload for custom SOPs
- Real-time device monitoring
- Analytics dashboard
- Export conversation history
- Mobile app

---

## 🚀 QUICK START COMMAND SEQUENCE

```bash
# 1. Setup
conda create -n techbuddy python=3.9
conda activate techbuddy
cd project_root
pip install -r api/requirements.txt

# 2. Create .env file with OpenAI API key

# 3. Start services
.\start-conda-sqlite.bat

# 4. Open browser
# Text: http://localhost:8000/
# Voice: http://localhost:8000/voice

# 5. Ingest documents
.\ingest-documents.bat

# 6. Test
# - Chat: "How do I install an OMEGA ONT?"
# - Tools: "register ONT ONT-12345 at Building A"
# - Voice: Say "Hey Buddy" then speak

# 7. Generate test data
.\generate-test-data.bat
.\generate-report.bat
```

---

## 📞 KEY METRICS FOR VALIDATION

After building, verify these metrics match expected behavior:

| Metric | Expected | Check |
|--------|----------|-------|
| Text chat response time | < 3 seconds | Fast streaming |
| Voice activation delay | < 500ms | "Hey Buddy" recognized quickly |
| Tool execution time | < 1 second | Database operations |
| Document ingestion | ~5-10 docs in < 10 seconds | Embedding generation |
| RAG retrieval accuracy | Top-3 chunks relevant | Manual testing |
| Database size (empty) | < 100KB each | Minimal overhead |
| API startup time | < 5 seconds | FastAPI + DB init |

---

**THIS PROMPT CONTAINS EVERYTHING NEEDED TO REBUILD THE TECH BUDDY CHATBOT PROJECT FROM SCRATCH!**

**Total Lines of Code:** ~4,000+ lines across all files  
**Documentation:** 20+ markdown files  
**Databases:** 2 SQLite databases with 5 tables each  
**Features:** 15+ major features  
**Batch Scripts:** 10+ automation scripts  

**Use this prompt with Cursor AI to recreate the entire project step-by-step!** 🚀

