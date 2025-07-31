#!/usr/bin/env python3
"""
Debug script to test MCP timeouts and identify where they're failing
"""

import asyncio
import logging
import time
import os
from pathlib import Path

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from mcp import ClientSession, StdioServerParameters  
from mcp.client.stdio import stdio_client
from mcp.types import TextContent

# Set massive timeout environment variables
os.environ['OPENAI_TIMEOUT'] = '3600'
os.environ['OPENAI_IMG2JSON_TIMEOUT'] = '5400'
os.environ['MCP_TOOL_TIMEOUT'] = '7200'
os.environ['FASTAPI_TIMEOUT'] = '7200'

async def test_mcp_connection():
    """Test MCP connection with detailed timing"""
    logger.info("🔍 Starting MCP Connection Debug Test")
    
    start_time = time.time()
    
    try:
        logger.info("⏱️  Step 1: Creating server parameters...")
        server_params = StdioServerParameters(
            command="uv",
            args=["run", "mcp", "run", "server/tesseract.py"]
        )
        logger.info(f"✅ Server params created in {time.time() - start_time:.2f}s")
        
        logger.info("⏱️  Step 2: Connecting to stdio...")
        step2_start = time.time()
        async with stdio_client(server_params) as (read, write):
            logger.info(f"✅ STDIO connected in {time.time() - step2_start:.2f}s")
            
            logger.info("⏱️  Step 3: Creating client session...")
            step3_start = time.time()
            async with ClientSession(read, write) as session:
                logger.info(f"✅ Session created in {time.time() - step3_start:.2f}s")
                
                logger.info("⏱️  Step 4: Initializing session...")
                step4_start = time.time()
                await session.initialize()
                logger.info(f"✅ Session initialized in {time.time() - step4_start:.2f}s")
                
                logger.info("⏱️  Step 5: Listing tools...")
                step5_start = time.time()
                tools = await session.list_tools()
                logger.info(f"✅ Tools listed in {time.time() - step5_start:.2f}s")
                logger.info(f"📋 Available tools: {[tool.name for tool in tools.tools]}")
                
                logger.info("⏱️  Step 6: Testing openai_llm_img2json tool...")
                step6_start = time.time()
                
                # Use asyncio.wait_for with a very long timeout to see if it's our timeout or MCP's
                try:
                    result = await asyncio.wait_for(
                        session.call_tool("openai_llm_img2json", {}),
                        timeout=7200.0  # 2 hours
                    )
                    logger.info(f"✅ Tool executed in {time.time() - step6_start:.2f}s")
                    
                    if result.content:
                        content = result.content[0]
                        if isinstance(content, TextContent):
                            logger.info(f"📄 Result: {content.text[:200]}...")
                        else:
                            logger.info(f"📄 Result type: {type(content)}")
                    else:
                        logger.info("📄 No result content")
                        
                except asyncio.TimeoutError:
                    logger.error(f"❌ Tool timed out after {time.time() - step6_start:.2f}s")
                    return False
                except Exception as e:
                    logger.error(f"❌ Tool error after {time.time() - step6_start:.2f}s: {e}")
                    return False
                
    except Exception as e:
        logger.error(f"❌ Connection failed after {time.time() - start_time:.2f}s: {e}")
        return False
    
    total_time = time.time() - start_time
    logger.info(f"🎉 Total test completed in {total_time:.2f}s")
    return True

async def test_quick_tools():
    """Test some quick tools to see if the issue is specific to long-running tools"""
    logger.info("🔍 Testing quick tools...")
    
    try:
        server_params = StdioServerParameters(
            command="uv", 
            args=["run", "mcp", "run", "server/tesseract.py"]
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # Test listing tools (should be quick)
                start = time.time()
                tools = await session.list_tools()
                logger.info(f"✅ list_tools completed in {time.time() - start:.2f}s")
                
                # Try a potentially quicker tool if available
                for tool in tools.tools:
                    if 'health' in tool.name.lower() or 'ping' in tool.name.lower():
                        start = time.time()
                        result = await session.call_tool(tool.name, {})
                        logger.info(f"✅ {tool.name} completed in {time.time() - start:.2f}s")
                        break
                        
    except Exception as e:
        logger.error(f"❌ Quick tools test failed: {e}")

def main():
    """Main debug function"""
    print("🔧 MCP TIMEOUT DEBUG TOOL")
    print("=" * 50)
    
    # Show timeout config
    from config.timeout_config import TimeoutConfig
    TimeoutConfig.print_config()
    
    print("\n🧪 Running Connection Tests...")
    print("=" * 50)
    
    # Test 1: Quick tools
    try:
        asyncio.run(test_quick_tools())
    except Exception as e:
        logger.error(f"Quick tools test crashed: {e}")
    
    print("\n🧪 Running Full Tool Test...")
    print("=" * 50)
    
    # Test 2: Full connection and tool test  
    try:
        success = asyncio.run(test_mcp_connection())
        if success:
            print("🎉 All tests passed!")
        else:
            print("❌ Tests failed - check logs above")
    except Exception as e:
        logger.error(f"Full test crashed: {e}")

if __name__ == "__main__":
    main() 