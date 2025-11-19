"""
Migrate local vectors and documents to Databricks storage
"""
import os
import json
import logging
from typing import List, Dict, Any
from dotenv import load_dotenv
from databricks_storage import DatabricksStorage
from document_processor import DocumentProcessor

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_local_vectors() -> List[Dict[str, Any]]:
    """Load vectors from local_vectors.json"""
    try:
        with open('local_vectors.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('vectors', [])
    except Exception as e:
        logger.error(f"Error loading local vectors: {str(e)}")
        return []

def load_local_documents() -> List[Dict[str, Any]]:
    """Load documents from ./SOP directory"""
    try:
        docs_dir = os.getenv('DOCUMENTS_DIRECTORY', './SOP')
        doc_processor = DocumentProcessor()
        documents = doc_processor.process_directory(docs_dir)
        return documents
    except Exception as e:
        logger.error(f"Error loading documents: {str(e)}")
        return []

def group_chunks_by_document(chunks: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Group chunks by their source document"""
    grouped = {}

    for chunk in chunks:
        file_name = chunk['metadata']['file_name']
        if file_name not in grouped:
            grouped[file_name] = []
        grouped[file_name].append(chunk)

    return grouped

def migrate_to_databricks():
    """Main migration function"""
    print()
    print("=" * 80)
    print("MIGRATE LOCAL DATA TO DATABRICKS STORAGE")
    print("=" * 80)
    print()

    # Initialize storage
    storage = DatabricksStorage()

    # Step 1: Load local data
    print("Step 1: Loading local data...")
    chunks = load_local_vectors()
    documents = load_local_documents()

    if not chunks and not documents:
        print("[ERROR] No local data found to migrate")
        return False

    print(f"[SUCCESS] Loaded {len(chunks)} chunks")
    print(f"[SUCCESS] Loaded {len(documents)} documents")
    print()

    # Step 2: Check Databricks connection
    print("Step 2: Checking Databricks connection...")
    doc_count = storage.get_document_count()
    chunk_count = storage.get_chunk_count()

    print(f"[INFO] Current Databricks storage:")
    print(f"  Documents: {doc_count}")
    print(f"  Chunks: {chunk_count}")
    print()

    # Step 3: Ask for confirmation
    if doc_count > 0 or chunk_count > 0:
        response = input("Databricks storage is not empty. Clear existing data? (yes/no): ")
        if response.lower() in ['yes', 'y']:
            print("[INFO] Clearing existing data...")
            if storage.clear_all_data():
                print("[SUCCESS] Data cleared")
            else:
                print("[ERROR] Failed to clear data")
                return False
        else:
            print("[INFO] Keeping existing data, will append new data")

    print()

    # Step 4: Migrate documents
    print("Step 3: Migrating documents to Databricks...")

    document_mapping = {}  # file_name -> document_id

    for i, doc in enumerate(documents, 1):
        print(f"  [{i}/{len(documents)}] Migrating {doc['file_name']}...", end=' ')

        document_id = storage.generate_document_id(doc['file_name'], doc['content'])
        document_mapping[doc['file_name']] = document_id

        if storage.save_document(doc):
            print("[OK]")
        else:
            print("[FAILED]")

    print()

    # Step 5: Migrate chunks
    print("Step 4: Migrating chunks to Databricks...")

    # Group chunks by document
    grouped_chunks = group_chunks_by_document(chunks)

    for file_name, file_chunks in grouped_chunks.items():
        document_id = document_mapping.get(file_name)

        if not document_id:
            logger.warning(f"No document ID for {file_name}, skipping chunks")
            continue

        print(f"  Migrating {len(file_chunks)} chunks for {file_name}...", end=' ')

        if storage.save_chunks(file_chunks, document_id):
            print("[OK]")
        else:
            print("[FAILED]")

    print()

    # Step 6: Verify migration
    print("Step 5: Verifying migration...")

    final_doc_count = storage.get_document_count()
    final_chunk_count = storage.get_chunk_count()

    print(f"[INFO] Final Databricks storage:")
    print(f"  Documents: {final_doc_count}")
    print(f"  Chunks: {final_chunk_count}")
    print()

    if final_doc_count >= len(documents) and final_chunk_count >= len(chunks):
        print("[SUCCESS] Migration completed successfully!")
        print()
        print("=" * 80)
        print("MIGRATION SUMMARY")
        print("=" * 80)
        print(f"Documents migrated: {len(documents)}")
        print(f"Chunks migrated: {len(chunks)}")
        print(f"Total documents in Databricks: {final_doc_count}")
        print(f"Total chunks in Databricks: {final_chunk_count}")
        print()
        print("Next steps:")
        print("  1. Enable Databricks storage in .env:")
        print("     USE_DATABRICKS_STORAGE=true")
        print("  2. Restart the chatbot:")
        print("     python web_chat.py")
        print()
        return True
    else:
        print("[ERROR] Migration incomplete!")
        print(f"Expected at least {len(documents)} documents, got {final_doc_count}")
        print(f"Expected at least {len(chunks)} chunks, got {final_chunk_count}")
        return False

if __name__ == "__main__":
    import sys

    print()
    print("=" * 80)
    print("DATABRICKS STORAGE MIGRATION TOOL")
    print("=" * 80)
    print()
    print("This tool will migrate your local documents and chunks to Databricks.")
    print()
    print("Prerequisites:")
    print("  [OK] Databricks tables created (run setup_databricks_storage.sql)")
    print("  [OK] DATABRICKS_TOKEN and credentials configured in .env")
    print("  [OK] local_vectors.json exists with current chunks")
    print("  [OK] Documents in ./SOP directory")
    print()

    response = input("Continue with migration? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Migration cancelled.")
        sys.exit(0)

    success = migrate_to_databricks()

    if success:
        print("=" * 80)
        print("MIGRATION COMPLETE!")
        print("=" * 80)
        sys.exit(0)
    else:
        print("=" * 80)
        print("MIGRATION FAILED!")
        print("=" * 80)
        sys.exit(1)
