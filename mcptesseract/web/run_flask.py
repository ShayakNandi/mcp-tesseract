#!/usr/bin/env python3
"""
Script to run the Flask-SocketIO Tesseract OCR server
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import the flask_app
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

def main():
    print("🔥 Starting Flask-SocketIO Tesseract OCR Server...")
    print("📋 Available at: http://localhost:5000")
    print("🔄 SocketIO endpoint: /socket.io/")
    print("⚡ Real-time communication enabled")
    print()
    print("🆚 Compare with FastAPI version at: http://localhost:8001")
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        # Import and run the Flask app
        from web.flask_app import app, socketio, mcp_client
        
        # Start the MCP client first
        print("🔗 Initializing MCP client...")
        mcp_client.start_async_loop()
        success = mcp_client.connect()
        
        if success:
            print("✅ MCP client connected successfully")
        else:
            print("⚠️  MCP client connection failed - will retry on first request")
        
        print("🚀 Starting Flask server...")
        
        # Run the Flask-SocketIO app
        socketio.run(
            app, 
            host='0.0.0.0', 
            port=5000, 
            debug=True,
            use_reloader=False  # Disable reloader to avoid issues with threads
        )
        
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting Flask server: {e}")
        sys.exit(1)
    finally:
        # Clean up MCP client
        try:
            mcp_client.disconnect()
            print("🧹 MCP client disconnected")
        except:
            pass

if __name__ == "__main__":
    main() 