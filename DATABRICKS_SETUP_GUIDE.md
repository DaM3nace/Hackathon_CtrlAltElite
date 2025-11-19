# Databricks Setup Guide for Knowledge Base Chatbot

Complete guide to set up DG-prefixed tables in Databricks for conversation logging and analytics.

## 📋 Prerequisites

- Access to a Databricks workspace
- SQL warehouse or compute cluster
- Permissions to create tables and indexes
- Optional: Catalog and schema creation permissions

## 🚀 Quick Setup (5 Minutes)

### Option 1: Execute SQL Script Directly

1. **Open Databricks SQL Editor**
   - Navigate to your Databricks workspace
   - Go to **SQL** > **SQL Editor**

2. **Update Catalog and Schema** (if needed)
   ```sql
   -- Edit these lines in setup_databricks_tables.sql
   USE CATALOG main;        -- Change if using different catalog
   USE SCHEMA default;      -- Change if using different schema
   ```

3. **Execute Setup Script**
   - Copy contents of `setup_databricks_tables.sql`
   - Paste into SQL Editor
   - Click **Run All**
   - Verify tables created successfully

### Option 2: Import from Chatbot Export

1. **Export conversation data from chatbot**
   ```bash
   python main.py export-databricks
   ```

2. **Locate exported package**
   - Default location: `databricks_package/`
   - Contains: SQL scripts and CSV data

3. **In Databricks SQL Editor**
   - Run `01_create_tables.sql` to create tables
   - Use Data Import wizard for CSV files OR
   - Run `02_insert_data.sql` to insert data

## 📊 Tables Created

### 1. DG_CONVERSATIONS
Main conversation records with full context.

**Columns:**
- `conversation_id` - Unique conversation identifier
- `session_id` - Groups related conversations
- `user_id` - User identifier (default: 'anonymous')
- `timestamp` - When conversation occurred
- `user_query` - Question asked
- `bot_response` - Generated response
- `query_length` - Character count of query
- `response_length` - Character count of response
- `num_sources` - Documents used for answer
- `response_time_ms` - Generation time in milliseconds
- `metadata` - Additional JSON metadata
- `created_at` - Record creation time

**Indexes:**
- `idx_dg_conv_session` on `session_id`
- `idx_dg_conv_timestamp` on `timestamp`
- `idx_dg_conv_user` on `user_id`

### 2. DG_CONVERSATION_SOURCES
Links conversations to source documents.

**Columns:**
- `conversation_id` - Links to DG_CONVERSATIONS
- `source_rank` - Relevance ranking (1 = best)
- `file_name` - Source document name
- `file_path` - Full document path
- `similarity_score` - Semantic similarity score
- `created_at` - Record creation time

**Indexes:**
- `idx_dg_sources_conv` on `conversation_id`
- `idx_dg_sources_file` on `file_name`

### 3. DG_CONVERSATION_METRICS
Optimized for reporting and analytics.

**Columns:**
- `conversation_id` - Links to DG_CONVERSATIONS
- `session_id` - Session identifier
- `user_id` - User identifier
- `date` - Conversation date (for aggregations)
- `query_length` - Query character count
- `response_length` - Response character count
- `response_time_ms` - Performance metric
- `num_sources_used` - Sources count
- `created_at` - Record creation time

**Indexes:**
- `idx_dg_metrics_date` on `date`
- `idx_dg_metrics_session` on `session_id`

## 📈 Pre-built Views

### DG_CONVERSATIONS_WITH_SOURCES
Joins conversations with their source documents.

```sql
SELECT * FROM DG_CONVERSATIONS_WITH_SOURCES
WHERE session_id = 'your-session-id'
ORDER BY timestamp DESC;
```

### DG_DAILY_METRICS
Daily aggregated metrics for dashboards.

```sql
SELECT * FROM DG_DAILY_METRICS
WHERE date >= CURRENT_DATE - INTERVAL 30 DAYS
ORDER BY date DESC;
```

## 🔍 Sample Queries

