#!/usr/bin/env python3
"""
Simple test script to verify document processing works
"""

import os
from pathlib import Path
from document_processor import DocumentProcessor

def test_document_processing():
    print("Testing document processor...")
    
    # Create test directory structure
    test_dir = Path("test_docs")
    test_dir.mkdir(exist_ok=True)
    
    # Create a test text file
    test_txt = test_dir / "test.txt"
    test_txt.write_text("This is a test document for the knowledge base chatbot.")
    
    # Test the processor
    processor = DocumentProcessor()
    documents = processor.process_directory(str(test_dir))
    
    if documents:
        print(f"Successfully processed {len(documents)} documents")
        for doc in documents:
            print(f"   - {doc['file_name']}: {len(doc['content'])} characters")
    else:
        print("No documents processed")
    
    # Cleanup
    test_txt.unlink()
    test_dir.rmdir()

if __name__ == "__main__":
    test_document_processing()