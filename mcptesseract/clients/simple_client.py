import asyncio
import json
import os
from mcp import ClientSession, StdioServerParameters  
from mcp.client.stdio import stdio_client
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

async def main():
    # Configure your MCP server
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "mcp", "run", "server/tesseract.py"]  # Your server file
    )
    
    # Initialize OpenAI client
    openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Connect to MCP server
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Get available tools
            tools = await session.list_tools()
            print(f"Available tools: {[tool.name for tool in tools.tools]}")
            
            # Chat loop
            conversation = []
            
            while True:
                user_input = input("\nYou: ")
                if user_input.lower() in ['quit', 'exit']:
                    break
                    
                conversation.append({"role": "user", "content": user_input})
                
                # Send to LLM with tool descriptions
                tool_descriptions = "\n".join([
                    f"- {tool.name}: {tool.description}" 
                    for tool in tools.tools
                ])
                
                system_prompt = f"""You can use these tools:
{tool_descriptions}

To use a tool, respond with: USE_TOOL:tool_name:{{arguments}}"""
                
                messages = [
                    {"role": "system", "content": system_prompt},
                    *conversation
                ]
                
                response = await openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    temperature=0.7
                )
                
                assistant_response = response.choices[0].message.content
                
                # Check if LLM wants to use a tool
                if assistant_response and assistant_response.startswith("USE_TOOL:"):
                    parts = assistant_response.split(":", 2)
                    tool_name = parts[1] 
                    tool_args = json.loads(parts[2])
                    
                    print(f"Using tool: {tool_name}")
                    result = await session.call_tool(tool_name, tool_args)
                    tool_result = "No result"
                    if result.content:
                        from mcp.types import TextContent
                        content = result.content[0]
                        if isinstance(content, TextContent):
                            tool_result = content.text
                        else:
                            tool_result = str(content)
                    
                    # Get final response
                    conversation.append({"role": "assistant", "content": f"Used {tool_name}, got: {tool_result}"})
                    
                    final_response = await openai_client.chat.completions.create(
                        model="gpt-4o",
                        messages=[{"role": "system", "content": "Summarize the tool result naturally"}] + conversation,
                        temperature=0.7
                    )
                    
                    assistant_response = final_response.choices[0].message.content or "No response"
                
                conversation.append({"role": "assistant", "content": assistant_response})
                print(f"Assistant: {assistant_response}")

if __name__ == "__main__":
    asyncio.run(main())
