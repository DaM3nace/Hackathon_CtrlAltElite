#!/usr/bin/env python3
"""
Restart the web chat interface - kills existing processes and starts fresh
"""

import subprocess
import time
import sys
import os

def restart_webchat():
    print("🔄 Restarting Knowledge Base Web Chat...")
    print("=" * 50)
    
    # Try to kill existing processes (Windows compatible)
    try:
        # Windows taskkill approach
        result = subprocess.run(['tasklist'], capture_output=True, text=True)
        if 'python' in result.stdout:
            print("🛑 Stopping existing Python processes...")
            subprocess.run(['taskkill', '/F', '/IM', 'python.exe'], 
                         capture_output=True)
            time.sleep(2)
    except:
        print("ℹ️  No existing processes to stop")
    
    print("🚀 Starting fresh web chat instance...")
    
    # Start the web chat
    try:
        # Import and start directly
        from web_chat import app
        import uvicorn
        
        print("📱 Web chat starting at: http://127.0.0.1:8000")
        print("🔧 Features enabled:")
        print("   • Conversation logging with session tracking")
        print("   • Databricks export functionality") 
        print("   • Real-time performance metrics")
        print("   • Source document attribution")
        print("\n💡 New Features:")
        print("   • Export to Databricks button in sidebar")
        print("   • Enhanced conversation statistics")
        print("   • Session-based chat history")
        
        print("\n🌐 Opening browser automatically...")
        
        # Try to open browser
        try:
            import webbrowser
            webbrowser.open('http://127.0.0.1:8000')
        except:
            pass
        
        print("\n🛑 Press Ctrl+C to stop the server")
        print("=" * 50)
        
        # Start the server
        uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
        
    except KeyboardInterrupt:
        print("\n\n👋 Web chat stopped successfully!")
    except Exception as e:
        print(f"\n❌ Error starting web chat: {str(e)}")
        print("\n🔧 Troubleshooting:")
        print("   1. Check if port 8000 is available")
        print("   2. Try: python web_chat.py")
        print("   3. Try: python main.py web")

if __name__ == "__main__":
    restart_webchat()