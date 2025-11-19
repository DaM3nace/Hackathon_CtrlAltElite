"""
Re-chunk knowledge base with different settings
"""
import os
import json
from dotenv import load_dotenv
from document_processor import DocumentProcessor
from text_processor import TextProcessor

load_dotenv()

def backup_current_vectors():
    """Backup current vectors"""
    if os.path.exists('local_vectors.json'):
        backup_file = 'local_vectors.backup.json'
        import shutil
        shutil.copy('local_vectors.json', backup_file)
        print(f"[SUCCESS] Backed up current vectors to {backup_file}")
        return True
    else:
        print("[INFO] No existing vectors to backup")
        return False

def rechunk_documents(chunk_size: int = 512, chunk_overlap: int = 50):
    """Re-chunk all documents with new settings"""
    print()
    print("=" * 80)
    print("RE-CHUNKING KNOWLEDGE BASE")
    print("=" * 80)
    print()
    print(f"Settings:")
    print(f"  Chunk Size: {chunk_size} tokens")
    print(f"  Chunk Overlap: {chunk_overlap} tokens")
    print()

    # Get documents directory
    docs_dir = os.getenv('DOCUMENTS_DIRECTORY', './SOP')
    if not os.path.exists(docs_dir):
        print(f"[ERROR] Documents directory not found: {docs_dir}")
        return False

    # Process documents
    print("Step 1: Loading documents...")
    doc_processor = DocumentProcessor()
    documents = doc_processor.process_directory(docs_dir)
    print(f"[SUCCESS] Loaded {len(documents)} documents")
    print()

    # Chunk documents
    print("Step 2: Chunking documents...")
    text_processor = TextProcessor(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = text_processor.process_documents(documents)
    print(f"[SUCCESS] Created {len(chunks)} chunks")
    print()

    # Show statistics
    print("Step 3: Chunk Statistics:")
    chunk_sizes = [len(c['content']) for c in chunks]
    token_counts = [c.get('token_count', 0) for c in chunks]

    print(f"  Total Chunks: {len(chunks)}")
    print(f"  Avg Size: {sum(chunk_sizes) // len(chunk_sizes)} characters")
    print(f"  Min Size: {min(chunk_sizes)} characters")
    print(f"  Max Size: {max(chunk_sizes)} characters")
    print(f"  Avg Tokens: {sum(token_counts) // len(token_counts)}")
    print()

    # Group by file
    files = {}
    for chunk in chunks:
        fname = chunk['metadata']['file_name']
        if fname not in files:
            files[fname] = 0
        files[fname] += 1

    print("  Chunks per file:")
    for fname, count in sorted(files.items()):
        print(f"    {fname}: {count} chunks")
    print()

    # Save to local vectors
    print("Step 4: Saving chunks...")
    vector_data = {
        'vectors': chunks,
        'metadata': {
            'total_chunks': len(chunks),
            'chunk_size': chunk_size,
            'chunk_overlap': chunk_overlap,
            'embedding_model': 'all-MiniLM-L6-v2'
        }
    }

    with open('local_vectors.json', 'w', encoding='utf-8') as f:
        json.dump(vector_data, f, indent=2)
    print(f"[SUCCESS] Saved {len(chunks)} chunks to local_vectors.json")
    print()

    print("=" * 80)
    print("RE-CHUNKING COMPLETE!")
    print("=" * 80)
    print()
    print("Next steps:")
    print("  1. Test the chatbot: python web_chat.py")
    print("  2. Run analysis: python analyze_chunks.py")
    print("  3. If not satisfied, restore backup: copy local_vectors.backup.json local_vectors.json")
    print()

    return True

if __name__ == "__main__":
    import sys

    print()
    print("=" * 80)
    print("KNOWLEDGE BASE RE-CHUNKING TOOL")
    print("=" * 80)
    print()

    # Parse arguments
    chunk_size = int(sys.argv[1]) if len(sys.argv) > 1 else int(os.getenv('CHUNK_SIZE', 512))
    chunk_overlap = int(sys.argv[2]) if len(sys.argv) > 2 else int(os.getenv('CHUNK_OVERLAP', 50))

    print(f"Current settings from .env:")
    print(f"  CHUNK_SIZE={os.getenv('CHUNK_SIZE', '512')}")
    print(f"  CHUNK_OVERLAP={os.getenv('CHUNK_OVERLAP', '50')}")
    print()

    if len(sys.argv) > 1:
        print(f"Command-line override:")
        print(f"  CHUNK_SIZE={chunk_size}")
        print(f"  CHUNK_OVERLAP={chunk_overlap}")
        print()

    # Confirm
    response = input("Continue with re-chunking? This will replace your current chunks. (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Aborted.")
        exit(0)

    # Backup
    print()
    print("Creating backup...")
    backup_current_vectors()

    # Re-chunk
    print()
    success = rechunk_documents(chunk_size, chunk_overlap)

    if success:
        print("[SUCCESS] Knowledge base re-chunked successfully!")
        print()
        print("Note: You need to restart the web server for changes to take effect:")
        print("  1. Stop current server (Ctrl+C)")
        print("  2. Restart: python web_chat.py")
    else:
        print("[ERROR] Re-chunking failed!")
        print("Your original chunks are preserved in local_vectors.backup.json")
