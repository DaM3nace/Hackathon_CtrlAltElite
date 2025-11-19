# Quick Databricks Setup - 5 Minutes

## Step 1: Copy SQL Script (1 minute)

1. Open file: `setup_databricks_tables.sql`
2. Copy entire contents (Ctrl+A, Ctrl+C)

## Step 2: Open Databricks (1 minute)

1. Navigate to your Databricks workspace
2. Go to **SQL** > **SQL Editor**
3. Create new query

## Step 3: Update Settings (1 minute)

Update lines 7-8 if needed:
```sql
USE CATALOG main;        -- Change to your catalog
USE SCHEMA default;      -- Change to your schema
```

## Step 4: Execute Script (2 minutes)

1. Paste SQL into editor
2. Click **Run All**
3. Wait for completion

## Verification

Run this query to verify:
```sql
SHOW TABLES LIKE 'DG_%';
```

You should see:
- DG_CONVERSATIONS
- DG_CONVERSATION_SOURCES
- DG_CONVERSATION_METRICS

## What Gets Created

**Tables:**
- `DG_CONVERSATIONS` - Main conversation records
- `DG_CONVERSATION_SOURCES` - Source document links
- `DG_CONVERSATION_METRICS` - Analytics data

**Views:**
- `DG_CONVERSATIONS_WITH_SOURCES` - Joined data
- `DG_DAILY_METRICS` - Daily summaries

**Indexes:**
- Optimized for session_id, timestamp, date queries

## Import Data (Optional)

If you have exported conversation data:

1. Run export command:
   ```bash
   python main.py export-databricks
   ```

2. In Databricks, go to **Data** > **Create Table** > **Upload File**

3. Upload these CSV files:
   - `databricks_package/csv_data/DG_CONVERSATIONS.csv`
   - `databricks_package/csv_data/DG_CONVERSATION_SOURCES.csv`
   - `databricks_package/csv_data/DG_CONVERSATION_METRICS.csv`

4. Map to existing tables

## Test Query

```sql
-- Get latest conversations
SELECT
    conversation_id,
    user_query,
    response_time_ms,
    timestamp
FROM DG_CONVERSATIONS
ORDER BY timestamp DESC
LIMIT 10;
```

## Daily Metrics

```sql
-- View daily statistics
SELECT * FROM DG_DAILY_METRICS
WHERE date >= CURRENT_DATE - INTERVAL 7 DAYS
ORDER BY date DESC;
```

## Done!

Your Databricks tables are now ready for conversation analytics.

## Next Steps

1. Create dashboard using DG_DAILY_METRICS view
2. Set up alerts for performance metrics
3. Schedule weekly OPTIMIZE jobs
4. Review pre-built queries in `03_reporting_queries.sql`

## Troubleshooting

**Tables not found?**
- Check catalog and schema names match your environment

**Permission denied?**
- Request CREATE TABLE permissions from admin

**Index errors?**
- Indexes are optional, can comment out if issues

## Support Files

- **setup_databricks_tables.sql** - Main setup script
- **DATABRICKS_SETUP_GUIDE.md** - Detailed documentation
- **03_reporting_queries.sql** - Pre-built analytics queries (after export)