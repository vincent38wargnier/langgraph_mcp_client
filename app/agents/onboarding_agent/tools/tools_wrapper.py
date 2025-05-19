from typing import Dict, Any, Annotated, List
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState
import sys
import importlib
import traceback
import asyncio
import logging
import requests
import os
from app.settings.config import settings
from app.utils.magic_print import magic_print

# Set up logging to capture detailed error info
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_tools")

# Echo tool for local testing
@tool
async def echo_tool(
    message: str,
    state: Annotated[dict, InjectedState]
) -> Dict[str, Any]:
    """A simple echo tool that returns the message passed to it.
    This is useful for testing the agent's ability to use tools.
    
    Args:
        message: The message to echo back
        
    Returns:
        Dict[str, Any]: A dictionary containing the echoed message
    """
    return {
        "success": True,
        "message": f"Echo: {message}"
    }

# Function to connect to MCP server
async def connect_to_mcp_server():
    """Connect to the MCP server using the endpoint that works."""
    # Get the correct MCP endpoint - use the one that works from testing
    mcp_url = "https://magify.app.n8n.cloud/mcp/d36d2dcd-b620-4efb-aab0-972d691a8550/sse"
    magic_print(f"Connecting to MCP server at: {mcp_url}", "blue")
    
    # Try using the SSE endpoint
    try:
        from langchain_mcp_adapters.client import MultiServerMCPClient
        
        # Configure the client
        client_config = {
            "magify": {
                "url": mcp_url,
                "transport": "sse" 
            }
        }
        
        magic_print(f"Client configuration: {client_config}", "cyan")
        
        # Create the client using the correct pattern
        client = MultiServerMCPClient(client_config)
        
        # Get available tools
        magic_print("Fetching tools...", "blue")
        tools = await asyncio.wait_for(client.get_tools(), timeout=30.0)
        
        if tools:
            magic_print(f"✅ Successfully connected to MCP server!", "green")
            final_tools = []
            
            for tool in tools:
                magic_print(f"  - Found tool: {tool.name}", "green")
                
                # Use the tool directly without trying to modify its properties
                final_tools.append(tool)
            
            return final_tools
        else:
            magic_print("⚠️ No tools found from MCP server", "yellow")
    except Exception as e:
        magic_print(f"❌ Failed to connect to MCP server: {str(e)}", "red")
        magic_print(traceback.format_exc(), "red")
    
    # If we reach here, connection failed
    magic_print("❌ Failed to connect to MCP server", "red") 
    return []

# Initialize tools
def initialize_tools():
    """Initialize tools by connecting to the MCP server"""
    magic_print("🔧 Initializing tools...", "blue")
    
    try:
        # Check for required packages
        try:
            import langchain_mcp_adapters
            ver = getattr(langchain_mcp_adapters, "__version__", "unknown")
            magic_print(f"✅ Found langchain_mcp_adapters version {ver}", "green")
        except ImportError:
            magic_print("❌ langchain_mcp_adapters not found", "red")
            magic_print("Install with: pip install langchain-mcp-adapters", "yellow")
            return [echo_tool]
        
        # Set up asyncio event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Connect to MCP server
        if loop.is_running():
            magic_print("⚠️ Event loop already running, can't fetch MCP tools", "yellow")
            mcp_tools = []
        else:
            mcp_tools = loop.run_until_complete(connect_to_mcp_server())
        
        # Add MCP tools to the list
        if mcp_tools:
            tool_names = [tool.name for tool in mcp_tools]
            magic_print(f"✅ Successfully loaded {len(mcp_tools)} MCP tools: {', '.join(tool_names)}", "green")
            return [echo_tool] + mcp_tools
    except Exception as e:
        magic_print(f"❌ Error initializing tools: {str(e)}", "red")
        magic_print(traceback.format_exc(), "red")
    
    magic_print("⚠️ Using only echo_tool (no MCP tools available)", "yellow")
    return [echo_tool]

# Initialize the tools
tools_wrapper = initialize_tools()

# Log available tools
magic_print(f"⚙️ Total tools available: {len(tools_wrapper)}", "green")
for i, tool in enumerate(tools_wrapper, 1):
    name = getattr(tool, 'name', str(tool))
    desc = getattr(tool, 'description', '')[:50] + '...' if hasattr(tool, 'description') else ''
    magic_print(f"  {i}. {name} {desc}", "cyan")
