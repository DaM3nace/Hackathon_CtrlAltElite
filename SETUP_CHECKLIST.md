# Databricks Setup Checklist

Complete checklist for setting up DG-prefixed tables in Databricks.

## Pre-Setup Requirements

- [ ] Access to Databricks workspace
- [ ] SQL warehouse or compute cluster available
- [ ] Permissions to create tables
- [ ] Know your catalog and schema names

---

## Setup Steps

### Phase 1: Prepare (2 minutes)

- [ ] Open file: `setup_databricks_tables.sql`
- [ ] Review lines 7-8 for catalog/schema names
- [ ] Update if needed:
  ```sql
  USE CATALOG main;        -- Your catalog
  USE SCHEMA default;      -- Your schema
  ```
- [ ] Copy entire SQL script (Ctrl+A, Ctrl+C)

### Phase 2: Execute in Databricks (3 minutes)

- [ ] Open Databricks workspace
- [ ] Navigate to **SQL** > **SQL Editor**
- [ ] Create new query
- [ ] Paste SQL script
- [ ] Click **Run All**
- [ ] Wait for completion (~2 minutes)
- [ ] Check for any errors in output

### Phase 3: Verify Tables (2 minutes)

Run this verification query:
```sql
SHOW TABLES LIKE 'DG_%';
```

Expected results - all 3 tables present:
- [ ] DG_CONVERSATIONS
- [ ] DG_CONVERSATION_SOURCES
- [ ] DG_CONVERSATION_METRICS

Check table structures:
- [ ] `DESCRIBE EXTENDED DG_CONVERSATIONS;`
- [ ] `DESCRIBE EXTENDED DG_CONVERSATION_SOURCES;`
- [ ] `DESCRIBE EXTENDED DG_CONVERSATION_METRICS;`

### Phase 4: Verify Views (1 minute)

- [ ] `SELECT * FROM DG_CONVERSATIONS_WITH_SOURCES LIMIT 5;`
- [ ] `SELECT * FROM DG_DAILY_METRICS LIMIT 5;`

### Phase 5: Import Data (Optional, 5 minutes)

If you have conversation data:

- [ ] Run: `python main.py export-databricks`
- [ ] Locate: `databricks_package/csv_data/`
- [ ] In Databricks: **Data** > **Create Table** > **Upload File**
- [ ] Upload `DG_CONVERSATIONS.csv` → DG_CONVERSATIONS table
- [ ] Upload `DG_CONVERSATION_SOURCES.csv` → DG_CONVERSATION_SOURCES table
- [ ] Upload `DG_CONVERSATION_METRICS.csv` → DG_CONVERSATION_METRICS table
- [ ] Verify data: `SELECT COUNT(*) FROM DG_CONVERSATIONS;`

---

## Post-Setup Tasks

### Immediate Verification

- [ ] Test sample query:
  ```sql
  SELECT conversation_id, user_query, timestamp
  FROM DG_CONVERSATIONS
  ORDER BY timestamp DESC
  LIMIT 10;
  ```

- [ ] Check indexes created:
  ```sql
  SHOW INDEXES FROM DG_CONVERSATIONS;
  ```

- [ ] Verify Delta properties:
  ```sql
  SHOW TBLPROPERTIES DG_CONVERSATIONS;
  ```

### Security Setup

- [ ] Grant SELECT permissions to analyst group:
  ```sql
  GRANT SELECT ON TABLE DG_CONVERSATIONS TO `data_analysts`;
  GRANT SELECT ON TABLE DG_CONVERSATION_SOURCES TO `data_analysts`;
  GRANT SELECT ON TABLE DG_CONVERSATION_METRICS TO `data_analysts`;
  ```

- [ ] Test permissions with analyst account

### First Dashboard (10 minutes)

- [ ] Create new Databricks SQL dashboard
- [ ] Add widget: Daily conversation volume
  ```sql
  SELECT date, total_conversations
  FROM DG_DAILY_METRICS
  WHERE date >= CURRENT_DATE - INTERVAL 30 DAYS
  ORDER BY date DESC;
  ```

- [ ] Add widget: Average response time trend
  ```sql
  SELECT date, avg_response_time_ms
  FROM DG_DAILY_METRICS
  WHERE date >= CURRENT_DATE - INTERVAL 30 DAYS
  ORDER BY date;
  ```

- [ ] Add widget: Most used documents
  ```sql
  SELECT file_name, COUNT(*) as usage_count
  FROM DG_CONVERSATION_SOURCES
  GROUP BY file_name
  ORDER BY usage_count DESC
  LIMIT 10;
  ```

- [ ] Schedule dashboard refresh (e.g., every hour)

