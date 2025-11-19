#!/usr/bin/env python3
"""
Start the web chat interface and show instructions
"""

import subprocess
import webbrowser
import time
import threading
from web_chat import app
import uvicorn

def start_server():
    """Start the web server"""
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")

def main():
    print("=" * 60)
    print("🚀 Starting Knowledge Base Web Chat")
    print("=" * 60)
    
    print("\n1. Starting web server...")
    
    # Start server in background thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # Give server time to start
    time.sleep(3)
    
    print("2. Web chat is now running at: http://127.0.0.1:8000")
    print("\n🌐 Open your browser and navigate to: http://127.0.0.1:8000")
    
    print("\n💡 Features:")
    print("   • Ask questions about your documents")
    print("   • View knowledge base statistics")  
    print("   • See source documents for each answer")
    print("   • Clean, responsive interface")
    
    print("\n📝 Try asking:")
    print('   • "What are the password requirements?"')
    print('   • "How do I install an ONT?"')
    print('   • "What is the incident response procedure?"')
    
    print(f"\n📊 Current knowledge base: {22} chunks from 7 documents")
    
    print("\n🛑 Press Ctrl+C to stop the server")
    
    try:
        # Try to open browser automatically
        webbrowser.open('http://127.0.0.1:8000')
        print("✅ Opened browser automatically")
    except:
        pass
    
    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n👋 Web chat stopped. Goodbye!")

if __name__ == "__main__":
    main()