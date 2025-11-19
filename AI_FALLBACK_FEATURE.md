# AI Model Fallback Feature

## Overview

The chatbot now includes an intelligent fallback mechanism that uses **Databricks Foundation Model (databricks-gpt-5-1)** when the knowledge base documents don't provide a good answer.

## How It Works

### 1. **Document Search First**
- The system first searches your knowledge base documents
- Calculates similarity scores for retrieved documents
- Uses semantic search with embeddings

### 2. **Similarity Threshold Check**
- Default threshold: **0.3** (30% similarity)
- If the best matching document is below this threshold, fallback activates
- Configurable via environment variable

### 3. **Intelligent Fallback**
When documents don't match well:
- **Option A**: Low similarity with some context → Databricks model gets partial context + question
- **Option B**: No relevant docs → Databricks model answers from general knowledge
- Clearly indicates the source of the answer

## Configuration

### Environment Variables

Add these to your `.env` file:

```env
# AI Model Fallback Configuration
SIMILARITY_THRESHOLD=0.3          # Minimum similarity score (0.0 to 1.0)
USE_DATABRICKS_FALLBACK=true      # Enable/disable fallback
DATABRICKS_MODEL_ENDPOINT=databricks-gpt-5-1  # Model to use
```

### Adjusting Similarity Threshold

```python
# More strict (only use fallback if very poor match)
SIMILARITY_THRESHOLD=0.1

# Balanced (default)
SIMILARITY_THRESHOLD=0.3

# More aggressive (use fallback more often)
SIMILARITY_THRESHOLD=0.5
```

## Response Indicators

The system clearly indicates which source was used:

### RAG Response (Good Document Match)
```
Based on the available documents, here's what I found:

[Document content...]

Document 1: password_policy.md
Content: Passwords must be at least 12 characters...
Relevance: 0.542
```

### Databricks Model + Context (Partial Match)
```
[AI-generated response using available context]

[Source: RAG + Databricks AI Model]
```

### Databricks Model Only (No Match)
```
[AI-generated response from general knowledge]

[Source: Databricks AI Model - No relevant documents found]
```

## Benefits

### 1. **Better User Experience**
- Always provides an answer, even for questions outside your docs
- No frustrating "I don't know" responses
- Seamless transition between knowledge base and AI

### 2. **Transparency**
- Users know when answers come from docs vs. AI
- Clear source attribution
- Builds trust

### 3. **Cost Optimization**
- Only calls expensive AI model when needed
- Free document search handles most queries
- Logged for analysis

### 4. **Quality Control**
- Similarity scores logged in Databricks
- Track when fallback is used
- Optimize threshold based on real usage

## Logging and Analytics

All responses are logged to Databricks with metadata:

```json
{
  "model_used": "databricks-gpt-5-1",
  "used_fallback": true,
  "similarity_threshold": 0.3,
  "max_similarity": 0.24,
  "response_time_ms": 1250
}
```

### Analytics Queries

**Track fallback usage:**
```sql
SELECT
    DATE(timestamp) as date,
    COUNT(*) as total_queries,
    SUM(CASE WHEN JSON_EXTRACT(metadata, '$.used_fallback') = 'true' THEN 1 ELSE 0 END) as fallback_used,
    AVG(CAST(JSON_EXTRACT(metadata, '$.max_similarity') AS DOUBLE)) as avg_similarity
FROM DG_CONVERSATIONS
GROUP BY DATE(timestamp)
ORDER BY date DESC;
```

**Find queries that needed fallback:**
```sql
SELECT
    user_query,
    JSON_EXTRACT(metadata, '$.max_similarity') as best_match_score,
    response_time_ms
FROM DG_CONVERSATIONS
WHERE JSON_EXTRACT(metadata, '$.used_fallback') = 'true'
ORDER BY timestamp DESC
LIMIT 20;
```

## Testing the Feature

### Test 1: Question in Your Docs (Should NOT use fallback)
```
Question: "What are the password requirements?"
Expected: RAG response with document excerpts
Similarity: >0.3
```

### Test 2: Question NOT in Your Docs (Should use fallback)
```
Question: "What is the capital of France?"
Expected: Databricks AI Model response
Similarity: <0.3
Source indicator: "[Source: Databricks AI Model - No relevant documents found]"
```

### Test 3: Partial Match (May use fallback)
```
Question: "How do quantum computers work in network security?"
Expected: Databricks AI Model with partial context
Source indicator: "[Source: RAG + Databricks AI Model]"
```

## API Response Structure

```python
{
    "query": "user question",
    "response": "generated answer",
    "sources": [...],
    "model_used": "databricks-gpt-5-1" | "rag_local",
    "used_fallback": true | false,
    "response_time_ms": 850,
    "conversation_id": "uuid"
}
```

## Disabling Fallback

To use only your knowledge base (no AI fallback):

```env
USE_DATABRICKS_FALLBACK=false
```

Responses will be:
- Answer from docs if similarity > threshold
- "I couldn't find relevant information" if below threshold

## Error Handling

If Databricks model API fails:
1. Attempts to call the model
2. Logs the error
3. Returns fallback message: "AI model currently unavailable"
4. User can retry or rephrase

## Cost Considerations

### Free Operations
- Document search and embedding generation
- Similarity calculation
- Context formatting

### Paid Operations (Databricks API)
- Only when similarity < threshold
- Typical cost: ~$0.002 per request
- Logged for billing analysis

### Optimization Tips
1. **Lower threshold** (0.1-0.2) = Fewer API calls, more "not found" responses
2. **Higher threshold** (0.4-0.5) = More API calls, always have an answer
3. **Monitor usage** via Databricks logs
4. **Improve docs** to reduce fallback need

## Troubleshooting

### Issue: Fallback always triggers
**Cause**: Similarity threshold too high or poor embeddings
**Solution**:
- Lower SIMILARITY_THRESHOLD to 0.2
- Check knowledge base has documents
- Verify embedding model loaded

### Issue: Fallback never triggers
**Cause**: Threshold too low or token not configured
**Solution**:
- Increase SIMILARITY_THRESHOLD to 0.4
- Verify DATABRICKS_TOKEN is set
- Check USE_DATABRICKS_FALLBACK=true

### Issue: API errors
**Cause**: Invalid token or model endpoint
**Solution**:
- Verify Databricks token is valid
- Check model endpoint name
- Review Databricks API logs

## Security Notes

- Databricks token stored in `.env` (never commit)
- API calls use HTTPS encryption
- User queries sent to Databricks for processing
- Consider data privacy policies
- Audit logs available in Databricks

## Next Steps

1. ✓ Feature implemented and configured
2. → Test with sample queries
3. → Monitor fallback usage in analytics
4. → Adjust similarity threshold based on results
5. → Update knowledge base to reduce fallback need

## Support

For issues or questions:
- Check logs: `conversations.json`
- Review Databricks analytics
- Adjust configuration in `.env`
- Test with CLI: `python main.py ask "your question"`

---

**Feature Status: ACTIVE**
**Default Threshold: 0.3**
**Model: databricks-gpt-5-1**
