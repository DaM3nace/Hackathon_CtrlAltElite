import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConversationLogger:
    def __init__(self, local_storage_file: str = "conversations.json"):
        self.local_storage_file = local_storage_file
        self.conversations = []
        self.load_local_conversations()
    
    def load_local_conversations(self):
        """Load conversations from local JSON file"""
        if Path(self.local_storage_file).exists():
            try:
                with open(self.local_storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.conversations = data.get('conversations', [])
                logger.info(f"Loaded {len(self.conversations)} conversations from local storage")
            except Exception as e:
                logger.error(f"Error loading conversations: {str(e)}")
                self.conversations = []
    
    def save_local_conversations(self):
        """Save conversations to local JSON file"""
        try:
            data = {
                'conversations': self.conversations,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.local_storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving conversations: {str(e)}")
    
    def log_conversation(self, 
                        session_id: str,
                        user_query: str, 
                        bot_response: str, 
                        sources: List[Dict[str, Any]],
                        response_time_ms: float = 0,
                        user_id: str = "anonymous",
                        metadata: Optional[Dict[str, Any]] = None) -> str:
        """Log a conversation exchange"""
        
        conversation_id = str(uuid.uuid4())
        timestamp = datetime.now()
        
        conversation_record = {
            'conversation_id': conversation_id,
            'session_id': session_id,
            'user_id': user_id,
            'timestamp': timestamp.isoformat(),
            'user_query': user_query,
            'bot_response': bot_response,
            'sources': sources,
            'response_time_ms': response_time_ms,
            'query_length': len(user_query),
            'response_length': len(bot_response),
            'num_sources': len(sources),
            'metadata': metadata or {}
        }
        
        # Add to local storage
        self.conversations.append(conversation_record)
        self.save_local_conversations()
        
        logger.info(f"Logged conversation {conversation_id} for session {session_id}")
        return conversation_id
    
    def get_session_history(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get conversation history for a session"""
        session_conversations = [
            conv for conv in self.conversations 
            if conv.get('session_id') == session_id
        ]
        
        # Sort by timestamp (most recent first)
        session_conversations.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return session_conversations[:limit]
    
    def get_conversation_stats(self) -> Dict[str, Any]:
        """Get statistics about conversations"""
        if not self.conversations:
            return {}
        
        total_conversations = len(self.conversations)
        unique_sessions = len(set(conv.get('session_id', '') for conv in self.conversations))
        unique_users = len(set(conv.get('user_id', '') for conv in self.conversations))
        
        avg_query_length = sum(conv.get('query_length', 0) for conv in self.conversations) / total_conversations
        avg_response_length = sum(conv.get('response_length', 0) for conv in self.conversations) / total_conversations
        avg_response_time = sum(conv.get('response_time_ms', 0) for conv in self.conversations) / total_conversations
        
        # Most recent conversation
        recent_conversations = sorted(self.conversations, key=lambda x: x.get('timestamp', ''), reverse=True)
        last_conversation_time = recent_conversations[0].get('timestamp', '') if recent_conversations else ''
        
        return {
            'total_conversations': total_conversations,
            'unique_sessions': unique_sessions,
            'unique_users': unique_users,
            'avg_query_length': round(avg_query_length, 1),
            'avg_response_length': round(avg_response_length, 1),
            'avg_response_time_ms': round(avg_response_time, 1),
            'last_conversation_time': last_conversation_time
        }
    
    def export_for_databricks(self) -> Dict[str, List[Dict[str, Any]]]:
        """Export conversations in format suitable for Databricks tables with DG prefix"""
        
        # DG_CONVERSATIONS table data
        dg_conversations = []
        dg_conversation_sources = []
        dg_conversation_metrics = []
        
        for conv in self.conversations:
            # Main conversation record
            dg_conversations.append({
                'conversation_id': conv.get('conversation_id'),
                'session_id': conv.get('session_id'),
                'user_id': conv.get('user_id'),
                'timestamp': conv.get('timestamp'),
                'user_query': conv.get('user_query'),
                'bot_response': conv.get('bot_response'),
                'query_length': conv.get('query_length'),
                'response_length': conv.get('response_length'),
                'num_sources': conv.get('num_sources'),
                'response_time_ms': conv.get('response_time_ms'),
                'metadata': json.dumps(conv.get('metadata', {})),
                'created_at': datetime.now().isoformat()
            })
            
            # Sources for each conversation
            for i, source in enumerate(conv.get('sources', [])):
                dg_conversation_sources.append({
                    'conversation_id': conv.get('conversation_id'),
                    'source_rank': i + 1,
                    'file_name': source.get('file_name', ''),
                    'file_path': source.get('file_path', ''),
                    'similarity_score': source.get('similarity', 0),
                    'created_at': datetime.now().isoformat()
                })
            
            # Metrics record
            dg_conversation_metrics.append({
                'conversation_id': conv.get('conversation_id'),
                'session_id': conv.get('session_id'),
                'user_id': conv.get('user_id'),
                'date': conv.get('timestamp', '').split('T')[0],  # Extract date part
                'query_length': conv.get('query_length'),
                'response_length': conv.get('response_length'),
                'response_time_ms': conv.get('response_time_ms'),
                'num_sources_used': conv.get('num_sources'),
                'created_at': datetime.now().isoformat()
            })
        
        return {
            'DG_CONVERSATIONS': dg_conversations,
            'DG_CONVERSATION_SOURCES': dg_conversation_sources,  
            'DG_CONVERSATION_METRICS': dg_conversation_metrics
        }
    
    def generate_databricks_sql(self) -> str:
        """Generate SQL statements to create Databricks tables with DG prefix"""
        
        sql_statements = """
-- Create Databricks tables for conversation logging with DG prefix

-- Main conversations table
CREATE TABLE IF NOT EXISTS DG_CONVERSATIONS (
    conversation_id STRING,
    session_id STRING,
    user_id STRING,
    timestamp TIMESTAMP,
    user_query STRING,
    bot_response STRING,
    query_length INT,
    response_length INT,
    num_sources INT,
    response_time_ms DOUBLE,
    metadata STRING,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
) USING DELTA
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true');

-- Conversation sources table
CREATE TABLE IF NOT EXISTS DG_CONVERSATION_SOURCES (
    conversation_id STRING,
    source_rank INT,
    file_name STRING,
    file_path STRING,
    similarity_score DOUBLE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
) USING DELTA
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true');

-- Conversation metrics table for reporting
CREATE TABLE IF NOT EXISTS DG_CONVERSATION_METRICS (
    conversation_id STRING,
    session_id STRING,
    user_id STRING,
    date DATE,
    query_length INT,
    response_length INT,
    response_time_ms DOUBLE,
    num_sources_used INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
) USING DELTA
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true');

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_dg_conv_session ON DG_CONVERSATIONS (session_id);
CREATE INDEX IF NOT EXISTS idx_dg_conv_timestamp ON DG_CONVERSATIONS (timestamp);
CREATE INDEX IF NOT EXISTS idx_dg_metrics_date ON DG_CONVERSATION_METRICS (date);
"""
        
        return sql_statements
    
    def export_to_csv_for_databricks(self, output_dir: str = "databricks_export"):
        """Export conversation data to CSV files for Databricks import"""
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        export_data = self.export_for_databricks()
        
        import csv
        
        for table_name, records in export_data.items():
            if not records:
                continue
                
            csv_file = output_path / f"{table_name}.csv"
            
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                if records:
                    writer = csv.DictWriter(f, fieldnames=records[0].keys())
                    writer.writeheader()
                    writer.writerows(records)
            
            logger.info(f"Exported {len(records)} records to {csv_file}")
        
        # Also create the SQL file
        sql_file = output_path / "create_tables.sql"
        with open(sql_file, 'w', encoding='utf-8') as f:
            f.write(self.generate_databricks_sql())
        
        logger.info(f"Exported SQL schema to {sql_file}")
        
        return output_path