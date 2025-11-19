# Databricks Setup Files Summary

All files ready for setting up DG-prefixed tables in Databricks.

## Core Setup Files

### 1. setup_databricks_tables.sql
**Purpose:** Complete SQL script to create all DG tables, indexes, and views

**What it creates:**
- 3 tables: DG_CONVERSATIONS, DG_CONVERSATION_SOURCES, DG_CONVERSATION_METRICS
- Indexes for optimal query performance
- 2 views: DG_CONVERSATIONS_WITH_SOURCES, DG_DAILY_METRICS
- Table properties for Delta optimization

**Usage:**
```sql
-- Copy entire file and run in Databricks SQL Editor
-- Update catalog/schema on lines 7-8 if needed
```

**Size:** ~200 lines of SQL
**Execution time:** ~2 minutes

---

### 2. DATABRICKS_SETUP_GUIDE.md
**Purpose:** Comprehensive setup and usage documentation

**Contents:**
- Step-by-step setup instructions
- Table schema documentation
- 6 sample analytics queries
- Dashboard creation guide
- Maintenance tasks (OPTIMIZE, VACUUM, ANALYZE)
- Security and permissions setup
- Data import methods
- Troubleshooting guide

**Use for:** Reference during and after setup

---

### 3. quick_databricks_setup.md
**Purpose:** 5-minute quick start guide

**Contents:**
- Minimal steps to get tables created
- Quick verification queries
- Basic testing
- Fast troubleshooting

**Use for:** Fastest path to working tables

---

## Setup Helper Scripts

### 4. setup_databricks.py
**Purpose:** Interactive Python assistant for setup

**Features:**
- Checks prerequisites
- Shows SQL preview
- Generates connection templates
- Displays table information
- Exports conversation data
- Opens documentation

**Usage:**
```bash
python setup_databricks.py
```

**Note:** Has Unicode issues on some systems, use markdown guides instead

---

### 5. databricks_sync.py
**Purpose:** Handles data export from chatbot to Databricks format

**Features:**
- Exports conversation data to CSV
- Generates INSERT SQL statements
- Creates reporting queries
- Formats data for DG tables
- Includes comprehensive README

**Usage:**
```bash
python main.py export-databricks
# Or
python databricks_sync.py
```

**Output:** `databricks_package/` directory with:
- CSV files for data import
- SQL files for table creation and data insertion
- Pre-built analytics queries
- Setup instructions

---

## Table Schemas

### DG_CONVERSATIONS
```sql
- conversation_id STRING (PK)
- session_id STRING (indexed)
- user_id STRING
- timestamp TIMESTAMP (indexed)
- user_query STRING
- bot_response STRING
- query_length INT
- response_length INT
- num_sources INT
- response_time_ms DOUBLE
- metadata STRING (JSON)
- created_at TIMESTAMP
```

### DG_CONVERSATION_SOURCES
```sql
- conversation_id STRING (FK, indexed)
- source_rank INT
- file_name STRING (indexed)
- file_path STRING
- similarity_score DOUBLE
- created_at TIMESTAMP
```

### DG_CONVERSATION_METRICS
```sql
- conversation_id STRING (FK)
- session_id STRING
- user_id STRING
- date DATE (indexed)
- query_length INT
- response_length INT
- response_time_ms DOUBLE
- num_sources_used INT
- created_at TIMESTAMP
```

---

## Views

### DG_CONVERSATIONS_WITH_SOURCES
Joins conversations with their source documents using COLLECT_LIST.

### DG_DAILY_METRICS
Pre-aggregated daily statistics for dashboards:
- Total conversations
- Unique sessions/users
- Average response times (mean, median, p95)
- Average query/response lengths
- Average sources used

---

## Quick Start Workflow

**Option 1: Tables Only (2 minutes)**
1. Open `setup_databricks_tables.sql`
2. Copy to Databricks SQL Editor
3. Update catalog/schema (lines 7-8)
4. Run All
5. Verify with: `SHOW TABLES LIKE 'DG_%';`

**Option 2: Tables + Data (5 minutes)**
1. Export data: `python main.py export-databricks`
2. Run `databricks_package/01_create_tables.sql`
3. Import CSV files via Data Import wizard
4. Test with sample queries

**Option 3: Guided Setup (10 minutes)**
1. Read `quick_databricks_setup.md`
2. Follow step-by-step instructions
3. Use `DATABRICKS_SETUP_GUIDE.md` for details

---

## Post-Setup Tasks

### Immediate (After Table Creation)
- [ ] Verify tables exist: `SHOW TABLES LIKE 'DG_%';`
- [ ] Check table structures: `DESCRIBE EXTENDED DG_CONVERSATIONS;`
- [ ] Test views work: `SELECT * FROM DG_DAILY_METRICS LIMIT 5;`
- [ ] Import data (if available)

### First Week
- [ ] Create initial dashboard
- [ ] Set up query alerts for errors
- [ ] Grant permissions to users
- [ ] Test all sample queries

### Ongoing
- [ ] Weekly: Run OPTIMIZE on tables
- [ ] Weekly: Update statistics with ANALYZE TABLE
- [ ] Monthly: VACUUM old data
- [ ] Monthly: Review and archive old conversations

---

## File Locations

```
ChatBuddyClaude/
├── setup_databricks_tables.sql          # Main setup script
├── DATABRICKS_SETUP_GUIDE.md            # Detailed documentation
├── quick_databricks_setup.md            # Quick start guide
├── DATABRICKS_FILES_SUMMARY.md          # This file
├── setup_databricks.py                  # Interactive setup helper
├── databricks_sync.py                   # Data export handler
├── conversation_logger.py               # Logs conversations
└── databricks_package/                  # Generated after export
    ├── 01_create_tables.sql
    ├── 02_insert_data.sql
    ├── 03_reporting_queries.sql
    ├── README.md
    └── csv_data/
        ├── DG_CONVERSATIONS.csv
        ├── DG_CONVERSATION_SOURCES.csv
        └── DG_CONVERSATION_METRICS.csv
```

---

## Summary

**All files ready for Databricks setup with DG-prefixed tables!**

**Fastest path:**
1. Copy `setup_databricks_tables.sql` to Databricks
2. Run it
3. Done!

**With data:**
1. Run `python main.py export-databricks`
2. Follow Option 2 workflow above

**Need help:**
- Quick reference: `quick_databricks_setup.md`
- Full details: `DATABRICKS_SETUP_GUIDE.md`