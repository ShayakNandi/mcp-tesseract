#!/usr/bin/env python3
"""
Test script for the robust MCP connection manager
Tests the pWaitFor-style connection pattern
"""

import asyncio
import logging
import time
import os
import sys

# Set up detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add server directory to path
sys.path.append('server')

from server.mcp_connection_manager import (
    MCPConnectionManager, 
    ConnectionConfig, 
    connect_to_tesseract_server,
    ConnectionState
)

async def test_basic_connection():
    """Test basic connection with default settings"""
    logger.info("🧪 Test 1: Basic Connection")
    
    try:
        manager = await connect_to_tesseract_server()
        logger.info(f"✅ Connected! State: {manager.state}")
        logger.info(f"🛠️ Tools: {[t['name'] for t in manager.get_tools()]}")
        
        await manager.disconnect()
        logger.info("✅ Disconnected successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Basic connection test failed: {e}")
        return False

async def test_robust_connection():
    """Test connection with custom robust settings"""
    logger.info("🧪 Test 2: Robust Connection with Custom Config")
    
    config = ConnectionConfig(
        connection_timeout=90.0,    # 1.5 minutes for connection
        ready_timeout=180.0,        # 3 minutes to be ready
        tool_discovery_timeout=60.0, # 1 minute for tool discovery
        max_retries=5,              # 5 retries
        retry_delay=5.0             # 5 second delay between retries
    )
    
    try:
        manager = await connect_to_tesseract_server(config)
        logger.info(f"✅ Robust connection! State: {manager.state}")
        logger.info(f"🛠️ Tools: {[t['name'] for t in manager.get_tools()]}")
        
        # Test a quick tool call
        if 'openai_llm_img2json' in [t['name'] for t in manager.get_tools()]:
            logger.info("🧪 Testing openai_llm_img2json tool...")
            start_time = time.time()
            
            result = await manager.call_tool_safe(
                'openai_llm_img2json', 
                {},
                timeout=600.0  # 10 minute test timeout
            )
            
            elapsed = time.time() - start_time
            logger.info(f"🎯 Tool result: {result[:100]}...")
            logger.info(f"⏱️ Tool completed in {elapsed:.2f}s")
            
        await manager.disconnect()
        logger.info("✅ Robust test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Robust connection test failed: {e}")
        return False

async def test_connection_states():
    """Test connection state transitions"""
    logger.info("🧪 Test 3: Connection State Monitoring")
    
    config = ConnectionConfig(
        connection_timeout=30.0,
        ready_timeout=60.0,
        max_retries=2
    )
    
    manager = MCPConnectionManager(config)
    
    # Check initial state
    logger.info(f"Initial state: {manager.state}")
    assert manager.state == ConnectionState.DISCONNECTED
    
    # Test connection
    from mcp import StdioServerParameters
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "mcp", "run", "server/tesseract.py"]
    )
    
    start_time = time.time()
    success = await manager.connect(server_params)
    elapsed = time.time() - start_time
    
    if success:
        logger.info(f"✅ Connection successful in {elapsed:.2f}s")
        logger.info(f"Final state: {manager.state}")
        assert manager.state == ConnectionState.READY
        
        await manager.disconnect()
        logger.info(f"After disconnect: {manager.state}")
        assert manager.state == ConnectionState.DISCONNECTED
        
        return True
    else:
        logger.error(f"❌ Connection failed after {elapsed:.2f}s")
        logger.info(f"Final state: {manager.state}")
        return False

async def test_error_scenarios():
    """Test error handling and recovery"""
    logger.info("🧪 Test 4: Error Handling")
    
    # Test with invalid server params
    config = ConnectionConfig(
        connection_timeout=10.0,  # Short timeout for quick failure
        max_retries=2
    )
    
    manager = MCPConnectionManager(config)
    
    # Try to connect to non-existent server
    from mcp import StdioServerParameters
    bad_params = StdioServerParameters(
        command="invalid_command",
        args=["invalid", "args"]
    )
    
    start_time = time.time()
    success = await manager.connect(bad_params)
    elapsed = time.time() - start_time
    
    if not success:
        logger.info(f"✅ Error handling worked - failed in {elapsed:.2f}s")
        logger.info(f"Error state: {manager.state}")
        assert manager.state == ConnectionState.ERROR
        return True
    else:
        logger.error("❌ Expected connection to fail but it succeeded")
        return False

def set_massive_timeouts():
    """Set massive timeout environment variables"""
    os.environ['OPENAI_TIMEOUT'] = '3600'
    os.environ['OPENAI_IMG2JSON_TIMEOUT'] = '5400'
    os.environ['MCP_TOOL_TIMEOUT'] = '7200'
    os.environ['FASTAPI_TIMEOUT'] = '7200'
    logger.info("🕐 Set massive timeout environment variables")

async def main():
    """Run all tests"""
    print("🔧 ROBUST MCP CONNECTION MANAGER TESTS")
    print("=" * 60)
    
    # Set massive timeouts
    set_massive_timeouts()
    
    # Show current timeout config
    try:
        from config.timeout_config import TimeoutConfig
        TimeoutConfig.print_config()
    except Exception as e:
        logger.warning(f"Could not load timeout config: {e}")
    
    print("\n" + "=" * 60)
    
    tests = [
        ("Basic Connection", test_basic_connection),
        ("Robust Connection", test_robust_connection),
        ("Connection States", test_connection_states),
        ("Error Handling", test_error_scenarios),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = await test_func()
            results.append((test_name, result))
            if result:
                logger.info(f"✅ {test_name} PASSED")
            else:
                logger.error(f"❌ {test_name} FAILED")
        except Exception as e:
            logger.error(f"💥 {test_name} CRASHED: {e}")
            results.append((test_name, False))
        
        # Brief pause between tests
        await asyncio.sleep(1)
    
    # Summary
    print(f"\n{'='*20} SUMMARY {'='*20}")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! The robust connection manager is working!")
    else:
        print("⚠️ Some tests failed. Check the logs above for details.")

if __name__ == "__main__":
    asyncio.run(main()) 