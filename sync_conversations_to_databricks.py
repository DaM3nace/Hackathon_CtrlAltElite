"""
Direct sync of conversations to Databricks tables
"""
import os
import json
import logging
from typing import Dict, List, Any
from datetime import datetime
from dotenv import load_dotenv
import requests
from conversation_logger import ConversationLogger

# Force .env file to override system environment variables
load_dotenv(override=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConversationsDatabricksSync:
    """Sync conversations directly to Databricks tables"""

    def __init__(self):
        self.server_hostname = os.getenv('DATABRICKS_SERVER_HOSTNAME')
        self.http_path = os.getenv('DATABRICKS_HTTP_PATH')
        self.token = os.getenv('DATABRICKS_TOKEN')
        self.catalog = os.getenv('DATABRICKS_CATALOG', 'hackathon')
        self.schema = os.getenv('DATABRICKS_SCHEMA', 'hackathon_ctrl_alt_elite')

        # Table names with DG prefix
        self.conversations_table = f"{self.catalog}.{self.schema}.DG_CONVERSATIONS"
        self.sources_table = f"{self.catalog}.{self.schema}.DG_CONVERSATION_SOURCES"
        self.metrics_table = f"{self.catalog}.{self.schema}.DG_CONVERSATION_METRICS"

        self.api_url = f"https://{self.server_hostname}/api/2.0/sql/statements"

        logger.info(f"Initialized Databricks sync")
        logger.info(f"  Conversations: {self.conversations_table}")
        logger.info(f"  Sources: {self.sources_table}")
        logger.info(f"  Metrics: {self.metrics_table}")

    def execute_sql(self, sql_query: str, wait_timeout: str = "30s") -> Dict[str, Any]:
        """Execute SQL query via Databricks SQL API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }

            payload = {
                "statement": sql_query,
                "warehouse_id": self.http_path.split('/')[-1],
                "wait_timeout": wait_timeout
            }

            response = requests.post(self.api_url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()

            result = response.json()
            return result

        except Exception as e:
            logger.error(f"Error executing SQL: {str(e)}")
            return {"status": "error", "message": str(e)}

    def create_tables_if_not_exist(self) -> bool:
        """Create conversation tables if they don't exist"""
        try:
            logger.info("Creating conversation tables if they don't exist...")

            # Read the table creation SQL
            sql_file = "databricks_package/01_create_tables.sql"
            if not os.path.exists(sql_file):
                logger.error(f"SQL file not found: {sql_file}")
                logger.info("Run: python databricks_sync.py first to generate SQL files")
                return False

            with open(sql_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()

            # Split into individual statements and execute each
            statements = [s.strip() for s in sql_content.split(';') if s.strip() and not s.strip().startswith('--')]

            for stmt in statements:
                if stmt and len(stmt) > 10:  # Skip empty or very short statements
                    result = self.execute_sql(stmt)
                    if result.get('status') == 'error':
                        logger.warning(f"Table creation warning (may already exist): {result.get('message', '')[:100]}")

            logger.info("Tables ready")
            return True

        except Exception as e:
            logger.error(f"Error creating tables: {str(e)}")
            return False

    def clear_existing_data(self) -> bool:
        """Clear existing conversation data (optional, for fresh sync)"""
        try:
            logger.warning("Clearing existing conversation data...")

            # Delete in reverse order of dependencies
            for table in [self.sources_table, self.metrics_table, self.conversations_table]:
                sql = f"DELETE FROM {table}"
                result = self.execute_sql(sql)

                if result.get('status') == 'error':
                    logger.error(f"Failed to clear {table}: {result.get('message')}")
                    return False
                else:
                    logger.info(f"Cleared {table}")

            return True

        except Exception as e:
            logger.error(f"Error clearing data: {str(e)}")
            return False

    def sync_conversations(self, conversation_logger: ConversationLogger, clear_first: bool = False) -> bool:
        """Sync all conversations to Databricks"""
        try:
            if clear_first:
                if not self.clear_existing_data():
                    logger.warning("Failed to clear existing data, continuing anyway...")

            # Get export data
            export_data = conversation_logger.export_for_databricks()

            # Sync conversations
            if export_data['DG_CONVERSATIONS']:
                logger.info(f"Syncing {len(export_data['DG_CONVERSATIONS'])} conversations...")

                for conv in export_data['DG_CONVERSATIONS']:
                    # Escape single quotes
                    conversation_id = conv['conversation_id'].replace("'", "''")
                    session_id = conv['session_id'].replace("'", "''")
                    user_id = conv['user_id'].replace("'", "''")
                    timestamp = conv['timestamp'].replace("'", "''")
                    user_query = conv['user_query'].replace("'", "''")
                    bot_response = conv['bot_response'].replace("'", "''")
                    metadata_str = json.dumps(conv['metadata']).replace("'", "''")
                    created_at = conv['created_at'].replace("'", "''")

                    sql = f"""
                    INSERT INTO {self.conversations_table}
                    (conversation_id, session_id, user_id, timestamp, user_query, bot_response,
                     query_length, response_length, num_sources, response_time_ms, metadata, created_at)
                    VALUES
                    ('{conversation_id}', '{session_id}', '{user_id}', '{timestamp}',
                     '{user_query}', '{bot_response}',
                     {conv['query_length']}, {conv['response_length']}, {conv['num_sources']},
                     {conv['response_time_ms']}, '{metadata_str}', '{created_at}')
                    """

                    result = self.execute_sql(sql)
                    if result.get('status') == 'error':
                        logger.error(f"Failed to sync conversation {conversation_id[:8]}: {result.get('message', '')[:100]}")

                logger.info(f"[OK] Synced {len(export_data['DG_CONVERSATIONS'])} conversations")

            # Sync sources
            if export_data['DG_CONVERSATION_SOURCES']:
                logger.info(f"Syncing {len(export_data['DG_CONVERSATION_SOURCES'])} sources...")

                for source in export_data['DG_CONVERSATION_SOURCES']:
                    conversation_id = source['conversation_id'].replace("'", "''")
                    file_name = source['file_name'].replace("'", "''")
                    file_path = source['file_path'].replace("'", "''")
                    created_at = source['created_at'].replace("'", "''")

                    sql = f"""
                    INSERT INTO {self.sources_table}
                    (conversation_id, source_rank, file_name, file_path, similarity_score, created_at)
                    VALUES
                    ('{conversation_id}', {source['source_rank']}, '{file_name}', '{file_path}',
                     {source['similarity_score']}, '{created_at}')
                    """

                    result = self.execute_sql(sql)
                    if result.get('status') == 'error':
                        logger.error(f"Failed to sync source: {result.get('message', '')[:100]}")

                logger.info(f"[OK] Synced {len(export_data['DG_CONVERSATION_SOURCES'])} sources")

            # Sync metrics
            if export_data['DG_CONVERSATION_METRICS']:
                logger.info(f"Syncing {len(export_data['DG_CONVERSATION_METRICS'])} metrics...")

                for metric in export_data['DG_CONVERSATION_METRICS']:
                    conversation_id = metric['conversation_id'].replace("'", "''")
                    session_id = metric['session_id'].replace("'", "''")
                    user_id = metric['user_id'].replace("'", "''")
                    date = metric['date'].replace("'", "''")
                    created_at = metric['created_at'].replace("'", "''")

                    sql = f"""
                    INSERT INTO {self.metrics_table}
                    (conversation_id, session_id, user_id, date, query_length, response_length,
                     response_time_ms, num_sources_used, created_at)
                    VALUES
                    ('{conversation_id}', '{session_id}', '{user_id}', '{date}',
                     {metric['query_length']}, {metric['response_length']},
                     {metric['response_time_ms']}, {metric['num_sources_used']}, '{created_at}')
                    """

                    result = self.execute_sql(sql)
                    if result.get('status') == 'error':
                        logger.error(f"Failed to sync metric: {result.get('message', '')[:100]}")

                logger.info(f"[OK] Synced {len(export_data['DG_CONVERSATION_METRICS'])} metrics")

            return True

        except Exception as e:
            logger.error(f"Error syncing conversations: {str(e)}")
            return False

    def verify_sync(self) -> Dict[str, int]:
        """Verify conversation data in Databricks"""
        counts = {}

        for table_name, table in [
            ('conversations', self.conversations_table),
            ('sources', self.sources_table),
            ('metrics', self.metrics_table)
        ]:
            sql = f"SELECT COUNT(*) FROM {table}"
            result = self.execute_sql(sql)

            if 'result' in result and 'data_array' in result['result']:
                count = result['result']['data_array'][0][0]
                counts[table_name] = int(count) if count is not None else 0
            else:
                counts[table_name] = 0

        return counts


if __name__ == "__main__":
    print("=" * 80)
    print("SYNC CONVERSATIONS TO DATABRICKS")
    print("=" * 80)
    print()

    # Load conversations
    conversation_logger = ConversationLogger()
    print(f"Loaded {len(conversation_logger.conversations)} conversations from local storage")
    print()

    # Initialize sync
    sync = ConversationsDatabricksSync()
    print()

    # Create tables if needed
    print("Step 1: Ensuring tables exist...")
    if not sync.create_tables_if_not_exist():
        print("[FAILED] Could not create tables")
        exit(1)
    print()

    # Sync conversations
    print("Step 2: Syncing conversations to Databricks...")
    clear_first = False  # Set to True to clear existing data first
    if sync.sync_conversations(conversation_logger, clear_first=clear_first):
        print("[OK] Conversations synced successfully")
    else:
        print("[FAILED] Sync failed")
        exit(1)
    print()

    # Verify
    print("Step 3: Verifying data in Databricks...")
    counts = sync.verify_sync()
    print(f"  Conversations: {counts.get('conversations', 0)}")
    print(f"  Sources: {counts.get('sources', 0)}")
    print(f"  Metrics: {counts.get('metrics', 0)}")
    print()

    print("=" * 80)
    print("[SUCCESS] Conversations stored in Databricks!")
    print("=" * 80)
    print()
    print("Query your data:")
    print(f"  SELECT * FROM {sync.conversations_table} LIMIT 10;")
    print()
