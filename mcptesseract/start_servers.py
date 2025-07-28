#!/usr/bin/env python3
"""
Convenient script to start both FastAPI and Flask servers
Handles port conflicts and provides clear instructions
"""

import subprocess
import sys
import time
import threading
import signal
import os
from pathlib import Path

class ServerManager:
    def __init__(self):
        self.processes = []
        self.running = True
        
    def start_server(self, name, script, port, delay=0):
        """Start a server in a separate process"""
        if delay:
            time.sleep(delay)
            
        print(f"🚀 Starting {name} on port {port}...")
        try:
            process = subprocess.Popen(
                [sys.executable, script],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            self.processes.append((name, process, port))
            
            # Monitor the process output
            def monitor_output():
                while self.running and process.poll() is None:
                    line = process.stdout.readline()
                    if line:
                        print(f"[{name}] {line.strip()}")
            
            thread = threading.Thread(target=monitor_output, daemon=True)
            thread.start()
            
            return True
        except Exception as e:
            print(f"❌ Failed to start {name}: {e}")
            return False
    
    def stop_all(self):
        """Stop all running servers"""
        print("\n🛑 Stopping all servers...")
        self.running = False
        
        for name, process, port in self.processes:
            try:
                process.terminate()
                process.wait(timeout=5)
                print(f"✅ Stopped {name}")
            except subprocess.TimeoutExpired:
                process.kill()
                print(f"🔪 Force killed {name}")
            except Exception as e:
                print(f"⚠️ Error stopping {name}: {e}")
        
        self.processes = []

def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    print("\n\n🛑 Received interrupt signal...")
    manager.stop_all()
    sys.exit(0)

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import flask
        import flask_socketio
        import fastapi
        import uvicorn
        print("✅ All dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("💡 Run: uv sync")
        return False

def main():
    print("🎯 Tesseract OCR Server Manager")
    print("=" * 40)
    
    if not check_dependencies():
        return
    
    global manager
    manager = ServerManager()
    
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    choice = input("""
Choose an option:
1. Start FastAPI server only (port 8001)
2. Start Flask server only (port 5000)  
3. Start both servers (recommended for comparison)
4. Run test script

Enter your choice (1-4): """).strip()
    
    if choice == "1":
        print("\n🔥 Starting FastAPI server...")
        manager.start_server("FastAPI", "web/fastapi_app.py", 8001)
        print(f"\n✅ FastAPI server running at: http://localhost:8001")
        
    elif choice == "2":
        print("\n🔥 Starting Flask server...")
        manager.start_server("Flask", "web/run_flask.py", 5000)
        print(f"\n✅ Flask server running at: http://localhost:5000")
        
    elif choice == "3":
        print("\n🔥 Starting both servers...")
        
        # Start FastAPI first
        success1 = manager.start_server("FastAPI", "web/fastapi_app.py", 8001)
        time.sleep(2)
        
        # Start Flask with delay
        success2 = manager.start_server("Flask", "web/run_flask.py", 5000, delay=1)
        
        if success1 and success2:
            print("\n🎉 Both servers are starting!")
            print("📋 Access URLs:")
            print("   • FastAPI: http://localhost:8001")
            print("   • Flask:   http://localhost:5000")
            print("\n🆚 Compare the interfaces side by side!")
        else:
            print("❌ One or more servers failed to start")
            
    elif choice == "4":
        print("\n🧪 Running test script...")
        subprocess.run([sys.executable, "test_both_servers.py"])
        return
        
    else:
        print("❌ Invalid choice")
        return
    
    # Keep the script running
    try:
        print("\n⌨️ Press Ctrl+C to stop all servers")
        while manager.running:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        manager.stop_all()

if __name__ == "__main__":
    main() 