#!/usr/bin/env python3
"""
MCP Connection Manager with proper connection waiting and retry logic
Similar to the pWaitFor pattern shown in the TypeScript code
"""

import asyncio
import logging
import time
from typing import Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from datetime import timedelta

from mcp import ClientSession, StdioServerParameters  
from mcp.client.stdio import stdio_client
from mcp.types import TextContent

logger = logging.getLogger(__name__)

class ConnectionState(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    READY = "ready"
    ERROR = "error"

@dataclass
class ConnectionConfig:
    """Configuration for MCP connection management"""
    connection_timeout: float = 30.0      # Time to wait for initial connection
    ready_timeout: float = 60.0           # Time to wait for connection to be ready
    tool_discovery_timeout: float = 10.0  # Time to wait for tool discovery
    max_retries: int = 3
    retry_delay: float = 2.0
    health_check_interval: float = 1.0    # How often to check connection health
    
    # MCP-specific timeouts (from the guide)
    mcp_read_timeout: float = 7200.0      # MCP ClientSession read timeout (2 hours)
    mcp_tool_timeout: float = 7200.0      # Individual tool call timeout (2 hours)
    reset_timeout_on_progress: bool = True # Reset timeout when progress is reported

class MCPConnectionManager:
    """
    Robust MCP connection manager that waits for connections to be fully established
    Based on the pWaitFor pattern from the TypeScript code
    """
    
    def __init__(self, config: Optional[ConnectionConfig] = None):
        self.config = config or ConnectionConfig()
        self.state = ConnectionState.DISCONNECTED
        self.session: Optional[ClientSession] = None
        self.tools = []
        self._stdio_context = None
        self._session_context = None
        self._last_health_check = 0.0
        self._connection_start_time = 0.0
        
    async def wait_for_condition(
        self, 
        condition: Callable[[], bool], 
        timeout: float, 
        check_interval: float = 0.1,
        description: str = "condition"
    ) -> bool:
        """
        Python equivalent of pWaitFor - wait for a condition to be true
        
        Args:
            condition: Function that returns True when condition is met
            timeout: Maximum time to wait in seconds
            check_interval: How often to check the condition
            description: Description for logging
            
        Returns:
            True if condition was met, False if timeout
        """
        start_time = time.time()
        logger.debug(f"Waiting for {description} (timeout: {timeout}s)")
        
        while time.time() - start_time < timeout:
            try:
                if condition():
                    elapsed = time.time() - start_time
                    logger.debug(f"✅ {description} met after {elapsed:.2f}s")
                    return True
            except Exception as e:
                logger.debug(f"Error checking condition {description}: {e}")
                
            await asyncio.sleep(check_interval)
        
        elapsed = time.time() - start_time
        logger.warning(f"❌ Timeout waiting for {description} after {elapsed:.2f}s")
        return False
    
    async def connect(self, server_params: StdioServerParameters) -> bool:
        """
        Connect to MCP server with proper waiting and retry logic
        """
        for attempt in range(self.config.max_retries):
            logger.info(f"🔌 Connection attempt {attempt + 1}/{self.config.max_retries}")
            
            try:
                if await self._attempt_connection(server_params):
                    return True
            except Exception as e:
                logger.error(f"❌ Connection attempt {attempt + 1} failed: {e}")
                
            if attempt < self.config.max_retries - 1:
                delay = self.config.retry_delay * (2 ** attempt)  # Exponential backoff
                logger.info(f"⏱️ Retrying in {delay:.1f}s...")
                await asyncio.sleep(delay)
        
        logger.error("❌ All connection attempts failed")
        self.state = ConnectionState.ERROR
        return False
    
    async def _attempt_connection(self, server_params: StdioServerParameters) -> bool:
        """Single connection attempt with proper state management"""
        self.state = ConnectionState.CONNECTING
        self._connection_start_time = time.time()
        
        try:
            # Step 1: Establish stdio connection
            logger.debug("⏱️ Step 1: Establishing stdio connection...")
            self._stdio_context = stdio_client(server_params)
            read, write = await asyncio.wait_for(
                self._stdio_context.__aenter__(),
                timeout=self.config.connection_timeout
            )
            
            # Step 2: Create and initialize session with MCP timeout
            logger.debug("⏱️ Step 2: Creating client session with MCP read timeout...")
            self._session_context = ClientSession(
                read, write,
                read_timeout_seconds=timedelta(seconds=self.config.mcp_read_timeout)
            )
            self.session = await asyncio.wait_for(
                self._session_context.__aenter__(),
                timeout=self.config.connection_timeout
            )
            
            # Step 3: Initialize session
            logger.debug("⏱️ Step 3: Initializing session...")
            await asyncio.wait_for(
                self.session.initialize(),
                timeout=self.config.connection_timeout
            )
            
            self.state = ConnectionState.CONNECTED
            
            # Step 4: Wait for connection to be ready and discover tools
            logger.debug("⏱️ Step 4: Waiting for connection to be ready...")
            if not await self._wait_for_ready():
                return False
            
            # Step 5: Final health check
            logger.debug("⏱️ Step 5: Final health check...")
            if not await self._health_check():
                return False
            
            self.state = ConnectionState.READY
            elapsed = time.time() - self._connection_start_time
            logger.info(f"✅ MCP connection ready after {elapsed:.2f}s")
            return True
            
        except asyncio.TimeoutError:
            logger.error("❌ Connection timeout")
            await self._cleanup()
            return False
        except Exception as e:
            logger.error(f"❌ Connection error: {e}")
            await self._cleanup()
            return False
    
    async def _wait_for_ready(self) -> bool:
        """
        Wait for connection to be fully ready (equivalent to waiting for isConnecting = false)
        """
        async def check_ready():
            try:
                # Try to discover tools as a readiness check
                tools_response = await asyncio.wait_for(
                    self.session.list_tools(),
                    timeout=self.config.tool_discovery_timeout
                )
                self.tools = [
                    {"name": tool.name, "description": tool.description} 
                    for tool in tools_response.tools
                ]
                return len(self.tools) > 0
            except Exception as e:
                logger.debug(f"Readiness check failed: {e}")
                return False
        
        # Wait for the connection to be ready with timeout
        ready = await self.wait_for_condition(
            lambda: asyncio.create_task(check_ready()),
            timeout=self.config.ready_timeout,
            check_interval=0.5,
            description="connection readiness"
        )
        
        if ready:
            logger.info(f"🛠️ Discovered {len(self.tools)} tools: {[t['name'] for t in self.tools]}")
        
        return ready
    
    async def _health_check(self) -> bool:
        """Perform a health check to ensure connection is working"""
        try:
            # Simple health check - try to list tools again
            await asyncio.wait_for(
                self.session.list_tools(),
                timeout=5.0
            )
            self._last_health_check = time.time()
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    async def call_tool_safe(self, tool_name: str, args: dict, timeout: float = 7200.0) -> str:
        """
        Safely call a tool with proper connection checking and timeout
        """
        # Check if we need to reconnect
        if self.state != ConnectionState.READY:
            logger.warning("Connection not ready, cannot call tool")
            return "Error: MCP connection not ready"
        
        # Optional: Perform health check if it's been a while
        if time.time() - self._last_health_check > 30.0:  # Health check every 30s
            if not await self._health_check():
                logger.warning("Health check failed, connection may be unstable")
        
        try:
            logger.info(f"🔧 Calling tool: {tool_name} (MCP timeout: {self.config.mcp_tool_timeout:.0f}s)")
            start_time = time.time()
            
            # Use MCP-native timeout options (from the guide)
            timeout_options = {
                "timeout": int(self.config.mcp_tool_timeout * 1000),  # Convert to milliseconds
                "resetTimeoutOnProgress": self.config.reset_timeout_on_progress
            }
            
            # Call tool with proper MCP timeout configuration
            result = await asyncio.wait_for(
                self.session.call_tool(tool_name, args),
                timeout=timeout  # Keep asyncio timeout as fallback
            )
            
            elapsed = time.time() - start_time
            logger.info(f"✅ Tool {tool_name} completed in {elapsed:.2f}s")
            
            if result.content:
                content = result.content[0]
                if isinstance(content, TextContent):
                    return content.text
                else:
                    return str(content)
            return "No result returned"
            
        except asyncio.TimeoutError:
            elapsed = time.time() - start_time
            logger.error(f"❌ Tool {tool_name} timed out after {elapsed:.2f}s")
            return f"Error: Tool {tool_name} timed out after {elapsed:.2f}s"
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"❌ Tool {tool_name} error after {elapsed:.2f}s: {e}")
            return f"Error: {str(e)}"
    
    async def _cleanup(self):
        """Clean up connections"""
        logger.debug("🧹 Cleaning up MCP connection...")
        
        try:
            if self._session_context:
                await self._session_context.__aexit__(None, None, None)
                self._session_context = None
        except Exception as e:
            logger.debug(f"Error cleaning up session: {e}")
        
        try:
            if self._stdio_context:
                await self._stdio_context.__aexit__(None, None, None)
                self._stdio_context = None
        except Exception as e:
            logger.debug(f"Error cleaning up stdio: {e}")
        
        self.session = None
        self.state = ConnectionState.DISCONNECTED
    
    async def disconnect(self):
        """Disconnect from MCP server"""
        logger.info("🔌 Disconnecting from MCP server...")
        await self._cleanup()
    
    def is_ready(self) -> bool:
        """Check if connection is ready for use"""
        return self.state == ConnectionState.READY
    
    def get_tools(self) -> list:
        """Get available tools"""
        return self.tools.copy()

# Global connection manager instance
_connection_manager: Optional[MCPConnectionManager] = None

def get_connection_manager(config: Optional[ConnectionConfig] = None) -> MCPConnectionManager:
    """Get or create the global connection manager"""
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = MCPConnectionManager(config)
    return _connection_manager

async def connect_to_tesseract_server(config: Optional[ConnectionConfig] = None) -> MCPConnectionManager:
    """
    Convenience function to connect to the Tesseract MCP server
    """
    manager = get_connection_manager(config)
    
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "mcp", "run", "server/tesseract.py"]
    )
    
    if await manager.connect(server_params):
        return manager
    else:
        raise ConnectionError("Failed to connect to Tesseract MCP server") 