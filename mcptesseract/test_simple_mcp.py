#!/usr/bin/env python3
"""
Simple test to check if MCP server starts and responds
"""

import asyncio
import subprocess
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_server_startup():
    """Test if the server can start without crashing"""
    logger.info("🧪 Testing MCP server startup...")
    
    try:
        # Start server as subprocess to capture output
        process = subprocess.Popen(
            ["uv", "run", "python", "server/tesseract.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd="."
        )
        
        # Give it a few seconds to start
        await asyncio.sleep(5)
        
        # Check if process is still running
        if process.poll() is None:
            logger.info("✅ Server is running!")
            
            # Terminate the process
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                
            return True
        else:
            # Process ended, get output
            stdout, stderr = process.communicate()
            logger.error(f"❌ Server crashed!")
            logger.error(f"STDOUT: {stdout}")
            logger.error(f"STDERR: {stderr}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Failed to start server: {e}")
        return False

async def test_mcp_run():
    """Test using uv run mcp run"""
    logger.info("🧪 Testing with 'uv run mcp run'...")
    
    try:
        process = subprocess.Popen(
            ["uv", "run", "mcp", "run", "server/tesseract.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd="."
        )
        
        # Give it time to start
        await asyncio.sleep(5)
        
        if process.poll() is None:
            logger.info("✅ MCP run is working!")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            return True
        else:
            stdout, stderr = process.communicate()
            logger.error(f"❌ MCP run failed!")
            logger.error(f"STDOUT: {stdout}")
            logger.error(f"STDERR: {stderr}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Failed to run mcp: {e}")
        return False

async def main():
    print("🔧 MCP SERVER STARTUP TEST")
    print("=" * 40)
    
    # Test 1: Direct python execution
    success1 = await test_server_startup()
    
    print()
    
    # Test 2: MCP run command
    success2 = await test_mcp_run()
    
    print("\n" + "=" * 40)
    print("RESULTS:")
    print(f"  Direct Python: {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"  MCP Run:       {'✅ PASS' if success2 else '❌ FAIL'}")
    
    if success1 and success2:
        print("🎉 Server startup is working!")
    elif success2:
        print("⚠️ Use 'uv run mcp run' - direct python has issues")
    else:
        print("❌ Server has startup problems - check dependencies")

if __name__ == "__main__":
    asyncio.run(main()) 