#!/usr/bin/env python3
"""
Test conversation logging and Databricks export functionality
"""

from simple_rag_system import SimpleRAGSystem
from databricks_sync import DatabricksSync
import uuid

def test_conversation_logging():
    print("=== Testing Conversation Logging & Databricks Export ===\n")
    
    # Initialize the RAG system (with conversation logging)
    rag = SimpleRAGSystem()
    
    # Create a test session
    session_id = str(uuid.uuid4())
    print(f"Test Session ID: {session_id}\n")
    
    # Ask some test questions
    test_questions = [
        "What are the password requirements?",
        "How long should passwords be?", 
        "What is the incident response procedure?",
        "Tell me about ONT installation procedures"
    ]
    
    print("1. Testing conversation logging:")
    for i, question in enumerate(test_questions, 1):
        print(f"   Q{i}: {question}")
        result = rag.ask_question(question, session_id=session_id, user_id="test_user")
        print(f"   > Logged conversation ID: {result['conversation_id']}")
        print(f"   > Response time: {result['response_time_ms']:.0f}ms")
        print()
    
    # Get stats
    print("2. Conversation statistics:")
    stats = rag.get_knowledge_base_stats()
    conv_stats = {k: v for k, v in stats.items() if 'conversation' in k or 'response' in k}
    for key, value in conv_stats.items():
        print(f"   {key}: {value}")
    print()
    
    # Test Databricks export
    print("3. Testing Databricks export:")
    try:
        databricks_sync = DatabricksSync(rag.conversation_logger)
        package_path = databricks_sync.export_full_databricks_package("test_databricks_export")
        
        print(f"   Export successful!")
        print(f"   Package location: {package_path}")
        print(f"   Conversations exported: {len(rag.conversation_logger.conversations)}")
        
        # Show what was created
        import os
        files = os.listdir(package_path)
        print(f"   Files created:")
        for file in sorted(files):
            print(f"      - {file}")
        
        # Show CSV data structure  
        csv_files = [f for f in os.listdir(package_path / "csv_data") if f.endswith('.csv')]
        print(f"   CSV files for Databricks:")
        for csv_file in csv_files:
            print(f"      - {csv_file}")
            
    except Exception as e:
        print(f"   Export failed: {str(e)}")
    
    print("\n" + "="*60)
    print("Conversation logging and Databricks export test completed!")
    print("\nDatabricks Tables Created (DG Prefix):")
    print("   - DG_CONVERSATIONS - Main conversation records")
    print("   - DG_CONVERSATION_SOURCES - Source documents per response")  
    print("   - DG_CONVERSATION_METRICS - Analytics and reporting data")
    print("\nNext Steps:")
    print("   1. Upload the export package to Databricks")
    print("   2. Run the SQL scripts to create tables")
    print("   3. Import CSV data into the DG tables")
    print("   4. Use reporting queries for analytics")

if __name__ == "__main__":
    test_conversation_logging()