import asyncio
import json
import os
import logging
from pathlib import Path
from typing import Dict, Any
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from mcp import ClientSession, StdioServerParameters  
from mcp.client.stdio import stdio_client
from mcp.types import TextContent
import sys
sys.path.append('..')
from server.mcp_connection_manager import MCPConnectionManager, ConnectionConfig, connect_to_tesseract_server
import uvicorn

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Setup directories for static files and templates
web_dir = Path(__file__).parent
static_dir = web_dir / "static"
templates_dir = web_dir / "templates"

# Create directories if they don't exist
static_dir.mkdir(exist_ok=True)
templates_dir.mkdir(exist_ok=True)

# Store active WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected")
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"Client {client_id} disconnected")
    
    async def send_personal_message(self, message: dict, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(json.dumps(message))
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections.values():
            await connection.send_text(json.dumps(message))

manager = ConnectionManager()

class MCPTesseractClient:
    def __init__(self):
        # Use the robust connection manager
        self.connection_manager: Optional[MCPConnectionManager] = None
        
    async def connect(self):
        """Connect to the MCP Tesseract server using robust connection manager"""
        try:
            # Create connection manager with custom config for longer timeouts
            config = ConnectionConfig(
                connection_timeout=60.0,    # 1 minute for connection
                ready_timeout=120.0,        # 2 minutes to be ready
                tool_discovery_timeout=30.0, # 30s for tool discovery
                max_retries=5,              # More retries
                retry_delay=3.0             # Longer retry delay
            )
            
            logger.info("🔌 Connecting to MCP server with robust connection manager...")
            self.connection_manager = await connect_to_tesseract_server(config)
            logger.info("✅ MCP server connected and ready!")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            return False
    
    async def call_tool(self, tool_name: str, args: dict) -> str:
        """Call a tool on the MCP server using robust connection manager"""
        try:
            if not self.connection_manager or not self.connection_manager.is_ready():
                logger.info("Connection not ready, attempting to connect...")
                if not await self.connect():
                    return "Error: Unable to connect to MCP server"
            
            # Use the robust call_tool_safe method with massive timeout
            return await self.connection_manager.call_tool_safe(
                tool_name, 
                args, 
                timeout=7200.0  # 2 HOURS timeout for LLM operations
            )
            
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            return f"Error: {str(e)}"
    
    async def disconnect(self):
        """Disconnect from the MCP server"""
        if self.connection_manager:
            await self.connection_manager.disconnect()
            self.connection_manager = None
    
    def get_tools(self):
        """Get available tools"""
        if self.connection_manager:
            return self.connection_manager.get_tools()
        return []

# Global MCP client instance
mcp_client = MCPTesseractClient()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application lifespan events"""
    # Startup
    logger.info("Starting up FastAPI application...")
    success = await mcp_client.connect()
    if not success:
        logger.warning("Failed to connect to MCP server on startup - will retry on first request")
    
    yield
    
    # Shutdown
    logger.info("Shutting down FastAPI application...")
    await mcp_client.disconnect()

# Create FastAPI app with lifespan
app = FastAPI(
    title="Tesseract OCR Web Interface", 
    version="1.0.0",
    lifespan=lifespan
)

# Mount static files and setup templates after app creation
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
templates = Jinja2Templates(directory=str(templates_dir))

@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    """Serve the main web interface"""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "tools": mcp_client.tools
    })

@app.get("/tools")
async def get_tools():
    """Get available MCP tools"""
    return {"tools": mcp_client.tools}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload an image file for OCR processing"""
    try:
        # Ensure upload directory exists
        upload_dir = Path("image_folder")
        upload_dir.mkdir(exist_ok=True)
        
        # Save uploaded file
        file_path = upload_dir / file.filename
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        return {"filename": file.filename, "path": str(file_path), "message": "File uploaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/download/{filename}")
async def download_file(filename: str):
    """Download a transcription file"""
    file_path = Path("transcriptions") / filename
    if file_path.exists():
        return FileResponse(str(file_path), filename=filename)
    else:
        raise HTTPException(status_code=404, detail="File not found")

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time communication"""
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Send acknowledgment
            await manager.send_personal_message({
                "type": "status",
                "message": f"Processing: {message.get('action', 'unknown')}"
            }, client_id)
            
            # Process the request
            try:
                result = await process_websocket_message(message, client_id)
                await manager.send_personal_message(result, client_id)
            except Exception as e:
                await manager.send_personal_message({
                    "type": "error",
                    "message": f"Processing error: {str(e)}"
                }, client_id)
                
    except WebSocketDisconnect:
        manager.disconnect(client_id)

async def process_websocket_message(message: dict, client_id: str) -> dict:
    """Process incoming WebSocket messages"""
    action = message.get("action")
    
    if action == "ocr_single":
        # OCR single image
        image_path = message.get("image_path")
        output_folder = message.get("output_folder", "transcriptions")
        
        result = await mcp_client.call_tool("ocr_image_to_text", {
            "image_path": image_path,
            "output_folder": output_folder
        })
        
        return {
            "type": "ocr_result",
            "action": action,
            "result": result,
            "image_path": image_path
        }
    
    elif action == "ocr_batch":
        # Batch OCR folder
        image_folder = message.get("image_folder", "image_folder")
        output_folder = message.get("output_folder", "transcriptions")
        
        result = await mcp_client.call_tool("batch_ocr_folder", {
            "image_folder": image_folder,
            "output_folder": output_folder
        })
        
        return {
            "type": "batch_result",
            "action": action,
            "result": result,
            "image_folder": image_folder
        }
    
    elif action == "word_frequency":
        # Word frequency operations
        operation = message.get("operation")
        
        if operation == "store":
            txt_file_path = message.get("txt_file_path")
            result = await mcp_client.call_tool("store_word_frequencies", {
                "txt_file_path": txt_file_path
            })
        elif operation == "query":
            word = message.get("word")
            result = await mcp_client.call_tool("query_word_frequency", {
                "word": word
            })
        elif operation == "get_all":
            limit = message.get("limit", 20)
            result = await mcp_client.call_tool("get_all_word_frequencies", {
                "limit": limit
            })
        elif operation == "clear":
            result = await mcp_client.call_tool("clear_word_frequencies", {})
        else:
            result = "Unknown word frequency operation"
        
        return {
            "type": "word_frequency_result",
            "action": action,
            "operation": operation,
            "result": result
        }
    
    elif action == "bibliography":
        # Bibliography operations
        operation = message.get("operation")
        
        if operation == "process_json":
            json_folder = message.get("json_folder", "json_truth")
            result = await mcp_client.call_tool("process_json_ground_truth", {
                "json_folder": json_folder
            })
        elif operation == "query_json":
            query = message.get("query")
            limit = message.get("limit", 20)
            result = await mcp_client.call_tool("query_json_bibliography", {
                "query": query,
                "limit": limit
            })
        elif operation == "search_author":
            author_name = message.get("author_name")
            result = await mcp_client.call_tool("search_by_author", {
                "author_name": author_name
            })
        elif operation == "search_year_range":
            start_year = message.get("start_year")
            end_year = message.get("end_year")
            result = await mcp_client.call_tool("search_by_year_range", {
                "start_year": start_year,
                "end_year": end_year
            })
        elif operation == "stats":
            result = await mcp_client.call_tool("get_json_bibliography_stats", {})
        elif operation == "display_all":
            format_type = message.get("format", "compact")
            limit = message.get("limit", 100)
            result = await mcp_client.call_tool("display_all_json_bibliography", {
                "format": format_type,
                "limit": limit
            })
        elif operation == "clear":
            result = await mcp_client.call_tool("clear_json_bibliography", {})
        else:
            result = "Unknown bibliography operation"
        
        return {
            "type": "bibliography_result",
            "action": action,
            "operation": operation,
            "result": result
        }
    
    else:
        return {
            "type": "error",
            "message": f"Unknown action: {action}"
        }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "mcp_connected": mcp_client.session is not None,
        "tools_available": len(mcp_client.tools)
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001) 