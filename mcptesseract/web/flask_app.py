import asyncio
import json
import os
import logging
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file
from flask_socketio import SocketIO, emit
import threading
from mcp import ClientSession, StdioServerParameters  
from mcp.client.stdio import stdio_client
from mcp.types import TextContent

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'tesseract_ocr_secret_key_2024'

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Setup paths
web_dir = Path(__file__).parent
static_dir = web_dir / "flask_static"
templates_dir = web_dir / "flask_templates"

# Create directories if they don't exist
static_dir.mkdir(exist_ok=True)
templates_dir.mkdir(exist_ok=True)

class MCPFlaskClient:
    def __init__(self):
        self.session = None
        self.tools = []
        self._stdio_context = None
        self._session_context = None
        self._loop = None
        self._thread = None
        
    def start_async_loop(self):
        """Start the asyncio loop in a separate thread"""
        if self._thread is None or not self._thread.is_alive():
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()
    
    def _run_loop(self):
        """Run the asyncio loop in a thread"""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()
    
    def run_async(self, coro):
        """Run an async function from sync context"""
        if self._loop is None:
            self.start_async_loop()
            # Wait a bit for the loop to start
            import time
            time.sleep(0.1)
        
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result(timeout=600)  # 10 minutes timeout for LLM operations
        
    async def _connect_async(self):
        """Connect to the MCP Tesseract server (async)"""
        try:
            server_params = StdioServerParameters(
                command="uv",
                args=["run", "mcp", "run", "server/tesseract.py"]
            )
            
            # Store the context managers for proper cleanup
            self._stdio_context = stdio_client(server_params)
            self.read, self.write = await self._stdio_context.__aenter__()
            
            self._session_context = ClientSession(self.read, self.write)
            self.session = await self._session_context.__aenter__()
            await self.session.initialize()
            
            # Get available tools
            tools_response = await self.session.list_tools()
            self.tools = [{"name": tool.name, "description": tool.description} for tool in tools_response.tools]
            
            logger.info(f"Connected to MCP server. Available tools: {[tool['name'] for tool in self.tools]}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            await self._cleanup_async()
            return False
    
    def connect(self):
        """Connect to the MCP server (sync wrapper)"""
        return self.run_async(self._connect_async())
    
    async def _call_tool_async(self, tool_name: str, args: dict) -> str:
        """Call a tool on the MCP server (async)"""
        try:
            if not self.session:
                logger.info("No session available, attempting to reconnect...")
                if not await self._connect_async():
                    return "Error: Unable to connect to MCP server"
            
            # Call tool with extended timeout for LLM operations
            result = await asyncio.wait_for(
                self.session.call_tool(tool_name, args),
                timeout=600.0  # 10 minutes timeout for LLM operations
            )
            
            if result.content:
                content = result.content[0]
                if isinstance(content, TextContent):
                    return content.text
                else:
                    return str(content)
            return "No result returned"
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            return f"Error: {str(e)}"
    
    def call_tool(self, tool_name: str, args: dict) -> str:
        """Call a tool on the MCP server (sync wrapper)"""
        return self.run_async(self._call_tool_async(tool_name, args))
    
    async def _cleanup_async(self):
        """Internal cleanup method (async)"""
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
    
    def disconnect(self):
        """Disconnect from the MCP server (sync wrapper)"""
        logger.info("Disconnecting from MCP server...")
        if self._loop and self._loop.is_running():
            self.run_async(self._cleanup_async())
        
        # Stop the event loop
        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)

# Global MCP client instance
mcp_client = MCPFlaskClient()

# Note: before_first_request is deprecated in Flask 3.0+
# Initialization will be handled by the run script or manually

# Flask Routes
@app.route('/')
def index():
    """Serve the main web interface"""
    return render_template('index.html', tools=mcp_client.tools)

