# Document Chunking - Quick Reference

## Your Current Setup

```
┌─────────────────────────────────────────────────────┐
│             KNOWLEDGE BASE CHUNKS                   │
├─────────────────────────────────────────────────────┤
│  Total Chunks:     22 chunks                        │
│  Total Documents:  7 files                          │
│  Total Content:    38,090 characters                │
│  Configuration:    512 tokens, 50 overlap           │
└─────────────────────────────────────────────────────┘
```

## What Are Chunks?

Your documents are divided into **chunks** (smaller pieces) to enable:
- ✅ Faster search
- ✅ More relevant results
- ✅ Better context matching

### Example: How a Document Becomes Chunks

```
Original Document: device-status-monitoring.txt (8,850 chars)
                           ↓
              Split into paragraphs
                           ↓
         Group by size (512 tokens max)
                           ↓
           Add overlap (50 tokens)
                           ↓
              Generate embeddings
                           ↓
        ════════════════════════════════
        Chunk 1 (2,321 chars)
        "DEVICE STATUS MONITORING..."
        ────────────────────────────────
        Chunk 2 (2,104 chars) ← 50 token overlap
        "IMMEDIATE ACTIONS..."
        ────────────────────────────────
        Chunk 3 (2,321 chars) ← 50 token overlap
        "ESCALATION PROCEDURES..."
        ────────────────────────────────
        Chunk 4 (2,104 chars) ← 50 token overlap
        "MONITORING TOOLS..."
        ════════════════════════════════
```

## Current Statistics

### Chunk Size Distribution

```
Size Range              Count    Percentage    Quality
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
0-500 chars              2       9.1%          ⚠️  Too Small
500-1000 chars           4       18.2%         ✅ Good
1000-2000 chars          4       18.2%         ✅ Good
2000-3000 chars         10       45.5%         ✅ Excellent
3000+ chars              2       9.1%          ⚠️  Large

Average: 1,731 chars (382 tokens) ✅ OPTIMAL
```

### Files and Their Chunks

```
Document Name                                    Chunks  Size/Chunk
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
device-status-monitoring.txt                        4   2,212 chars
SOP- Installation of OMEGA ONT.docx                 6   1,479 chars
router-management-guide.md                          4   1,940 chars
SOP-Burying Fiber Drops.docx                        2   2,057 chars
ont-registration-procedure.md                       2   2,275 chars
sample_policy.md                                    2   1,134 chars
README.md                                           2     836 chars
```

## Quick Actions

### View Current Chunks

```bash
python analyze_chunks.py
```

**Output:** Detailed analysis of chunk sizes, distribution, and recommendations

### Re-Chunk with Different Settings

```bash
# Option 1: Edit .env file
# Change CHUNK_SIZE=256 or CHUNK_SIZE=1024

# Option 2: Run re-chunking
python rechunk_knowledge_base.py

# Follow prompts - it will backup and re-chunk
```

### Test Chunk Quality

```bash
# Start chatbot
python web_chat.py

# Try these test questions:
# 1. "What are password requirements?" (should find specific chunk)
# 2. "How do I install ONT?" (should find multiple chunks)
# 3. "What is quantum computing?" (should trigger AI fallback)
```

## Chunk Size Guide

### 256 Tokens (~1,024 chars) - Fine-Grained

```
✅ Use When:
   - Users ask specific questions
   - Documents have clear sections
   - Want precise retrieval

❌ Don't Use When:
   - Answers need broad context
   - Documents are narrative
   - Have small number of documents

Expected Result: ~40-50 chunks
```

### 512 Tokens (~2,048 chars) - Balanced ⭐ CURRENT

```
✅ Use When:
   - General-purpose chatbot
   - Mixed question types
   - Good balance of precision and context

✅ Current Status: OPTIMAL

Expected Result: ~20-30 chunks
```

### 1024 Tokens (~4,096 chars) - Broad Context

```
✅ Use When:
   - Need comprehensive answers
   - Procedural documents
   - Narrative content

❌ Don't Use When:
   - Need specific details
   - Want multiple search results

Expected Result: ~10-15 chunks
```

## How Search Works with Chunks

### Step-by-Step Query Process

```
User asks: "What are password requirements?"
                    ↓
        Generate query embedding
                    ↓
    Compare with all 22 chunk embeddings
                    ↓
        Find top 5 most similar chunks
                    ↓
        Calculate similarity scores
                    ↓
┌───────────────────────────────────────────┐
│ Results:                                  │
│ 1. sample_policy.md_1    Score: 0.54 ✅   │
│ 2. sample_policy.md_0    Score: 0.42 ✅   │
│ 3. router-guide.md_2     Score: 0.28 ❌   │
│ 4. device-mon.txt_0      Score: 0.15 ❌   │
│ 5. ont-reg.md_1          Score: 0.08 ❌   │
└───────────────────────────────────────────┘
                    ↓
    Check if max similarity >= 0.3 threshold
                    ↓
         YES → Use document chunks
         NO → Trigger AI fallback
                    ↓
        Generate response with context
```

