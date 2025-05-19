#!/usr/bin/env python3
"""
Test script to validate that our MCP server setup works correctly.
This tries multiple approaches to connect to the MCP server.

Run with:
python test_mcp_server.py
"""
import asyncio
import os
import sys
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.utils.magic_print import magic_print
from app.settings.config import settings

# Get MCP endpoint from settings
MCP_ENDPOINT = settings.MCP_ENDPOINT if hasattr(settings, 'MCP_ENDPOINT') else os.getenv('MCP_ENDPOINT', 
                "https://magify.app.n8n.cloud/mcp/d36d2dcd-b620-4efb-aab0-972d691a8550")

async def test_mcp_connection():
    """Test connecting to the MCP server with multiple transport methods"""
    try:
        from langchain_mcp_adapters.client import MultiServerMCPClient
        magic_print("✅ Successfully imported MultiServerMCPClient", "green")
    except ImportError as e:
        magic_print(f"❌ Failed to import MultiServerMCPClient: {e}", "red")
        magic_print("Try running: pip install langchain-mcp-adapters", "yellow")
        return False
        
    # Try HTTP request to test if server is accessible
    magic_print(f"Testing basic HTTP connection to: {MCP_ENDPOINT}", "blue")
    try:
        response = requests.head(MCP_ENDPOINT, timeout=5)
        magic_print(f"HTTP Status: {response.status_code}", "cyan")
        if response.status_code >= 400:
            magic_print(f"⚠️ Warning: Server returned HTTP {response.status_code}", "yellow")
    except Exception as e:
        magic_print(f"⚠️ Warning: HTTP connection failed: {str(e)}", "yellow")
    
    # Try different transport methods
    transport_methods = ["sse", "streamable_http", "websocket"]
    
    for transport in transport_methods:
        magic_print(f"\nTrying with {transport} transport...", "blue")
        
        # Prepare endpoints to try
        if transport == "sse":
            # For SSE, try both with and without /sse suffix
            base_url = MCP_ENDPOINT
            sse_url = f"{MCP_ENDPOINT}/sse" if not MCP_ENDPOINT.endswith("/sse") else MCP_ENDPOINT
            endpoints = [base_url, sse_url]
        else:
            # For other transports, just use the base URL
            endpoints = [MCP_ENDPOINT]
        
        for endpoint in endpoints:
            magic_print(f"Testing endpoint: {endpoint}", "cyan")
            
            try:
                # Configure client
                client_config = {
                    "magify": {
                        "url": endpoint,
                        "transport": transport
                    }
                }
                
                magic_print(f"Client config: {client_config}", "cyan")
                
                # Create client
                client = MultiServerMCPClient(client_config)
                
                # Try to get tools
                magic_print("Fetching tools...", "blue")
                tools = await asyncio.wait_for(client.get_tools(), timeout=10.0)
                
                if tools:
                    magic_print(f"✅ Success! Found {len(tools)} tools with {transport} transport", "green")
                    for i, tool in enumerate(tools, 1):
                        name = getattr(tool, "name", str(tool))
                        description = getattr(tool, "description", "No description")
                        magic_print(f"  {i}. {name}: {description}", "cyan")
                    
                    # Try calling a tool
                    if len(tools) > 0:
                        tool = tools[0]
                        magic_print(f"\nTesting tool: {tool.name}", "blue")
                        params = {"text": "Hello from test script!"} if "text" in str(tool.args) else {}
                        result = await tool.ainvoke(params)
                        magic_print(f"Result: {result}", "green")
                    
                    # Store the successful config for later
                    with open(".mcp_config", "w") as f:
                        f.write(f"MCP_ENDPOINT={endpoint}\n")
                        f.write(f"MCP_TRANSPORT={transport}\n")
                    magic_print("✅ Saved working configuration to .mcp_config", "green")
                    
                    return True
                else:
                    magic_print(f"⚠️ No tools found with {transport} on {endpoint}", "yellow")
            except Exception as e:
                magic_print(f"❌ Failed with {transport} on {endpoint}: {str(e)}", "red")
    
    magic_print("❌ All connection attempts failed", "red")
    return False

if __name__ == "__main__":
    # Print the current settings
    magic_print(f"Testing MCP server connection...", "blue")
    magic_print(f"MCP Endpoint: {MCP_ENDPOINT}", "blue")
    
    # Run the test
    success = asyncio.run(test_mcp_connection())
    
    if success:
        magic_print("\n✅ MCP server test successful!", "green")
        magic_print("You can now run the agent with:", "blue")
        magic_print("python main.py", "cyan")
    else:
        magic_print("\n❌ MCP server test failed", "red")
        magic_print("Try the following:", "blue")
        magic_print("1. Verify your MCP endpoint is correct", "yellow")
        magic_print("2. Check your network connection", "yellow")
        magic_print("3. Make sure the MCP server is running", "yellow")
        magic_print("4. Ask for the correct URL to the MCP server", "yellow") 