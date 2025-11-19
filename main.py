#!/usr/bin/env python3
"""
Knowledge Base Chatbot with RAG and Databricks Integration

This script provides a command-line interface to set up and run the knowledge base chatbot.
"""

import argparse
import os
import sys
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_environment():
    """Check if .env file exists and guide user to set it up."""
    env_file = Path('.env')
    env_example = Path('.env.example')
    
    if not env_file.exists():
        if env_example.exists():
            print("❌ .env file not found!")
            print(f"📋 Please copy {env_example} to .env and fill in your credentials:")
            print("   cp .env.example .env")
            print("\nRequired environment variables:")
            print("   - DATABRICKS_SERVER_HOSTNAME")
            print("   - DATABRICKS_HTTP_PATH")
            print("   - DATABRICKS_TOKEN")
            print("   - OPENAI_API_KEY (optional, for better responses)")
            return False
        else:
            print("❌ Neither .env nor .env.example found!")
            return False
    
    return True

def install_dependencies():
    """Install required Python packages."""
    print("📦 Installing dependencies...")
    os.system("pip install -r requirements.txt")
    print("✅ Dependencies installed!")

def update_knowledge_base(documents_dir: str):
    """Update the knowledge base with documents from a directory."""
    if not Path(documents_dir).exists():
        print(f"Directory not found: {documents_dir}")
        return False
    
    try:
        from simple_rag_system import SimpleRAGSystem
        
        print(f"Processing documents from: {documents_dir}")
        rag_system = SimpleRAGSystem()
        rag_system.update_knowledge_base(documents_dir)
        
        print("Knowledge base updated successfully!")
        return True
    except Exception as e:
        print(f"Error updating knowledge base: {str(e)}")
        return False

def run_web():
    """Run the web chat interface."""
    print("Starting web chat interface...")
    print("Open your browser to: http://127.0.0.1:8000")
    os.system("python web_chat.py")

def run_fastapi():
    """Run the FastAPI server."""
    if not setup_environment():
        return
    
    print("🚀 Starting FastAPI server...")
    os.system("python api_server.py")

def interactive_query():
    """Run an interactive command-line query interface."""
    try:
        from simple_rag_system import SimpleRAGSystem
        
        print("Knowledge Base Chatbot - Interactive Mode")
        print("Type 'quit' to exit, 'stats' to see knowledge base statistics")
        print("-" * 50)
        
        rag_system = SimpleRAGSystem()
        
        while True:
            query = input("\nYour question: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            elif query.lower() == 'stats':
                stats = rag_system.get_knowledge_base_stats()
                if stats:
                    print("\nKnowledge Base Statistics:")
                    for key, value in stats.items():
                        print(f"   {key}: {value}")
                else:
                    print("No statistics available (knowledge base might be empty)")
                continue
            elif not query:
                print("Please enter a question")
                continue
            
            try:
                result = rag_system.ask_question(query)
                
                print(f"\nAnswer: {result['response']}")
                
                if result['sources']:
                    print(f"\nSources ({result['num_sources']} found):")
                    for i, source in enumerate(result['sources'], 1):
                        print(f"   {i}. {source['file_name']} (similarity: {source['similarity']})")
                else:
                    print("\nNo sources found")
                    
            except Exception as e:
                print(f"Error processing query: {str(e)}")
    
    except KeyboardInterrupt:
        print("\nGoodbye!")
    except Exception as e:
        print(f"Error starting interactive mode: {str(e)}")

def export_databricks():
    """Export conversation data for Databricks import"""
    try:
        from databricks_sync import create_databricks_sync_command
        create_databricks_sync_command()
    except Exception as e:
        print(f"Error exporting to Databricks: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description="Knowledge Base Chatbot with RAG and Databricks")
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Setup command
    setup_parser = subparsers.add_parser('setup', help='Set up the environment and install dependencies')
    
    # Update knowledge base command
    update_parser = subparsers.add_parser('update', help='Update knowledge base with documents')
    update_parser.add_argument('directory', nargs='?', default='./SOP', help='Directory containing documents to process (default: ./SOP)')
    
    # Run web interface command
    web_parser = subparsers.add_parser('web', help='Run web chat interface')
    
    # Run API server command
    api_parser = subparsers.add_parser('api', help='Run FastAPI server')
    
    # Interactive query command
    chat_parser = subparsers.add_parser('chat', help='Run interactive command-line chat')
    
    # Export to Databricks command
    export_parser = subparsers.add_parser('export-databricks', help='Export conversation data for Databricks')
    
    args = parser.parse_args()
    
    if args.command == 'setup':
        install_dependencies()
        if setup_environment():
            print("✅ Setup completed! You can now run the chatbot.")
        else:
            print("❌ Setup incomplete. Please configure your .env file.")
    
    elif args.command == 'update':
        if setup_environment():
            update_knowledge_base(args.directory)
    
    elif args.command == 'web':
        run_web()
    
    elif args.command == 'api':
        run_fastapi()
    
    elif args.command == 'chat':
        interactive_query()
    
    elif args.command == 'export-databricks':
        export_databricks()
    
    else:
        parser.print_help()
        print("\nQuick start:")
        print("1. python main.py setup")
        print("2. Add documents to SOP/ directory")
        print("3. python main.py update")
        print("4. python main.py web  # or 'chat' for command line")
        print("5. python main.py export-databricks  # export conversations")

if __name__ == "__main__":
    main()