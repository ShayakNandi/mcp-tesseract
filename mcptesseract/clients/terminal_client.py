import asyncio
import json
import os
import sys
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from contextlib import asynccontextmanager

# MCP Client imports
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# LLM imports  
from openai import AsyncOpenAI

# Environment
from dotenv import load_dotenv

load_dotenv()

@dataclass
class MCPServer:
    name: str
    command: str
    args: List[str]
    env: Optional[Dict[str, str]] = None

class TerminalMCPClient:
    def __init__(self):
        self.servers: List[MCPServer] = []
        self.active_sessions: Dict[str, ClientSession] = {}
        self.available_tools: Dict[str, Any] = {}
        
        # Initialize OpenAI client
        self.llm_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o"
        
        self.conversation_history = []
        
    def add_server(self, name: str, command: str, args: List[str], env: Optional[Dict[str, str]] = None):
        """Add an MCP server to connect to"""
        server = MCPServer(name=name, command=command, args=args, env=env)
        self.servers.append(server)
        
    async def connect_to_servers(self):
        """Connect to all configured MCP servers"""
        print("🔌 Connecting to MCP servers...")
        
        for server in self.servers:
            try:
                server_params = StdioServerParameters(
                    command=server.command,
                    args=server.args,
                    env=server.env
                )
                
                # This creates the connection context
                connection = stdio_client(server_params)
                read, write = await connection.__aenter__()
                
                # Create session
                session = ClientSession(read, write)
                await session.initialize()
                
                self.active_sessions[server.name] = session
                
                # Discover tools
                tools = await session.list_tools()
                for tool in tools.tools:
                    tool_key = f"{server.name}_{tool.name}"
                    self.available_tools[tool_key] = {
                        'server': server.name,
                        'name': tool.name,
                        'description': tool.description,
                        'schema': tool.inputSchema,
                        'session': session
                    }
                    
                print(f"✅ Connected to {server.name} - {len(tools.tools)} tools available")
                
            except Exception as e:
                print(f"❌ Failed to connect to {server.name}: {e}")
                
        print(f"🛠️  Total tools available: {len(self.available_tools)}")
        
    async def process_query(self, user_input: str) -> str:
        """Process user query with LLM and handle tool calls"""
        
        # Add user message to history
        self.conversation_history.append({"role": "user", "content": user_input})
        
        # Prepare system prompt with tool information
        system_prompt = self._build_system_prompt()
        
        messages = [
            {"role": "system", "content": system_prompt},
            *self.conversation_history
        ]
        
        return await self._process_openai_query(messages)
            
    def _build_system_prompt(self) -> str:
        """Build system prompt with available tools"""
        tools_desc = []
        for tool_key, tool_info in self.available_tools.items():
            tools_desc.append(
                f"- {tool_info['name']}: {tool_info['description']}\n"
                f"  Schema: {json.dumps(tool_info['schema'], indent=2)}"
            )
            
        return f"""You are a helpful AI assistant with access to the following MCP tools:

{chr(10).join(tools_desc)}

When you need to use a tool, respond with JSON in this format:
{{
    "action": "use_tool",
    "tool": "tool_name",
    "arguments": {{...}}
}}

Otherwise, respond normally. Be conversational and helpful."""

    async def _process_openai_query(self, messages: List[Dict[str, str]]) -> str:
        """Process query using OpenAI with function calling"""
        
        # Convert MCP tools to OpenAI function format
        functions = []
        for tool_key, tool_info in self.available_tools.items():
            functions.append({
                "type": "function",
                "function": {
                    "name": tool_key,
                    "description": tool_info['description'],
                    "parameters": tool_info['schema']
                }
            })
        
        # Make initial API call
        response = await self.llm_client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=functions if functions else None,
            tool_choice="auto" if functions else None,
            temperature=0.7
        )
        
        message = response.choices[0].message
        
        # Handle tool calls
        if message.tool_calls:
            # Add assistant message to history
            self.conversation_history.append({
                "role": "assistant", 
                "content": message.content,
                "tool_calls": [tc.model_dump() for tc in message.tool_calls]
            })
            
            # Execute tool calls
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                
                print(f"🔧 Using tool: {tool_name}")
                print(f"📝 Arguments: {tool_args}")
                
                if tool_name in self.available_tools:
                    tool_info = self.available_tools[tool_name]
                    session = tool_info['session']
                    actual_tool_name = tool_info['name']
                    
                    try:
                        result = await session.call_tool(actual_tool_name, tool_args)
                        tool_result = "No result"
                        if result.content:
                            from mcp.types import TextContent
                            content = result.content[0]
                            if isinstance(content, TextContent):
                                tool_result = content.text
                            else:
                                tool_result = str(content)
                        
                        # Add tool result to conversation
                        self.conversation_history.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": tool_result
                        })
                        
                        print(f"✅ Tool result: {tool_result[:200]}...")
                        
                    except Exception as e:
                        error_msg = f"Error executing tool: {e}"
                        self.conversation_history.append({
                            "role": "tool", 
                            "tool_call_id": tool_call.id,
                            "content": error_msg
                        })
                        print(f"❌ {error_msg}")
            
            # Get final response after tool execution
            final_response = await self.llm_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": self._build_system_prompt()}] + self.conversation_history,
                temperature=0.7
            )
            
            final_content = final_response.choices[0].message.content or "No response"
            self.conversation_history.append({"role": "assistant", "content": final_content})
            return final_content
            
        else:
            # No tool calls, regular response
            content = message.content or "No response"
            self.conversation_history.append({"role": "assistant", "content": content})
            return content

    async def chat_loop(self):
        """Main interactive chat loop"""
        print("🤖 Terminal MCP Client Started!")
        print("💬 Type your message and press Enter. Type 'quit' to exit.\n")
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("👋 Goodbye!")
                    break
                    
                if not user_input:
                    continue
                    
                print("🤔 Thinking...")
                response = await self.process_query(user_input)
                print(f"🤖 Assistant: {response}\n")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}\n")

    async def cleanup(self):
        """Clean up connections"""
        for session in self.active_sessions.values():
            # Session cleanup would go here
            pass

async def main():
    client = TerminalMCPClient()
    
    # Add your tesseract server
    client.add_server(
        name="tesseract",
        command="uv",
        args=["run", "mcp", "run", "server/tesseract.py"]  # Path to your server file
    )
    
    # Add other MCP servers as needed
    # client.add_server(
    #     name="weather", 
    #     command="uvx",
    #     args=["mcp-server-weather"]
    # )
    
    try:
        await client.connect_to_servers()
        await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