### 1. Daily Conversation Volume
```sql
SELECT
    date,
    total_conversations,
    unique_sessions,
    avg_response_time_ms
FROM DG_DAILY_METRICS
WHERE date >= CURRENT_DATE - INTERVAL 7 DAYS
ORDER BY date DESC;
```

### 2. Most Asked Questions
```sql
SELECT
    user_query,
    COUNT(*) as frequency,
    AVG(response_time_ms) as avg_response_time,
    AVG(num_sources) as avg_sources
FROM DG_CONVERSATIONS
WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL 30 DAYS
GROUP BY user_query
HAVING COUNT(*) > 1
ORDER BY frequency DESC
LIMIT 20;
```

### 3. Document Usage Analysis
```sql
SELECT
    file_name,
    COUNT(*) as times_used,
    AVG(similarity_score) as avg_similarity,
    COUNT(DISTINCT conversation_id) as unique_conversations
FROM DG_CONVERSATION_SOURCES
GROUP BY file_name
ORDER BY times_used DESC;
```

### 4. Performance Trends
```sql
SELECT
    DATE_TRUNC('hour', timestamp) as hour,
    COUNT(*) as conversations_per_hour,
    AVG(response_time_ms) as avg_response_time,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY response_time_ms) as p95_response_time
FROM DG_CONVERSATIONS
WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL 24 HOURS
GROUP BY DATE_TRUNC('hour', timestamp)
ORDER BY hour DESC;
```

### 5. Session Analysis
```sql
SELECT
    session_id,
    COUNT(*) as interactions,
    MIN(timestamp) as session_start,
    MAX(timestamp) as session_end,
    TIMESTAMPDIFF(SECOND, MIN(timestamp), MAX(timestamp)) as duration_seconds,
    AVG(response_time_ms) as avg_response_time
FROM DG_CONVERSATIONS
GROUP BY session_id
HAVING COUNT(*) > 1
ORDER BY interactions DESC
LIMIT 20;
```

### 6. User Engagement
```sql
SELECT
    user_id,
    COUNT(*) as total_queries,
    COUNT(DISTINCT session_id) as sessions,
    AVG(query_length) as avg_query_length,
    MIN(timestamp) as first_interaction,
    MAX(timestamp) as last_interaction
FROM DG_CONVERSATIONS
WHERE user_id != 'anonymous'
GROUP BY user_id
ORDER BY total_queries DESC;
```

## 📊 Creating Dashboards

### Recommended Dashboard Widgets

1. **Conversation Volume Over Time**
   - Line chart of daily conversations
   - Use: `DG_DAILY_METRICS` view

2. **Average Response Time Trend**
   - Area chart of response times
   - Use: `avg_response_time_ms` from `DG_DAILY_METRICS`

3. **Top Documents by Usage**
   - Bar chart of most referenced files
   - Use: Document usage query above

4. **User Activity Heatmap**
   - Hour-of-day analysis
   - Use: Performance trends query

5. **Query Length Distribution**
   - Histogram of query character counts
   - Use: `query_length` from `DG_CONVERSATION_METRICS`

## 🔧 Maintenance Tasks

### Optimize Tables (Run Weekly)
```sql
OPTIMIZE DG_CONVERSATIONS ZORDER BY (session_id, timestamp);
OPTIMIZE DG_CONVERSATION_SOURCES ZORDER BY (conversation_id);
OPTIMIZE DG_CONVERSATION_METRICS ZORDER BY (date);
```

### Vacuum Old Data (Run Monthly)
```sql
-- Remove files older than 30 days
VACUUM DG_CONVERSATIONS RETAIN 720 HOURS;
VACUUM DG_CONVERSATION_SOURCES RETAIN 720 HOURS;
VACUUM DG_CONVERSATION_METRICS RETAIN 720 HOURS;
```

### Update Statistics (Run Weekly)
```sql
ANALYZE TABLE DG_CONVERSATIONS COMPUTE STATISTICS;
ANALYZE TABLE DG_CONVERSATION_SOURCES COMPUTE STATISTICS;
ANALYZE TABLE DG_CONVERSATION_METRICS COMPUTE STATISTICS;
```