## Optimization Scenarios

### Scenario 1: Too Many AI Fallbacks

**Symptoms:**
- Similarity scores < 0.3
- AI fallback triggered often
- "AI-generated" responses common

**Solutions:**
```bash
# 1. Make chunks smaller for better matching
# Edit .env: CHUNK_SIZE=256
python rechunk_knowledge_base.py

# 2. Add more documents to knowledge base
# Copy documents to ./SOP directory
python main.py update

# 3. Increase chunk overlap
# Edit .env: CHUNK_OVERLAP=100
python rechunk_knowledge_base.py
```

### Scenario 2: Answers Lack Context

**Symptoms:**
- Retrieved chunks too small
- Answers incomplete
- Users need more detail

**Solutions:**
```bash
# 1. Make chunks larger
# Edit .env: CHUNK_SIZE=1024
python rechunk_knowledge_base.py

# 2. Increase number of retrieved chunks
# Edit simple_rag_system.py
# Change: top_k=5 to top_k=10

# 3. Decrease similarity threshold
# Edit .env: SIMILARITY_THRESHOLD=0.2
```

### Scenario 3: Search Results Too Broad

**Symptoms:**
- Many irrelevant chunks returned
- Similarity scores all similar
- Hard to find specific info

**Solutions:**
```bash
# 1. Make chunks smaller
# Edit .env: CHUNK_SIZE=256
python rechunk_knowledge_base.py

# 2. Increase similarity threshold
# Edit .env: SIMILARITY_THRESHOLD=0.4

# 3. Retrieve fewer chunks
# Edit simple_rag_system.py
# Change: top_k=5 to top_k=3
```

## Configuration Files

### .env - Main Configuration

```env
# Current settings
CHUNK_SIZE=512              # Size in tokens
CHUNK_OVERLAP=50           # Overlap in tokens
DOCUMENTS_DIRECTORY=./SOP   # Where documents are stored
SIMILARITY_THRESHOLD=0.3    # When to trigger AI fallback
```

### local_vectors.json - Stored Chunks

```json
{
  "vectors": [
    {
      "content": "chunk text...",
      "metadata": {
        "file_name": "document.txt",
        "file_path": "C:/path/to/document.txt"
      },
      "token_count": 382,
      "embedding": [...],
      "chunk_id": "document.txt_0"
    }
  ]
}
```

## Monitoring Chunk Performance

### Check conversations.json

```bash
# View recent queries and results
type conversations.json
```

Look for:
- `max_similarity`: Should be > 0.3 for document questions
- `used_fallback`: true = AI used, false = document used
- `model_used`: "rag_local" = documents, "databricks-gpt-5-1" = AI

### Example Good Results

```json
{
  "query": "What are password requirements?",
  "max_similarity": 0.54,
  "used_fallback": false,
  "model_used": "rag_local"
}
```

### Example Poor Results (Needs Adjustment)

```json
{
  "query": "What is the ONT installation process?",
  "max_similarity": 0.18,
  "used_fallback": true,
  "model_used": "databricks-gpt-5-1"
}
```
→ If this happens for document topics, reduce CHUNK_SIZE

## Tools Reference

| Tool | Purpose | Usage |
|------|---------|-------|
| [analyze_chunks.py](analyze_chunks.py) | Analyze current chunks | `python analyze_chunks.py` |
| [rechunk_knowledge_base.py](rechunk_knowledge_base.py) | Re-chunk with new settings | `python rechunk_knowledge_base.py` |
| [text_processor.py](text_processor.py) | Chunking logic | Internal library |
| [document_processor.py](document_processor.py) | Document loading | Internal library |
| main.py update | Full rebuild | `python main.py update` |

## Quick Troubleshooting

| Issue | Quick Fix |
|-------|-----------|
| "No chunks found" | Run: `python main.py update` |
| "Chunks too large" | Edit .env: `CHUNK_SIZE=256`, then re-chunk |
| "Too many fallbacks" | Reduce chunk size or add more docs |
| "Missing context" | Increase chunk size or overlap |
| "Encoding errors" | Ensure all docs are UTF-8 encoded |

## Summary

**Current Status:** ✅ OPTIMAL

Your knowledge base is well-chunked:
- 22 chunks from 7 documents
- Average size: 1,731 chars (good balance)
- Most chunks in optimal range (2000-3000 chars)
- Configuration: 512 tokens (recommended for general use)

**Recommended Actions:**
1. ✅ Monitor for 1-2 weeks
2. Track similarity scores in conversations.json
3. Adjust if needed based on user feedback
4. Run `python analyze_chunks.py` periodically

**No immediate action needed** - your chunking is working well!

---

For detailed information, see [CHUNKING_GUIDE.md](CHUNKING_GUIDE.md)
