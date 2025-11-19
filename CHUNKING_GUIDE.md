# Knowledge Base Chunking Guide

## Overview

Your ChatBuddy system automatically divides documents into **chunks** for better search and retrieval. This guide explains how chunking works and how to optimize it for your use case.

## Current Status

```
Current Chunks: 22 chunks from 7 documents
Average Size: 1,731 characters (382 tokens)
Range: 170 - 3,467 characters
Configuration: 512 tokens with 50 token overlap
```

## How Chunking Works

### 1. Document Processing Flow

```
┌─────────────────────────────────────────────┐
│  Documents in ./SOP directory               │
│  (PDF, DOCX, TXT, MD, XLSX)                 │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  Extract Text                               │
│  - PDF: PyPDF2                              │
│  - DOCX: python-docx                        │
│  - TXT/MD: plain text                       │
│  - XLSX: pandas                             │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  Split into Paragraphs                      │
│  - Split on double newlines (\n\n)          │
│  - Preserve paragraph structure             │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  Create Chunks                              │
│  - Target: CHUNK_SIZE tokens                │
│  - Overlap: CHUNK_OVERLAP tokens            │
│  - Keep paragraphs together when possible   │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  Generate Embeddings                        │
│  - Model: all-MiniLM-L6-v2 (384 dim)        │
│  - OR: databricks-bge-large-en (1024 dim)   │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  Store in local_vectors.json                │
│  - Content + Metadata + Embedding           │
└─────────────────────────────────────────────┘
```

### 2. Chunking Strategy

**Smart Paragraph-Based Chunking:**
- Splits on paragraph boundaries (double newlines)
- Tries to keep related content together
- Falls back to sentence-level splitting for large paragraphs
- Adds overlap between chunks for context continuity

**Why Overlap Matters:**
- Prevents information loss at chunk boundaries
- Helps with questions that span multiple chunks
- Default: 50 tokens (~200 characters)

## Current Analysis

### Chunk Distribution

```
Distribution by Size:
  Very Small (0-500 chars):     2 chunks (9.1%)
  Small (500-1000 chars):       4 chunks (18.2%)
  Medium (1000-2000 chars):     4 chunks (18.2%)
  Large (2000-3000 chars):     10 chunks (45.5%)
  Very Large (3000+ chars):     2 chunks (9.1%)
```

### Files and Chunks

```
File                                                    Chunks  Avg Size
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
device-status-monitoring.txt                              4    2,212 chars
SOP- Installation of OMEGA ONT.docx                       6    1,479 chars
router-management-guide.md                                4    1,940 chars
SOP-Burying Fiber Drops.docx                              2    2,057 chars
ont-registration-procedure.md                             2    2,275 chars
sample_policy.md                                          2    1,134 chars
README.md                                                 2      836 chars
```

### Observations

✅ **Good:**
- 22 chunks provides reasonable granularity
- Most chunks (45%) are in the optimal "Large" range (2000-3000 chars)
- All documents successfully chunked

⚠️ **Potential Issues:**
- Some chunks are 2x larger than average (3,467 vs 1,731)
- 2 very small chunks (170 chars) - may lack context
- Size variance suggests inconsistent paragraph structure in docs

## Optimization Options

### Option 1: Smaller Chunks (Fine-Grained Search)

**Configuration:**
```env
CHUNK_SIZE=256
CHUNK_OVERLAP=50
```

**Expected Results:**
- ~40-50 chunks (2x current)
- Avg size: ~800-1,000 chars
- More precise retrieval
- Better for specific questions

**Use When:**
- Users ask very specific questions
- Documents contain distinct sections
- You want more search results per query

### Option 2: Current Setting (Balanced) ✅

**Configuration:**
```env
CHUNK_SIZE=512
CHUNK_OVERLAP=50
```

**Current Results:**
- 22 chunks
- Avg size: ~1,731 chars
- Good balance

**Use When:**
- General-purpose chatbot
- Mixed question types
- Current configuration (RECOMMENDED)

### Option 3: Larger Chunks (Broader Context)

**Configuration:**
```env
CHUNK_SIZE=1024
CHUNK_OVERLAP=100
```

**Expected Results:**
- ~10-15 chunks (0.5x current)
- Avg size: ~3,000-4,000 chars
- More context per chunk
- Fewer, broader results

**Use When:**
- Users need comprehensive answers
- Questions require broad context
- Documents are narrative/procedural

## How to Re-Chunk

### Method 1: Analyze First (Recommended)

```bash
# 1. Analyze current chunking
python analyze_chunks.py

# Review the output and decide on new settings
```

### Method 2: Re-Chunk with New Settings

```bash
# 2a. Edit .env file
# Change CHUNK_SIZE and CHUNK_OVERLAP values

# 2b. Run re-chunking script
python rechunk_knowledge_base.py

# Follow the prompts - it will:
# - Backup current chunks to local_vectors.backup.json
# - Re-process all documents
# - Create new chunks with new settings
# - Save to local_vectors.json
```

### Method 3: Re-Chunk with Custom Settings (Advanced)

```bash
# Re-chunk with specific settings (overrides .env)
python rechunk_knowledge_base.py 256 50

# Arguments:
#   256 = chunk size in tokens
#   50 = chunk overlap in tokens
```

### Method 4: Use main.py update

```bash
# This rebuilds the entire knowledge base
python main.py update

# Uses settings from .env file
```

## Testing After Re-Chunking

### 1. Restart Web Server

```bash
# Kill old server
netstat -ano | findstr :8000
taskkill //F //PID <pid>

# Start new server
python web_chat.py
```

