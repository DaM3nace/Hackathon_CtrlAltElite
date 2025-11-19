# Execute Databricks Table Setup

## Quick Start - 3 Steps to Complete Setup

### Step 1: Access Databricks SQL Editor
1. Open your Databricks workspace: https://dbc-4a93b454-f17b.cloud.databricks.com
2. Navigate to **SQL Editor** or **SQL Warehouse**
3. Ensure you're connected to your SQL warehouse

### Step 2: Execute Setup Script
Copy and paste the entire contents of `setup_databricks_tables.sql` into the SQL editor and click **Run All**

**File location:** `C:\Users\ftrhack116\ChatBuddyClaude\setup_databricks_tables.sql`

This script will:
- Set the catalog to `hackathon` and schema to `hackathon_ctrl_alt_elite`
- Create 3 tables: DG_CONVERSATIONS, DG_CONVERSATION_SOURCES, DG_CONVERSATION_METRICS
- Create 6 indexes for optimized queries
- Create 2 views for easy data access
- Verify the setup

### Step 3: Load Data (Choose One Option)

#### Option A: CSV Import (Recommended - Fastest)
1. In Databricks, go to **Data** → **Create Table** → **Upload File**
2. Upload these 3 CSV files from `databricks_package/csv_data/`:
   - `DG_CONVERSATIONS.csv` → Import to table `DG_CONVERSATIONS`
   - `DG_CONVERSATION_SOURCES.csv` → Import to table `DG_CONVERSATION_SOURCES`
   - `DG_CONVERSATION_METRICS.csv` → Import to table `DG_CONVERSATION_METRICS`

#### Option B: SQL Insert
1. Open `databricks_package/02_insert_data.sql`
2. Copy and paste into Databricks SQL Editor
3. Click **Run All**

---

## Verification Queries

After setup, run these queries to verify everything works:

### Check Tables Were Created
```sql
USE CATALOG hackathon;
USE SCHEMA hackathon_ctrl_alt_elite;

SHOW TABLES LIKE 'DG_%';
```
**Expected:** 3 tables + 2 views

### Count Records
```sql
SELECT 'DG_CONVERSATIONS' as table_name, COUNT(*) as record_count
FROM DG_CONVERSATIONS
UNION ALL
SELECT 'DG_CONVERSATION_SOURCES', COUNT(*)
FROM DG_CONVERSATION_SOURCES
UNION ALL
SELECT 'DG_CONVERSATION_METRICS', COUNT(*)
FROM DG_CONVERSATION_METRICS;
```
**Expected:** 5 conversations, 25 sources, 5 metrics

### Test Daily Metrics View
```sql
SELECT * FROM DG_DAILY_METRICS;
```
**Expected:** Shows aggregated daily statistics

### View Sample Conversation
```sql
SELECT
    conversation_id,
    user_query,
    SUBSTRING(bot_response, 1, 100) as response_preview,
    response_time_ms,
    num_sources
FROM DG_CONVERSATIONS
ORDER BY timestamp DESC
LIMIT 5;
```

---

## Quick Test: Run a Sample Analytics Query

```sql
-- Top 5 most referenced documents
SELECT
    file_name,
    COUNT(*) as times_used,
    AVG(similarity_score) as avg_similarity
FROM DG_CONVERSATION_SOURCES
GROUP BY file_name
ORDER BY times_used DESC
LIMIT 5;
```

---

## Troubleshooting

### Error: "Catalog does not exist"
**Solution:** Create the catalog first:
```sql
CREATE CATALOG IF NOT EXISTS hackathon;
CREATE SCHEMA IF NOT EXISTS hackathon.hackathon_ctrl_alt_elite;
```

### Error: "Permission denied"
**Solution:** Ensure you have CREATE TABLE permissions in the hackathon catalog

### Tables created but empty
**Solution:** Execute Step 3 (Load Data) to import the conversation data

### CSV Upload Fails
**Solution:**
- Check file encoding is UTF-8
- Try Option B (SQL Insert) instead
- Verify column mapping matches table schema

---

## What Gets Created

### Tables (3)
1. **DG_CONVERSATIONS** - Main conversation records (5 rows)
   - Stores queries, responses, timing, and metadata

2. **DG_CONVERSATION_SOURCES** - Source document references (25 rows)
   - Links conversations to source documents with similarity scores

3. **DG_CONVERSATION_METRICS** - Analytics metrics (5 rows)
   - Optimized for reporting and dashboards

### Indexes (6)
- `idx_dg_conv_session` - On DG_CONVERSATIONS(session_id)
- `idx_dg_conv_timestamp` - On DG_CONVERSATIONS(timestamp)
- `idx_dg_conv_user` - On DG_CONVERSATIONS(user_id)
- `idx_dg_sources_conv` - On DG_CONVERSATION_SOURCES(conversation_id)
- `idx_dg_sources_file` - On DG_CONVERSATION_SOURCES(file_name)
- `idx_dg_metrics_date` - On DG_CONVERSATION_METRICS(date)
- `idx_dg_metrics_session` - On DG_CONVERSATION_METRICS(session_id)

### Views (2)
1. **DG_CONVERSATIONS_WITH_SOURCES** - Conversations joined with their sources
2. **DG_DAILY_METRICS** - Daily aggregated statistics

---

## Next Steps After Setup

1. **Test Queries** - Run the 7 pre-built analytics queries in `databricks_package/03_reporting_queries.sql`

2. **Create Dashboard** - Use Databricks dashboards to visualize:
   - Daily conversation volume
   - Response time trends
   - Most referenced documents
   - User engagement patterns

3. **Set Up Alerts** - Configure alerts for:
   - Response time > 500ms
   - Error rates
   - Unusual activity patterns

4. **Schedule Reports** - Create scheduled jobs to generate reports

---

## Success Criteria

✓ All 3 DG tables exist
✓ All 6 indexes created
✓ Both views accessible
✓ Sample queries return data
✓ Record counts match expected values

---

**Estimated Time:** 5-10 minutes for complete setup

**Database:** `hackathon.hackathon_ctrl_alt_elite`
**Tables:** DG_CONVERSATIONS, DG_CONVERSATION_SOURCES, DG_CONVERSATION_METRICS