@app.route('/api/tools')
def get_tools():
    """Get available MCP tools"""
    return jsonify({"tools": mcp_client.tools})

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Upload an image file for OCR processing"""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Ensure upload directory exists
        upload_dir = Path("image_folder")
        upload_dir.mkdir(exist_ok=True)
        
        # Save uploaded file
        file_path = upload_dir / file.filename
        file.save(str(file_path))
        
        return jsonify({
            "filename": file.filename, 
            "path": str(file_path), 
            "message": "File uploaded successfully"
        })
    except Exception as e:
        return jsonify({"error": f"Upload failed: {str(e)}"}), 500

@app.route('/api/download/<filename>')
def download_file(filename):
    """Download a transcription file"""
    file_path = Path("transcriptions") / filename
    if file_path.exists():
        return send_file(str(file_path), as_attachment=True, download_name=filename)
    else:
        return jsonify({"error": "File not found"}), 404

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "mcp_connected": mcp_client.session is not None,
        "tools_available": len(mcp_client.tools)
    })

# SocketIO Event Handlers
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info(f"Client connected: {request.sid}")
    emit('status', {'message': 'Connected to Flask OCR server'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('ocr_request')
def handle_ocr_request(data):
    """Handle OCR processing requests"""
    try:
        action = data.get('action')
        
        # Send acknowledgment
        emit('status', {'message': f'Processing: {action}'})
        
        if action == 'ocr_single':
            # OCR single image
            image_path = data.get('image_path')
            output_folder = data.get('output_folder', 'transcriptions')
            
            result = mcp_client.call_tool("ocr_image_to_text", {
                "image_path": image_path,
                "output_folder": output_folder
            })
            
            emit('ocr_result', {
                'type': 'ocr_result',
                'action': action,
                'result': result,
                'image_path': image_path
            })
        
        elif action == 'ocr_batch':
            # Batch OCR folder
            image_folder = data.get('image_folder', 'image_folder')
            output_folder = data.get('output_folder', 'transcriptions')
            
            result = mcp_client.call_tool("batch_ocr_folder", {
                "image_folder": image_folder,
                "output_folder": output_folder
            })
            
            emit('ocr_result', {
                'type': 'batch_result',
                'action': action,
                'result': result,
                'image_folder': image_folder
            })
        
        elif action == 'word_frequency':
            # Word frequency operations
            operation = data.get('operation')
            
            if operation == 'store':
                txt_file_path = data.get('txt_file_path')
                result = mcp_client.call_tool("store_word_frequencies", {
                    "txt_file_path": txt_file_path
                })
            elif operation == 'query':
                word = data.get('word')
                result = mcp_client.call_tool("query_word_frequency", {
                    "word": word
                })
            elif operation == 'get_all':
                limit = data.get('limit', 20)
                result = mcp_client.call_tool("get_all_word_frequencies", {
                    "limit": limit
                })
            elif operation == 'clear':
                result = mcp_client.call_tool("clear_word_frequencies", {})
            else:
                result = "Unknown word frequency operation"
            
            emit('ocr_result', {
                'type': 'word_frequency_result',
                'action': action,
                'operation': operation,
                'result': result
            })
        
        elif action == 'bibliography':
            # Bibliography operations
            operation = data.get('operation')
            
            if operation == 'process_json':
                json_folder = data.get('json_folder', 'json_truth')
                result = mcp_client.call_tool("process_json_ground_truth", {
                    "json_folder": json_folder
                })
            elif operation == 'query_json':
                query = data.get('query')
                limit = data.get('limit', 20)
                result = mcp_client.call_tool("query_json_bibliography", {
                    "query": query,
                    "limit": limit
                })
            elif operation == 'search_author':
                author_name = data.get('author_name')
                result = mcp_client.call_tool("search_by_author", {
                    "author_name": author_name
                })
            elif operation == 'search_year_range':
                start_year = data.get('start_year')
                end_year = data.get('end_year')
                result = mcp_client.call_tool("search_by_year_range", {
                    "start_year": start_year,
                    "end_year": end_year
                })
            elif operation == 'stats':
                result = mcp_client.call_tool("get_json_bibliography_stats", {})
            elif operation == 'display_all':
                format_type = data.get('format', 'compact')
                limit = data.get('limit', 100)
                result = mcp_client.call_tool("display_all_json_bibliography", {
                    "format": format_type,
                    "limit": limit
                })
            elif operation == 'clear':
                result = mcp_client.call_tool("clear_json_bibliography", {})
            else:
                result = "Unknown bibliography operation"
            
            emit('ocr_result', {
                'type': 'bibliography_result',
                'action': action,
                'operation': operation,
                'result': result
            })
        
        else:
            emit('error', {'message': f'Unknown action: {action}'})
            
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        emit('error', {'message': f'Processing error: {str(e)}'})

if __name__ == '__main__':
    logger.info("🚀 Starting Tesseract OCR Flask Server...")
    logger.info("📋 Available at: http://localhost:5000")
    logger.info("🔄 SocketIO endpoint: /socket.io/")
    logger.info("Press Ctrl+C to stop the server")
    logger.info("=" * 50)
    
    try:
        socketio.run(app, host='0.0.0.0', port=5000, debug=True)
    except KeyboardInterrupt:
        logger.info("\n👋 Server stopped by user")
        mcp_client.disconnect()
    except Exception as e:
        logger.error(f"❌ Error starting server: {e}")
        mcp_client.disconnect() 