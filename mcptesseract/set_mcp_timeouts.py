#!/usr/bin/env python3
"""
Set MCP timeout environment variables based on the comprehensive guide
"""

import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def set_mcp_timeouts():
    """Set all MCP timeout environment variables to massive values"""
    
    # MCP-specific environment variables (from the guide)
    timeout_settings = {
        # Primary MCP timeout (in milliseconds)
        "MCP_TIMEOUT": "7200000",  # 2 hours in milliseconds
        
        # OpenAI API timeouts (in seconds) 
        "OPENAI_TIMEOUT": "3600",  # 1 hour
        "OPENAI_IMG2JSON_TIMEOUT": "5400",  # 90 minutes
        
        # Google AI timeout
        "GOOGLE_AI_TIMEOUT": "3600",  # 1 hour
        
        # MCP tool timeout (seconds)
        "MCP_TOOL_TIMEOUT": "7200",  # 2 hours
        
        # Web interface timeouts
        "FASTAPI_TIMEOUT": "7200",  # 2 hours
        "FLASK_TIMEOUT": "7200",  # 2 hours
        
        # Connection timeouts
        "MCP_CONNECTION_TIMEOUT": "600",  # 10 minutes
        
        # WebSocket timeouts  
        "WEBSOCKET_TIMEOUT": "7200",  # 2 hours
        "SOCKETIO_TIMEOUT": "7200",  # 2 hours
        
        # Additional MCP settings
        "MCP_READ_TIMEOUT": "7200",  # 2 hours
        "MCP_RESET_TIMEOUT_ON_PROGRESS": "true",
    }
    
    logger.info("🕐 Setting massive MCP timeout environment variables...")
    
    for key, value in timeout_settings.items():
        os.environ[key] = value
        logger.info(f"   {key} = {value}")
    
    # Verify settings
    logger.info("\n✅ MCP Timeout Settings Applied:")
    logger.info(f"   🔥 MCP_TIMEOUT: {os.environ.get('MCP_TIMEOUT')} ms ({float(os.environ.get('MCP_TIMEOUT', 0))/60000:.1f} minutes)")
    logger.info(f"   🤖 OPENAI_TIMEOUT: {os.environ.get('OPENAI_TIMEOUT')} s ({float(os.environ.get('OPENAI_TIMEOUT', 0))/60:.1f} minutes)")
    logger.info(f"   📄 OPENAI_IMG2JSON_TIMEOUT: {os.environ.get('OPENAI_IMG2JSON_TIMEOUT')} s ({float(os.environ.get('OPENAI_IMG2JSON_TIMEOUT', 0))/60:.1f} minutes)")
    logger.info(f"   🔧 MCP_TOOL_TIMEOUT: {os.environ.get('MCP_TOOL_TIMEOUT')} s ({float(os.environ.get('MCP_TOOL_TIMEOUT', 0))/60:.1f} minutes)")
    
    return timeout_settings

def create_powershell_commands():
    """Generate PowerShell commands to set environment variables"""
    timeout_settings = {
        "MCP_TIMEOUT": "7200000",
        "OPENAI_TIMEOUT": "3600", 
        "OPENAI_IMG2JSON_TIMEOUT": "5400",
        "MCP_TOOL_TIMEOUT": "7200",
        "FASTAPI_TIMEOUT": "7200",
        "MCP_READ_TIMEOUT": "7200",
        "MCP_RESET_TIMEOUT_ON_PROGRESS": "true"
    }
    
    logger.info("\n💻 PowerShell Commands:")
    logger.info("Copy and run these commands in PowerShell:")
    logger.info("-" * 50)
    
    for key, value in timeout_settings.items():
        logger.info(f"$env:{key}={value}")
    
    # Single line version
    single_line = "; ".join([f"$env:{key}={value}" for key, value in timeout_settings.items()])
    logger.info(f"\n📋 Single line command:")
    logger.info(single_line)

def test_timeout_config():
    """Test the timeout configuration"""
    try:
        from config.timeout_config import TimeoutConfig
        logger.info("\n🧪 Testing timeout configuration...")
        TimeoutConfig.print_config()
        return True
    except Exception as e:
        logger.error(f"❌ Could not load timeout config: {e}")
        return False

def main():
    """Main function to set up all MCP timeouts"""
    print("🔧 MCP TIMEOUT ENVIRONMENT VARIABLE SETUP")
    print("=" * 60)
    print("Based on: How to Increase Timeout Window Length for MCPs")
    print("=" * 60)
    
    # Set environment variables
    settings = set_mcp_timeouts()
    
    # Generate PowerShell commands
    create_powershell_commands()
    
    # Test configuration
    test_timeout_config()
    
    print("\n🎯 Next Steps:")
    print("1. Run the PowerShell commands above to set environment variables")
    print("2. Start MCP Inspector: npx @modelcontextprotocol/inspector uv run mcp run server/tesseract.py")
    print("3. Test openai_llm_img2json tool with your JPG files")
    print("4. Tools will now run for up to 2 HOURS without timing out!")
    
    return settings

if __name__ == "__main__":
    main() 