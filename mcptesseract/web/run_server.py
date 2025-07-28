#!/usr/bin/env python3
"""
Simple script to run the Tesseract FastAPI web server
"""

import uvicorn
import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import the fastapi_app
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

def main():
    print("🚀 Starting Tesseract OCR FastAPI Web Server...")
    print("📋 Available at: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("🔄 WebSocket endpoint: ws://localhost:8000/ws/{client_id}")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        # Run the FastAPI app with uvicorn
        uvicorn.run(
            "web.fastapi_app:app",
            host="0.0.0.0",
            port=8000,
            reload=True,  # Enable auto-reload for development
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 