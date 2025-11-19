#!/usr/bin/env python3
"""
Verify and display the Databricks export package
Shows what would be executed in Databricks
"""

import os
from pathlib import Path

def print_section(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def check_package():
    """Verify package contents"""
    print_section("DATABRICKS PACKAGE VERIFICATION")

    package_dir = Path("databricks_package")

    if not package_dir.exists():
        print("\nERROR: databricks_package directory not found!")
        print("Run: python main.py export-databricks")
        return False

    print("\nPackage location: databricks_package/")
    print("\nContents:")

    files_found = {
        'create_sql': False,
        'insert_sql': False,
        'queries_sql': False,
        'readme': False,
        'csv_dir': False
    }

    # Check SQL files
    if (package_dir / "01_create_tables.sql").exists():
        size = (package_dir / "01_create_tables.sql").stat().st_size
        print(f"  [OK] 01_create_tables.sql ({size} bytes)")
        files_found['create_sql'] = True

    if (package_dir / "02_insert_data.sql").exists():
        size = (package_dir / "02_insert_data.sql").stat().st_size
        print(f"  [OK] 02_insert_data.sql ({size} bytes)")
        files_found['insert_sql'] = True

    if (package_dir / "03_reporting_queries.sql").exists():
        size = (package_dir / "03_reporting_queries.sql").stat().st_size
        print(f"  [OK] 03_reporting_queries.sql ({size} bytes)")
        files_found['queries_sql'] = True

    if (package_dir / "README.md").exists():
        print(f"  [OK] README.md")
        files_found['readme'] = True

    # Check CSV directory
    csv_dir = package_dir / "csv_data"
    if csv_dir.exists():
        print(f"  [OK] csv_data/")
        files_found['csv_dir'] = True

        csv_files = list(csv_dir.glob("*.csv"))
        for csv_file in csv_files:
            size = csv_file.stat().st_size
            print(f"       - {csv_file.name} ({size:,} bytes)")

    return all(files_found.values())

def show_table_ddl():
    """Display table creation statements"""
    print_section("TABLE CREATION STATEMENTS (01_create_tables.sql)")

    sql_file = Path("databricks_package/01_create_tables.sql")
    if sql_file.exists():
        with open(sql_file, 'r', encoding='utf-8') as f:
            content = f.read()

        print("\n" + content)

        # Count statements
        tables = content.count("CREATE TABLE")
        indexes = content.count("CREATE INDEX")
        print(f"\nSummary: {tables} tables, {indexes} indexes")
    else:
        print("\nERROR: 01_create_tables.sql not found")

def show_data_summary():
    """Show summary of data to be imported"""
    print_section("DATA SUMMARY")

    csv_dir = Path("databricks_package/csv_data")

    if not csv_dir.exists():
        print("\nNo CSV data found")
        return

    print("\nCSV Files Ready for Import:")

    # DG_CONVERSATIONS
    conv_file = csv_dir / "DG_CONVERSATIONS.csv"
    if conv_file.exists():
        line_count = len(open(conv_file, encoding='utf-8').readlines()) - 1  # minus header
        size = conv_file.stat().st_size
        print(f"\n1. DG_CONVERSATIONS.csv")
        print(f"   - Records: {line_count}")
        print(f"   - Size: {size:,} bytes")
        print(f"   - Contains: conversation_id, session_id, user_query, bot_response, metrics")

    # DG_CONVERSATION_SOURCES
    sources_file = csv_dir / "DG_CONVERSATION_SOURCES.csv"
    if sources_file.exists():
        line_count = len(open(sources_file, encoding='utf-8').readlines()) - 1
        size = sources_file.stat().st_size
        print(f"\n2. DG_CONVERSATION_SOURCES.csv")
        print(f"   - Records: {line_count}")
        print(f"   - Size: {size:,} bytes")
        print(f"   - Contains: conversation_id, file_name, similarity_score, source_rank")

    # DG_CONVERSATION_METRICS
    metrics_file = csv_dir / "DG_CONVERSATION_METRICS.csv"
    if metrics_file.exists():
        line_count = len(open(metrics_file, encoding='utf-8').readlines()) - 1
        size = metrics_file.stat().st_size
        print(f"\n3. DG_CONVERSATION_METRICS.csv")
        print(f"   - Records: {line_count}")
        print(f"   - Size: {size:,} bytes")
        print(f"   - Contains: conversation_id, date, performance metrics")

def show_sample_data():
    """Show sample data from CSV files"""
    print_section("SAMPLE DATA (First 3 Records)")

    csv_dir = Path("databricks_package/csv_data")

    # Show sample from DG_CONVERSATIONS
    conv_file = csv_dir / "DG_CONVERSATIONS.csv"
    if conv_file.exists():
        print("\nDG_CONVERSATIONS:")
        with open(conv_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()[:4]  # header + 3 rows
            for i, line in enumerate(lines):
                if i == 0:
                    print(f"  Header: {line[:100].strip()}...")
                else:
                    # Show conversation_id and user_query only
                    parts = line.split(',', 5)
                    if len(parts) >= 5:
                        conv_id = parts[0]
                        session_id = parts[1]
                        user_query = parts[4][:50]
                        print(f"  Row {i}: ID={conv_id[:8]}..., Query={user_query}...")

def show_reporting_queries():
    """Display available reporting queries"""
    print_section("PRE-BUILT REPORTING QUERIES (03_reporting_queries.sql)")

    queries_file = Path("databricks_package/03_reporting_queries.sql")
    if queries_file.exists():
        with open(queries_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract query titles
        queries = []
        for line in content.split('\n'):
            if line.startswith('-- ') and any(c.isdigit() for c in line[:10]):
                queries.append(line.strip('- '))

        print("\nAvailable Analytics Queries:")
        for query in queries:
            print(f"  {query}")

        print(f"\nTotal: {len(queries)} pre-built queries")
        print("\nUse these queries in Databricks after importing data to:")
        print("  - Analyze conversation patterns")
        print("  - Track performance metrics")
        print("  - Monitor document usage")
        print("  - Create dashboards")

def show_execution_plan():
    """Show recommended execution steps"""
    print_section("EXECUTION PLAN FOR DATABRICKS")

    print("""
STEP 1: CREATE TABLES IN DATABRICKS
------------------------------------
1. Open Databricks SQL Editor
2. Copy contents of: databricks_package/01_create_tables.sql
3. Update catalog/schema if needed (default: main.default)
4. Execute SQL
5. Verify tables created: SHOW TABLES LIKE 'DG_%';

Expected Result: 3 tables created
  - DG_CONVERSATIONS
  - DG_CONVERSATION_SOURCES
  - DG_CONVERSATION_METRICS


STEP 2: IMPORT DATA (Choose One Method)
----------------------------------------
METHOD A: CSV Import (Recommended)
  1. In Databricks: Data > Create Table > Upload File
  2. Upload databricks_package/csv_data/DG_CONVERSATIONS.csv
  3. Map to DG_CONVERSATIONS table
  4. Repeat for DG_CONVERSATION_SOURCES.csv
  5. Repeat for DG_CONVERSATION_METRICS.csv

METHOD B: SQL Insert
  1. Copy contents of: databricks_package/02_insert_data.sql
  2. Execute in Databricks SQL Editor
  3. Wait for completion


STEP 3: VERIFY DATA
-------------------
Run verification query:
  SELECT
    'DG_CONVERSATIONS' as table_name,
    COUNT(*) as record_count
  FROM DG_CONVERSATIONS
  UNION ALL
  SELECT 'DG_CONVERSATION_SOURCES', COUNT(*) FROM DG_CONVERSATION_SOURCES
  UNION ALL
  SELECT 'DG_CONVERSATION_METRICS', COUNT(*) FROM DG_CONVERSATION_METRICS;


STEP 4: RUN ANALYTICS QUERIES
------------------------------
Copy and run queries from: databricks_package/03_reporting_queries.sql
Start with Query 1: Daily conversation volume


STEP 5: CREATE DASHBOARD (Optional)
------------------------------------
Use the pre-built queries to create visualizations:
  - Line chart: Daily conversation volume
  - Bar chart: Most referenced documents
  - Gauge: Average response time
  - Table: Recent conversations
""")

def generate_quick_commands():
    """Generate quick copy-paste commands"""
    print_section("QUICK REFERENCE COMMANDS")

    print("""
VERIFY TABLES IN DATABRICKS:
-----------------------------
SHOW TABLES LIKE 'DG_%';


CHECK TABLE STRUCTURES:
-----------------------
DESCRIBE EXTENDED DG_CONVERSATIONS;
DESCRIBE EXTENDED DG_CONVERSATION_SOURCES;
DESCRIBE EXTENDED DG_CONVERSATION_METRICS;


COUNT RECORDS:
--------------
SELECT COUNT(*) FROM DG_CONVERSATIONS;
SELECT COUNT(*) FROM DG_CONVERSATION_SOURCES;
SELECT COUNT(*) FROM DG_CONVERSATION_METRICS;


VIEW LATEST DATA:
-----------------
SELECT conversation_id, user_query, response_time_ms, timestamp
FROM DG_CONVERSATIONS
ORDER BY timestamp DESC
LIMIT 10;


SAMPLE ANALYTICS:
-----------------
-- Daily volume
SELECT date, COUNT(*) as conversations
FROM DG_CONVERSATION_METRICS
GROUP BY date
ORDER BY date DESC;

-- Top documents
SELECT file_name, COUNT(*) as usage_count
FROM DG_CONVERSATION_SOURCES
GROUP BY file_name
ORDER BY usage_count DESC
LIMIT 10;
""")

def main():
    print("\n" + "=" * 70)
    print("  DATABRICKS PACKAGE RUNNER")
    print("  Verify and Execute Conversation Analytics Setup")
    print("=" * 70)

    # Step 1: Verify package
    if not check_package():
        print("\nPackage verification failed!")
        return

    # Step 2: Show table DDL
    show_table_ddl()

    # Step 3: Show data summary
    show_data_summary()

    # Step 4: Show sample data
    show_sample_data()

    # Step 5: Show reporting queries
    show_reporting_queries()

    # Step 6: Show execution plan
    show_execution_plan()

    # Step 7: Quick commands
    generate_quick_commands()

    # Final summary
    print_section("SUMMARY")
    print("""
PACKAGE READY FOR DATABRICKS!

Files to use:
  1. databricks_package/01_create_tables.sql - Create DG tables
  2. databricks_package/csv_data/*.csv - Import data
  3. databricks_package/03_reporting_queries.sql - Run analytics

Next Action:
  1. Open Databricks SQL Editor
  2. Copy/paste 01_create_tables.sql
  3. Execute to create tables
  4. Import CSV data or run 02_insert_data.sql
  5. Use 03_reporting_queries.sql for insights

All tables use DG prefix for easy identification!
""")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted!")
    except Exception as e:
        print(f"\nError: {str(e)}")