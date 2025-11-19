"""
Analyze and visualize knowledge base chunking
"""
import json
import os
from dotenv import load_dotenv
from typing import Dict, List

load_dotenv()

def load_chunks():
    """Load chunks from local_vectors.json"""
    try:
        with open('local_vectors.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data['vectors']
    except Exception as e:
        print(f"Error loading chunks: {e}")
        return []

def analyze_chunks(chunks: List[Dict]) -> Dict:
    """Analyze chunk statistics"""
    if not chunks:
        return {}

    # Group by file
    files = {}
    for chunk in chunks:
        fname = chunk['metadata']['file_name']
        if fname not in files:
            files[fname] = []
        files[fname].append(chunk)

    # Calculate statistics
    chunk_sizes = [len(c['content']) for c in chunks]
    token_counts = [c.get('token_count', 0) for c in chunks]

    return {
        'total_chunks': len(chunks),
        'total_files': len(files),
        'files': files,
        'chunk_sizes': chunk_sizes,
        'token_counts': token_counts,
        'avg_chunk_size': sum(chunk_sizes) // len(chunk_sizes) if chunk_sizes else 0,
        'min_chunk_size': min(chunk_sizes) if chunk_sizes else 0,
        'max_chunk_size': max(chunk_sizes) if chunk_sizes else 0,
        'avg_tokens': sum(token_counts) // len(token_counts) if token_counts else 0,
        'total_content': sum(chunk_sizes)
    }

def print_analysis(analysis: Dict):
    """Print detailed analysis"""
    print()
    print("=" * 80)
    print("KNOWLEDGE BASE CHUNKING ANALYSIS")
    print("=" * 80)
    print()

    print("CURRENT CONFIGURATION:")
    print(f"  Chunk Size: {os.getenv('CHUNK_SIZE', '512')} tokens")
    print(f"  Chunk Overlap: {os.getenv('CHUNK_OVERLAP', '50')} tokens")
    print(f"  Documents Directory: {os.getenv('DOCUMENTS_DIRECTORY', './SOP')}")
    print()

    print("OVERALL STATISTICS:")
    print(f"  Total Chunks: {analysis['total_chunks']}")
    print(f"  Total Files: {analysis['total_files']}")
    print(f"  Total Content: {analysis['total_content']:,} characters")
    print()

    print("CHUNK SIZE STATISTICS:")
    print(f"  Average: {analysis['avg_chunk_size']:,} characters ({analysis['avg_tokens']} tokens)")
    print(f"  Minimum: {analysis['min_chunk_size']:,} characters")
    print(f"  Maximum: {analysis['max_chunk_size']:,} characters")
    print()

    print("CHUNKS PER FILE:")
    for fname, chunks in sorted(analysis['files'].items()):
        total_chars = sum(len(c['content']) for c in chunks)
        print(f"  {fname}")
        print(f"    Chunks: {len(chunks)}")
        print(f"    Total Size: {total_chars:,} characters")
        print(f"    Avg Chunk: {total_chars // len(chunks):,} characters")
    print()

    print("CHUNK SIZE DISTRIBUTION:")
    ranges = [
        (0, 500, "Very Small"),
        (500, 1000, "Small"),
        (1000, 2000, "Medium"),
        (2000, 3000, "Large"),
        (3000, 10000, "Very Large")
    ]

    for min_size, max_size, label in ranges:
        count = sum(1 for size in analysis['chunk_sizes'] if min_size <= size < max_size)
        if count > 0:
            pct = (count / analysis['total_chunks']) * 100
            bar = "#" * int(pct / 2)
            print(f"  {label:12} ({min_size:4}-{max_size:4} chars): {count:3} chunks ({pct:5.1f}%) {bar}")
    print()

def print_recommendations(analysis: Dict):
    """Print recommendations for chunk optimization"""
    print("RECOMMENDATIONS:")
    print("=" * 80)
    print()

    avg_size = analysis['avg_chunk_size']
    max_size = analysis['max_chunk_size']
    min_size = analysis['min_chunk_size']

    # Check if chunking is well-balanced
    if max_size > avg_size * 2:
        print("[WARNING] Some chunks are more than 2x the average size")
        print(f"  Max: {max_size} chars vs Avg: {avg_size} chars")
        print("  Consider reducing CHUNK_SIZE to create more uniform chunks")
        print()

    if min_size < 200:
        print("[INFO] Some very small chunks detected")
        print(f"  Min: {min_size} chars")
        print("  Small chunks may not provide enough context for good retrieval")
        print()

    if analysis['total_chunks'] < 10:
        print("[INFO] Low number of chunks detected")
        print(f"  Total: {analysis['total_chunks']} chunks")
        print("  Consider reducing CHUNK_SIZE to create more chunks for better granularity")
        print()

    # Optimal chunk size recommendations
    print("OPTIMAL CHUNK SIZE GUIDE:")
    print("  - 256 tokens (~1024 chars): Fine-grained, specific retrieval")
    print("  - 512 tokens (~2048 chars): Balanced (CURRENT SETTING)")
    print("  - 1024 tokens (~4096 chars): Broader context, fewer chunks")
    print()

    print("TO CHANGE CHUNK SIZE:")
    print("  1. Edit .env file:")
    print("     CHUNK_SIZE=256        # for smaller chunks")
    print("     CHUNK_SIZE=1024       # for larger chunks")
    print("     CHUNK_OVERLAP=50      # overlap between chunks")
    print()
    print("  2. Rebuild knowledge base:")
    print("     python main.py update")
    print()

def show_sample_chunks(chunks: List[Dict], num_samples: int = 3):
    """Show sample chunks"""
    print("SAMPLE CHUNKS:")
    print("=" * 80)
    print()

    for i, chunk in enumerate(chunks[:num_samples], 1):
        print(f"Chunk {i}:")
        print(f"  File: {chunk['metadata']['file_name']}")
        print(f"  Size: {len(chunk['content'])} characters")
        print(f"  Tokens: {chunk.get('token_count', 'N/A')}")
        print(f"  Chunk ID: {chunk.get('chunk_id', 'N/A')}")
        print(f"  Content Preview:")
        preview = chunk['content'][:300].replace('\n', '\n    ')
        print(f"    {preview}...")
        print()

if __name__ == "__main__":
    print("Loading chunks from local_vectors.json...")
    chunks = load_chunks()

    if not chunks:
        print("No chunks found! Have you built the knowledge base?")
        print("Run: python main.py update")
        exit(1)

    analysis = analyze_chunks(chunks)
    print_analysis(analysis)
    print_recommendations(analysis)
    show_sample_chunks(chunks)

    print("=" * 80)
    print("Analysis complete!")
    print("=" * 80)
