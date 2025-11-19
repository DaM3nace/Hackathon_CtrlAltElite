import os
import json
import uuid
from typing import Dict, List, Any
from datetime import datetime
import logging
from conversation_logger import ConversationLogger

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabricksSync:
    """
    Handles syncing conversation data to Databricks tables with DG prefix
    Due to Python 3.14 compatibility issues, this provides SQL generation and CSV export
    for manual import into Databricks
    """
    
    def __init__(self, conversation_logger: ConversationLogger):
        self.conversation_logger = conversation_logger
        self.catalog = os.getenv('DATABRICKS_CATALOG', 'hackathon')
        self.schema = os.getenv('DATABRICKS_SCHEMA', 'hackathon_ctrl_alt_elite')
        
        # Table names with DG prefix
        self.conversations_table = f"{self.catalog}.{self.schema}.DG_CONVERSATIONS"
        self.sources_table = f"{self.catalog}.{self.schema}.DG_CONVERSATION_SOURCES"
        self.metrics_table = f"{self.catalog}.{self.schema}.DG_CONVERSATION_METRICS"
    
    def generate_insert_sql(self) -> str:
        """Generate INSERT SQL statements for all conversation data"""

        export_data = self.conversation_logger.export_for_databricks()

        sql_statements = []

        # Add USE statements at the beginning
        header = f"""-- Insert data into Databricks tables
-- Database: {self.catalog}.{self.schema}

USE CATALOG {self.catalog};
USE SCHEMA {self.schema};

"""
        sql_statements.append(header)

        # Insert statements for DG_CONVERSATIONS
        if export_data['DG_CONVERSATIONS']:
            conversations_sql = """
-- Insert into DG_CONVERSATIONS table
INSERT INTO DG_CONVERSATIONS VALUES
"""
            values = []
            for conv in export_data['DG_CONVERSATIONS']:
                value_str = f"('{conv['conversation_id']}', '{conv['session_id']}', '{conv['user_id']}', '{conv['timestamp']}', {repr(conv['user_query'])}, {repr(conv['bot_response'])}, {conv['query_length']}, {conv['response_length']}, {conv['num_sources']}, {conv['response_time_ms']}, {repr(conv['metadata'])}, '{conv['created_at']}')"
                values.append(value_str)
            
            conversations_sql += ",\n".join(values) + ";\n"
            sql_statements.append(conversations_sql)
        
        # Insert statements for DG_CONVERSATION_SOURCES
        if export_data['DG_CONVERSATION_SOURCES']:
            sources_sql = """
-- Insert into DG_CONVERSATION_SOURCES table
INSERT INTO DG_CONVERSATION_SOURCES VALUES
"""
            values = []
            for source in export_data['DG_CONVERSATION_SOURCES']:
                value_str = f"('{source['conversation_id']}', {source['source_rank']}, '{source['file_name']}', '{source['file_path']}', {source['similarity_score']}, '{source['created_at']}')"
                values.append(value_str)
            
            sources_sql += ",\n".join(values) + ";\n"
            sql_statements.append(sources_sql)
        
        # Insert statements for DG_CONVERSATION_METRICS
        if export_data['DG_CONVERSATION_METRICS']:
            metrics_sql = """
-- Insert into DG_CONVERSATION_METRICS table
INSERT INTO DG_CONVERSATION_METRICS VALUES
"""
            values = []
            for metric in export_data['DG_CONVERSATION_METRICS']:
                value_str = f"('{metric['conversation_id']}', '{metric['session_id']}', '{metric['user_id']}', '{metric['date']}', {metric['query_length']}, {metric['response_length']}, {metric['response_time_ms']}, {metric['num_sources_used']}, '{metric['created_at']}')"
                values.append(value_str)
            
            metrics_sql += ",\n".join(values) + ";\n"
            sql_statements.append(metrics_sql)
        
        return "\n".join(sql_statements)
    
    def generate_reporting_queries(self) -> str:
        """Generate useful reporting queries for Databricks"""
        
        queries = f"""
-- Databricks Reporting Queries for Conversation Analysis

-- 1. Daily conversation volume
SELECT 
    date,
    COUNT(*) as total_conversations,
    COUNT(DISTINCT session_id) as unique_sessions,
    COUNT(DISTINCT user_id) as unique_users,
    AVG(response_time_ms) as avg_response_time_ms,
    AVG(query_length) as avg_query_length,
    AVG(response_length) as avg_response_length
FROM {self.metrics_table}
GROUP BY date
ORDER BY date DESC;

-- 2. Most common queries (by similarity)
SELECT 
    user_query,
    COUNT(*) as frequency,
    AVG(response_time_ms) as avg_response_time,
    AVG(num_sources) as avg_sources_used
FROM {self.conversations_table}
GROUP BY user_query
HAVING COUNT(*) > 1
ORDER BY frequency DESC
LIMIT 20;

-- 3. Source document usage analysis
SELECT 
    file_name,
    COUNT(*) as times_referenced,
    AVG(similarity_score) as avg_similarity,
    COUNT(DISTINCT conversation_id) as unique_conversations
FROM {self.sources_table}
GROUP BY file_name
ORDER BY times_referenced DESC;

-- 4. User engagement patterns
SELECT 
    user_id,
    COUNT(*) as total_queries,
    COUNT(DISTINCT session_id) as sessions,
    MIN(timestamp) as first_interaction,
    MAX(timestamp) as last_interaction,
    AVG(query_length) as avg_query_length
FROM {self.conversations_table}
WHERE user_id != 'anonymous'
GROUP BY user_id
ORDER BY total_queries DESC;

-- 5. Performance metrics over time
SELECT 
    DATE_TRUNC('hour', timestamp) as hour,
    COUNT(*) as conversations_per_hour,
    AVG(response_time_ms) as avg_response_time,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY response_time_ms) as p95_response_time,
    MAX(response_time_ms) as max_response_time
FROM {self.conversations_table}
GROUP BY DATE_TRUNC('hour', timestamp)
ORDER BY hour DESC
LIMIT 24;

-- 6. Quality metrics by source relevance
SELECT 
    CASE 
        WHEN avg_similarity >= 0.8 THEN 'High Relevance (0.8+)'
        WHEN avg_similarity >= 0.6 THEN 'Medium Relevance (0.6-0.8)'
        WHEN avg_similarity >= 0.4 THEN 'Low Relevance (0.4-0.6)'
        ELSE 'Very Low Relevance (<0.4)'
    END as relevance_tier,
    COUNT(*) as conversations,
    AVG(response_length) as avg_response_length
FROM (
    SELECT 
        conversation_id,
        AVG(similarity_score) as avg_similarity,
        MAX(response_length) as response_length
    FROM {self.sources_table} s
    JOIN {self.conversations_table} c ON s.conversation_id = c.conversation_id
    GROUP BY s.conversation_id
) subq
GROUP BY 
    CASE 
        WHEN avg_similarity >= 0.8 THEN 'High Relevance (0.8+)'
        WHEN avg_similarity >= 0.6 THEN 'Medium Relevance (0.6-0.8)'
        WHEN avg_similarity >= 0.4 THEN 'Low Relevance (0.4-0.6)'
        ELSE 'Very Low Relevance (<0.4)'
    END
ORDER BY conversations DESC;

-- 7. Session analysis
SELECT 
    session_id,
    COUNT(*) as interactions_per_session,
    MIN(timestamp) as session_start,
    MAX(timestamp) as session_end,
    DATEDIFF(SECOND, MIN(timestamp), MAX(timestamp)) as session_duration_seconds,
    AVG(response_time_ms) as avg_response_time
FROM {self.conversations_table}
GROUP BY session_id
HAVING COUNT(*) > 1
ORDER BY interactions_per_session DESC
LIMIT 20;
"""
        
        return queries
    
    def export_full_databricks_package(self, output_dir: str = "databricks_package"):
        """Export complete package for Databricks import"""
        
        from pathlib import Path
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # 1. Export CSV files
        csv_path = self.conversation_logger.export_to_csv_for_databricks(str(output_path / "csv_data"))
        
        # 2. Create table schema SQL
        schema_sql = self.conversation_logger.generate_databricks_sql()
        with open(output_path / "01_create_tables.sql", 'w', encoding='utf-8') as f:
            f.write(schema_sql)
        
        # 3. Create data insert SQL  
        insert_sql = self.generate_insert_sql()
        with open(output_path / "02_insert_data.sql", 'w', encoding='utf-8') as f:
            f.write(insert_sql)
        
        # 4. Create reporting queries
        reporting_sql = self.generate_reporting_queries()
        with open(output_path / "03_reporting_queries.sql", 'w', encoding='utf-8') as f:
            f.write(reporting_sql)
        
        # 5. Create README with instructions
        readme_content = f"""
# Databricks Conversation Analytics Package

This package contains conversation data and SQL scripts for importing into Databricks.

## Tables Created (DG Prefix)
- **DG_CONVERSATIONS**: Main conversation records
- **DG_CONVERSATION_SOURCES**: Document sources used for each response  
- **DG_CONVERSATION_METRICS**: Metrics for reporting and analysis

## Files Included
- `csv_data/`: CSV files for data import
- `01_create_tables.sql`: DDL statements to create tables
- `02_insert_data.sql`: INSERT statements for data (alternative to CSV)
- `03_reporting_queries.sql`: Pre-built analytics queries

## Import Instructions

### Option 1: CSV Import (Recommended)
1. Run `01_create_tables.sql` in Databricks to create tables
2. Use Databricks Data Import wizard to import CSV files:
   - Upload `DG_CONVERSATIONS.csv` to `{self.conversations_table}`
   - Upload `DG_CONVERSATION_SOURCES.csv` to `{self.sources_table}`
   - Upload `DG_CONVERSATION_METRICS.csv` to `{self.metrics_table}`

### Option 2: SQL Import
1. Run `01_create_tables.sql` to create tables
2. Run `02_insert_data.sql` to insert data

### Analytics
- Run queries from `03_reporting_queries.sql` for insights
- Create dashboards using the DG tables
- Set up scheduled reports

## Data Summary
- Total Conversations: {len(self.conversation_logger.conversations)}
- Export Timestamp: {datetime.now().isoformat()}
- Tables: DG_CONVERSATIONS, DG_CONVERSATION_SOURCES, DG_CONVERSATION_METRICS
"""
        
        with open(output_path / "README.md", 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        logger.info(f"Complete Databricks package exported to: {output_path}")
        return output_path

def create_databricks_sync_command():
    """Create a command-line utility for syncing conversations to Databricks"""
    
    conversation_logger = ConversationLogger()
    databricks_sync = DatabricksSync(conversation_logger)
    
    # Export the full package
    package_path = databricks_sync.export_full_databricks_package()
    
    print(f"[SUCCESS] Databricks package created: {package_path}")
    print(f"[INFO] {len(conversation_logger.conversations)} conversations exported")
    print(f"[NEXT STEPS]")
    print(f"   1. Upload package to Databricks workspace")
    print(f"   2. Run 01_create_tables.sql to create DG tables")
    print(f"   3. Import CSV data or run 02_insert_data.sql")
    print(f"   4. Use 03_reporting_queries.sql for analytics")

if __name__ == "__main__":
    create_databricks_sync_command()