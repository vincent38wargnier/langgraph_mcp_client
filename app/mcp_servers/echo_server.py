#!/usr/bin/env python3
"""
Simple MCP server using FastMCP that provides an echo tool.
This can be used for testing or as a fallback if external MCP servers are unavailable.

Run with:
python app/mcp_servers/echo_server.py
"""
import os
import sys
from mcp.server.fastmcp import FastMCP

# Create MCP server instance
mcp = FastMCP("echo_server")

@mcp.tool()
def echo_text(text: str) -> dict:
    """
    Simple echo tool that returns the text passed to it.
    
    Args:
        text: The text to echo back
        
    Returns:
        Dictionary with the echoed text
    """
    return {
        "result": f"Echo: {text}",
        "status": "success"
    }

@mcp.tool()
def get_current_time() -> dict:
    """
    Returns the current server time.
    
    Returns:
        Dictionary with the current time
    """
    from datetime import datetime
    return {
        "time": datetime.now().isoformat(),
        "status": "success"
    }

if __name__ == "__main__":
    print("Starting Echo MCP Server...")
    
    # Transport can be 'stdio', 'sse', 'websocket', or 'streamable_http'
    # For the CLI, we use stdio
    mcp.run(transport="stdio")
    
    print("Echo MCP Server stopped.") 