---

## Maintenance Setup

### Weekly Tasks

- [ ] Create job: Optimize tables
  ```sql
  OPTIMIZE DG_CONVERSATIONS ZORDER BY (session_id, timestamp);
  OPTIMIZE DG_CONVERSATION_SOURCES ZORDER BY (conversation_id);
  OPTIMIZE DG_CONVERSATION_METRICS ZORDER BY (date);
  ```

- [ ] Create job: Update statistics
  ```sql
  ANALYZE TABLE DG_CONVERSATIONS COMPUTE STATISTICS;
  ANALYZE TABLE DG_CONVERSATION_SOURCES COMPUTE STATISTICS;
  ANALYZE TABLE DG_CONVERSATION_METRICS COMPUTE STATISTICS;
  ```

- [ ] Schedule: Every Sunday at 2 AM

### Monthly Tasks

- [ ] Create job: Vacuum old data
  ```sql
  VACUUM DG_CONVERSATIONS RETAIN 720 HOURS;  -- 30 days
  VACUUM DG_CONVERSATION_SOURCES RETAIN 720 HOURS;
  VACUUM DG_CONVERSATION_METRICS RETAIN 720 HOURS;
  ```

- [ ] Schedule: First day of month at 3 AM

---

## Testing Queries

### Test 1: Recent Conversations
```sql
SELECT COUNT(*) FROM DG_CONVERSATIONS
WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL 24 HOURS;
```
Expected: Count of recent conversations

### Test 2: Join Performance
```sql
SELECT c.conversation_id, c.user_query, s.file_name
FROM DG_CONVERSATIONS c
JOIN DG_CONVERSATION_SOURCES s ON c.conversation_id = s.conversation_id
LIMIT 10;
```
Expected: Fast join, results returned

### Test 3: Aggregation Performance
```sql
SELECT date, COUNT(*) as conversations
FROM DG_CONVERSATION_METRICS
WHERE date >= CURRENT_DATE - INTERVAL 7 DAYS
GROUP BY date;
```
Expected: Quick aggregation

### Test 4: View Performance
```sql
SELECT * FROM DG_DAILY_METRICS
WHERE date >= CURRENT_DATE - INTERVAL 7 DAYS;
```
Expected: Pre-aggregated results

---

## Troubleshooting Checklist

### Tables Not Created
- [ ] Check SQL output for error messages
- [ ] Verify catalog and schema exist
- [ ] Confirm CREATE TABLE permissions
- [ ] Try creating one table at a time

### Index Creation Failed
- [ ] Indexes are optional - can comment out
- [ ] Some Databricks versions don't support all index types
- [ ] Tables work fine without indexes (just slower queries)

### Data Import Failed
- [ ] Check CSV file encoding (should be UTF-8)
- [ ] Verify column mapping matches table schema
- [ ] Try smaller batch of rows first
- [ ] Use SQL INSERT instead of CSV import

### Slow Queries
- [ ] Run OPTIMIZE on tables
- [ ] Run ANALYZE TABLE to update statistics
- [ ] Check if indexes exist
- [ ] Consider partitioning by date

---

## Success Criteria

Setup is complete when:
- [x] All 3 DG tables exist in Databricks
- [x] All indexes created successfully
- [x] Both views return data
- [x] Sample queries execute successfully
- [x] Data imported (if applicable)
- [x] Permissions granted to users
- [x] First dashboard created
- [x] Maintenance jobs scheduled

---

## Next Steps After Setup

1. **Review Analytics Queries**
   - Open `databricks_package/03_reporting_queries.sql`
   - Run 7 pre-built analytics queries
   - Adapt for your dashboards

2. **Set Up Alerts**
   - Alert on high response times
   - Alert on error conversations
   - Alert on zero conversations per day

3. **Document Usage**
   - Share dashboard links with team
   - Document query patterns
   - Create user guide for analysts

4. **Monitor Performance**
   - Track query execution times
   - Monitor table sizes
   - Review optimization impact

---

## Support Resources

- **Quick Start**: `quick_databricks_setup.md`
- **Full Guide**: `DATABRICKS_SETUP_GUIDE.md`
- **File Summary**: `DATABRICKS_FILES_SUMMARY.md`
- **SQL Script**: `setup_databricks_tables.sql`

---

## Completion Signature

- Setup by: ___________________
- Date: ___________________
- Databricks workspace: ___________________
- Catalog.Schema: ___________________
- Tables created: DG_CONVERSATIONS, DG_CONVERSATION_SOURCES, DG_CONVERSATION_METRICS
- Status: [ ] Complete

**Setup complete! DG tables ready for conversation analytics!**