## 🔐 Security Considerations

### Grant Read Access to Users
```sql
GRANT SELECT ON TABLE DG_CONVERSATIONS TO `data_analysts`;
GRANT SELECT ON TABLE DG_CONVERSATION_SOURCES TO `data_analysts`;
GRANT SELECT ON TABLE DG_CONVERSATION_METRICS TO `data_analysts`;
GRANT SELECT ON VIEW DG_CONVERSATIONS_WITH_SOURCES TO `data_analysts`;
GRANT SELECT ON VIEW DG_DAILY_METRICS TO `data_analysts`;
```

### Row-Level Security (Optional)
```sql
-- Restrict users to see only their own data
CREATE OR REPLACE VIEW DG_USER_CONVERSATIONS AS
SELECT * FROM DG_CONVERSATIONS
WHERE user_id = CURRENT_USER();
```

## 📥 Data Import Methods

### Method 1: CSV Import (Recommended for Bulk Data)

1. Navigate to **Data** > **Create Table**
2. Select **Upload File**
3. Upload CSV files from `databricks_package/csv_data/`:
   - `DG_CONVERSATIONS.csv`
   - `DG_CONVERSATION_SOURCES.csv`
   - `DG_CONVERSATION_METRICS.csv`
4. Map columns to existing tables
5. Execute import

### Method 2: SQL INSERT (For Small Datasets)

Run the generated `02_insert_data.sql` from export package.

### Method 3: Streaming from Chatbot (Real-time)

Configure environment variables in chatbot:
```bash
DATABRICKS_SERVER_HOSTNAME=your-workspace.cloud.databricks.com
DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/your-warehouse-id
DATABRICKS_TOKEN=your-access-token
```

## 🧪 Testing the Setup

### Verify Table Creation
```sql
-- Check all DG tables exist
SHOW TABLES LIKE 'DG_%';

-- Check row counts
SELECT 'DG_CONVERSATIONS' as table_name, COUNT(*) as row_count FROM DG_CONVERSATIONS
UNION ALL
SELECT 'DG_CONVERSATION_SOURCES', COUNT(*) FROM DG_CONVERSATION_SOURCES
UNION ALL
SELECT 'DG_CONVERSATION_METRICS', COUNT(*) FROM DG_CONVERSATION_METRICS;
```

### Test Queries
```sql
-- Get latest 10 conversations
SELECT conversation_id, user_query, response_time_ms
FROM DG_CONVERSATIONS
ORDER BY timestamp DESC
LIMIT 10;

-- Check view functionality
SELECT * FROM DG_DAILY_METRICS LIMIT 5;
```

## 🆘 Troubleshooting

### Issue: Tables not found
**Solution:** Verify catalog and schema names in setup script match your environment.

### Issue: Permission denied
**Solution:** Request CREATE TABLE permissions from workspace admin.

### Issue: Index creation fails
**Solution:** Indexes are optional - comment out if not supported in your Databricks version.

### Issue: CSV import fails
**Solution:** Check CSV encoding (should be UTF-8) and delimiter (comma).

## 📞 Support

- Review export logs in `databricks_package/README.md`
- Check pre-built queries in `03_reporting_queries.sql`
- Verify data format in CSV files before import

## ✅ Setup Checklist

- [ ] Execute `setup_databricks_tables.sql` in SQL Editor
- [ ] Verify all 3 tables created: DG_CONVERSATIONS, DG_CONVERSATION_SOURCES, DG_CONVERSATION_METRICS
- [ ] Verify indexes created successfully
- [ ] Test views: DG_CONVERSATIONS_WITH_SOURCES, DG_DAILY_METRICS
- [ ] Import sample data or export from chatbot
- [ ] Run sample queries to verify data
- [ ] Create initial dashboard widgets
- [ ] Grant appropriate permissions
- [ ] Schedule maintenance tasks

**Setup Complete! 🎉**

Your Databricks environment is now ready for chatbot conversation analytics and reporting.