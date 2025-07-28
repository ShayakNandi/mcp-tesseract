#!/usr/bin/env python3
"""
Test script to demonstrate both FastAPI and Flask implementations
This script will sync dependencies and provide instructions for testing both servers.
"""

import os
import sys
import subprocess
import requests
import time
from pathlib import Path

def sync_dependencies():
    """Sync the dependencies to include Flask packages"""
    print("📦 Syncing dependencies...")
    try:
        result = subprocess.run(['uv', 'sync'], capture_output=True, text=True, cwd='.')
        if result.returncode == 0:
            print("✅ Dependencies synced successfully")
            return True
        else:
            print(f"❌ Error syncing dependencies: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error running uv sync: {e}")
        return False

def test_server_health(url, server_name):
    """Test if a server is running and healthy"""
    try:
        response = requests.get(f"{url}/api/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ {server_name} is healthy:")
            print(f"   - Status: {data.get('status', 'unknown')}")
            print(f"   - MCP Connected: {data.get('mcp_connected', False)}")
            print(f"   - Tools Available: {data.get('tools_available', 0)}")
            return True
        else:
            print(f"⚠️ {server_name} responded with status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ {server_name} is not accessible: {e}")
        return False

def main():
    print("🧪 Flask & FastAPI Integration Test Suite")
    print("=" * 50)
    
    # Sync dependencies first
    if not sync_dependencies():
        print("⚠️ Warning: Dependency sync failed, but continuing with tests...")
    
    print("\n🚀 Server Status Check:")
    print("-" * 30)
    
    # Check FastAPI server
    fastapi_healthy = test_server_health("http://localhost:8001", "FastAPI Server")
    
    # Check Flask server  
    flask_healthy = test_server_health("http://localhost:5000", "Flask Server")
    
    print("\n📋 Instructions:")
    print("-" * 30)
    
    if not fastapi_healthy:
        print("🔧 To start FastAPI server:")
        print("   python web/fastapi_app.py")
        print("   Then visit: http://localhost:8001")
    
    if not flask_healthy:
        print("🔧 To start Flask server:")
        print("   python web/run_flask.py")
        print("   Then visit: http://localhost:5000")
    
    print("\n🎯 Testing Features:")
    print("-" * 30)
    print("1. 📄 Upload an image file for OCR processing")
    print("2. 📊 Test word frequency analysis")
    print("3. 📚 Process bibliography data")
    print("4. 🔄 Test real-time communication (WebSocket vs SocketIO)")
    
    print("\n🆚 Comparison:")
    print("-" * 30)
    print("FastAPI (8001)     | Flask-SocketIO (5000)")
    print("WebSocket          | Socket.IO")
    print("Async/Await        | Threading")
    print("Auto API Docs      | Manual Docs")
    print("Modern             | Traditional")
    
    print("\n💡 Integration Examples:")
    print("-" * 30)
    print("1. 🔗 Use both servers simultaneously")
    print("2. 🏗️ Hybrid architecture with FastAPI microservices")
    print("3. 🔄 Cross-server communication via HTTP APIs")
    
    if fastapi_healthy and flask_healthy:
        print("\n🎉 Both servers are running! You can now:")
        print("   - Compare the interfaces side by side")
        print("   - Test performance differences")
        print("   - Explore different integration patterns")
    
    print("\n📚 For more details, see the updated README.md")

if __name__ == "__main__":
    main() 