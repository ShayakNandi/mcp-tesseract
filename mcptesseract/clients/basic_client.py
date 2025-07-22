import asyncio
import json
import os
from mcp import ClientSession, StdioServerParameters  
from mcp.client.stdio import stdio_client
from mcp.types import TextContent
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
            print("\n🤖 MCP Tesseract Client")
            print("💬 Type your message and press Enter. Type 'quit' to exit.\n")
            
            while True:
                user_input = input("You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("👋 Goodbye!")
                    break
                    
                if not user_input:
                    continue
                
                # Simple tool detection - look for keywords
                tool_to_use = None
                tool_args = {}
                
                if "ocr" in user_input.lower() and "image" in user_input.lower():
                    # Try to extract image path from user input
                    if "image_folder/" in user_input:
                        # Extract path
                        words = user_input.split()
                        for word in words:
                            if "image_folder/" in word or word.endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp')):
                                tool_to_use = "ocr_image_to_text"
                                tool_args = {"image_path": word}
                                break
                elif "batch" in user_input.lower() and "folder" in user_input.lower():
                    tool_to_use = "batch_ocr_folder"
                    # Extract folder path if provided
                    words = user_input.split()
                    for word in words:
                        if "/" in word and not word.endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp')):
                            tool_args = {"image_folder": word}
                            break
                    if not tool_args:
                        tool_args = {"image_folder": "image_folder"}
                elif "word freq" in user_input.lower() or "frequency" in user_input.lower():
                    if "store" in user_input.lower():
                        tool_to_use = "store_word_frequencies"
                        # Simple path extraction
                        words = user_input.split()
                        for word in words:
                            if word.endswith('.txt'):
                                tool_args = {"txt_file_path": word}
                                break
                    elif "query" in user_input.lower():
                        tool_to_use = "query_word_frequency"
                        # Extract word to query
                        words = user_input.replace("query", "").replace("frequency", "").replace("word", "").split()
                        for word in words:
                            if word.isalpha() and len(word) > 2:
                                tool_args = {"word": word}
                                break
                    else:
                        tool_to_use = "get_all_word_frequencies"
                elif "bibliography" in user_input.lower():
                    if "json" in user_input.lower():
                        if "process" in user_input.lower():
                            tool_to_use = "process_json_ground_truth"
                        elif "query" in user_input.lower():
                            # Extract query text
                            query_text = user_input.replace("bibliography", "").replace("json", "").replace("query", "").strip()
                            if query_text:
                                tool_to_use = "query_json_bibliography"
                                tool_args = {"query": query_text}
                        elif "stats" in user_input.lower():
                            tool_to_use = "get_json_bibliography_stats"
                        elif "display" in user_input.lower() or "show" in user_input.lower() or "all" in user_input.lower():
                            tool_to_use = "display_all_json_bibliography"
                    else:
                        if "process" in user_input.lower():
                            tool_to_use = "process_ground_truth_folder"
                        elif "query" in user_input.lower():
                            query_text = user_input.replace("bibliography", "").replace("query", "").strip()
                            if query_text:
                                tool_to_use = "query_bibliography"
                                tool_args = {"query": query_text}
                        elif "display" in user_input.lower() or "show" in user_input.lower() or "all" in user_input.lower():
                            tool_to_use = "display_all_bibliography_entries"
                
                # If we found a tool to use, execute it
                if tool_to_use:
                    print(f"🔧 Using tool: {tool_to_use}")
                    if tool_args:
                        print(f"📝 Arguments: {tool_args}")
                    
                    try:
                        result = await session.call_tool(tool_to_use, tool_args)
                        tool_result = "No result"
                        if result.content:
                            content = result.content[0]
                            if isinstance(content, TextContent):
                                tool_result = content.text
                            else:
                                tool_result = str(content)
                        
                        print(f"🤖 Assistant: {tool_result}\n")
                        
                    except Exception as e:
                        print(f"❌ Error executing tool: {e}\n")
                else:
                    # Fall back to LLM for general conversation
                    try:
                        # Check if OpenAI API key is available and valid
                        api_key = os.getenv("OPENAI_API_KEY")
                        if not api_key or len(api_key) < 10:
                            raise ValueError("OpenAI API key not configured")
                            
                        # Build tool descriptions for context
                        tool_descriptions = "\n".join([
                            f"- {tool.name}: {tool.description}" 
                            for tool in tools.tools
                        ])
                        
                        system_prompt = f"""You are a helpful assistant that can help with OCR and bibliography tasks. 
                        
Available tools:
{tool_descriptions}

For specific tasks, suggest the exact tool name and parameters the user should try."""
                        
                        response = await openai_client.chat.completions.create(
                            model="gpt-4o",
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_input}
                            ],
                            temperature=0.7
                        )
                        
                        assistant_response = response.choices[0].message.content or "I'm not sure how to help with that."
                        print(f"🤖 Assistant: {assistant_response}\n")
                        
                    except Exception as e:
                        # If OpenAI fails, provide helpful tool suggestions without LLM
                        print(f"🤖 Assistant: I can help you with these OCR and bibliography tasks:\n")
                        print("📄 OCR Commands:")
                        print("  - 'OCR image image_folder/Bib1.png' - Process a single image")
                        print("  - 'batch OCR folder image_folder' - Process all images in folder")
                        print("\n📊 Word Frequency:")
                        print("  - 'get all word frequencies' - Show word stats")
                        print("  - 'query word frequency [word]' - Find specific word count")
                        print("\n📚 Bibliography:")
                        print("  - 'display all json bibliography' - Show all JSON bibliography entries")
                        print("  - 'process json bibliography' - Import JSON bibliography data")
                        print("  - 'query json bibliography [topic]' - Search bibliography")
                        print("  - 'get json bibliography stats' - Show bibliography statistics")
                        print("\n💡 Tip: Try being more specific with your commands!\n")

if __name__ == "__main__":
    asyncio.run(main()) 