### 2. Test Search Quality

Try these test questions:

**Specific Question:**
```
"What are the password requirements?"
```
- Should return specific, relevant chunk
- Check similarity score (should be > 0.5)

**Broad Question:**
```
"How do I install an ONT device?"
```
- Should return multiple relevant chunks
- Check if answer is comprehensive

**Technical Question:**
```
"What steps do I take for device monitoring?"
```
- Should return procedural chunks
- Check if steps are in order

### 3. Check Similarity Scores

```bash
# Test a query and see similarity scores
python -c "from simple_rag_system import SimpleRAGSystem; \
rag = SimpleRAGSystem(); \
result = rag.ask_question('What are password requirements?'); \
print(f'Max Similarity: {result.get(\"max_similarity\", 0):.3f}'); \
print(f'Model Used: {result[\"model_used\"]}'); \
print(f'Used Fallback: {result[\"used_fallback\"]}')"
```

**Ideal Results:**
- High similarity (> 0.5): Document-based answer
- Medium similarity (0.3-0.5): Document with context
- Low similarity (< 0.3): AI fallback triggered

## Troubleshooting

### Issue: Chunks Too Large

**Symptoms:**
- Some chunks > 3,000 characters
- Search returns too much irrelevant content

**Solution:**
```bash
# Reduce chunk size
# Edit .env: CHUNK_SIZE=256
python rechunk_knowledge_base.py
```

### Issue: Chunks Too Small

**Symptoms:**
- Many chunks < 500 characters
- Answers lack context
- Need to retrieve many chunks

**Solution:**
```bash
# Increase chunk size
# Edit .env: CHUNK_SIZE=1024
python rechunk_knowledge_base.py
```

### Issue: Poor Search Results

**Symptoms:**
- Low similarity scores (< 0.3)
- AI fallback triggers too often
- Answers not from documents

**Solutions:**
1. Check document quality - ensure SOPs are well-written
2. Add more documents to knowledge base
3. Adjust chunk size for better granularity
4. Increase chunk overlap (try 100 tokens)

### Issue: Re-Chunking Fails

**Symptoms:**
- Error during re-chunking
- Missing documents
- Encoding errors

**Solutions:**
```bash
# 1. Check documents directory
dir SOP

# 2. Verify .env configuration
type .env | findstr CHUNK

# 3. Restore backup if needed
copy local_vectors.backup.json local_vectors.json
```

## Advanced: Manual Chunk Inspection

### View Specific Chunks

```python
import json

# Load chunks
with open('local_vectors.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    chunks = data['vectors']

# View chunk
chunk = chunks[0]
print(f"File: {chunk['metadata']['file_name']}")
print(f"Size: {len(chunk['content'])} chars")
print(f"Tokens: {chunk['token_count']}")
print(f"Content:\n{chunk['content']}")
```

### Search for Specific Content

```python
import json

with open('local_vectors.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    chunks = data['vectors']

# Find chunks containing keyword
keyword = "password"
matching = [c for c in chunks if keyword.lower() in c['content'].lower()]

print(f"Found {len(matching)} chunks containing '{keyword}'")
for chunk in matching:
    print(f"\nFile: {chunk['metadata']['file_name']}")
    print(f"Preview: {chunk['content'][:200]}...")
```

## Best Practices

### 1. Document Preparation

✅ **Do:**
- Use clear section headers
- Separate topics with blank lines
- Keep paragraphs focused and concise
- Use consistent formatting

❌ **Don't:**
- Create very long paragraphs (> 2000 chars)
- Mix unrelated topics in same paragraph
- Use excessive formatting/special characters

### 2. Chunk Size Selection

| Use Case | Recommended Size | Reasoning |
|----------|-----------------|-----------|
| FAQ/Quick Answers | 256 tokens | Specific, targeted retrieval |
| General KB | 512 tokens | Balanced (CURRENT) |
| Technical Docs | 1024 tokens | Need more context |
| Narrative Docs | 1024-2048 tokens | Story/flow matters |

### 3. Testing Strategy

```bash
# 1. Analyze current chunks
python analyze_chunks.py

# 2. If needed, try smaller chunks first
python rechunk_knowledge_base.py 256 50

# 3. Test with real queries
python web_chat.py

# 4. Monitor similarity scores in conversations.json

# 5. Adjust and repeat
```

### 4. Monitoring

Track these metrics in `conversations.json`:
- `max_similarity`: Should be > 0.3 for document questions
- `used_fallback`: Should be low (< 20%) for document questions
- `model_used`: Should be "rag_local" for document questions

## Summary

**Current Setup:** ✅ Well-balanced, 22 chunks, good distribution

**Recommended Actions:**
1. ✅ Keep current settings (512 tokens) for now
2. Monitor query performance for 1-2 weeks
3. If users report irrelevant results → reduce to 256 tokens
4. If users need more context → increase to 1024 tokens

**Tools Available:**
- `analyze_chunks.py` - Analyze current chunking
- `rechunk_knowledge_base.py` - Re-chunk with new settings
- `main.py update` - Full knowledge base rebuild

**Need Help?**
- Check [text_processor.py](text_processor.py) for chunking logic
- Check [document_processor.py](document_processor.py) for document loading
- Review [local_vectors.json](local_vectors.json) for current chunks

---

**Status:** ✅ Chunking system operational and optimized
**Last Analysis:** Generated from current knowledge base
**Recommendation:** Current settings are well-balanced - monitor and adjust as needed
