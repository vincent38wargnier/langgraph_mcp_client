"""
Standalone script to test MCP connection.
Run with: python mcp_test.py
"""
import asyncio
import sys
import os
import traceback
import requests

# Add the root directory to sys.path to handle imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.utils.magic_print import magic_print
from app.settings.config import settings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_mcp_connection():
    """Test connection to MCP server using different methods."""
    magic_print("=" * 60, "blue")
    magic_print("🔧 MCP CONNECTION TEST", "blue")
    magic_print("=" * 60, "blue")
    
    # 1. Check settings and environment
    magic_print("\n1. ENVIRONMENT CHECK", "green")
    
    mcp_url = settings.MCP_ENDPOINT
    magic_print(f"MCP Endpoint from settings: {mcp_url}", "cyan")
    
    env_url = os.getenv("MCP_ENDPOINT", "Not set")
    magic_print(f"MCP Endpoint from env: {env_url}", "cyan")
    
    # 2. Direct HTTP request test
    magic_print("\n2. DIRECT HTTP REQUEST TEST", "green")
    
    try:
        magic_print(f"Sending GET request to: {mcp_url}", "cyan")
        response = requests.get(mcp_url, timeout=10)
        magic_print(f"Response status: {response.status_code}", "cyan")
        magic_print(f"Response headers: {dict(response.headers)}", "cyan")
        
        if len(response.content) < 1000:
            magic_print(f"Response content: {response.text}", "cyan")
        else:
            magic_print(f"Response content length: {len(response.content)} bytes", "cyan")
    except Exception as e:
        magic_print(f"❌ HTTP request failed: {str(e)}", "red")
    
    # 3. Test with MCP clients
    magic_print("\n3. MCP CLIENT TEST", "green")
    
    # Method 1: Test with MultiServerMCPClient
    magic_print("\n3.1 Testing with MultiServerMCPClient", "cyan")
    try:
        from langchain_mcp_adapters.client import MultiServerMCPClient
        
        client_config = {
            "magify": {
                "url": mcp_url,
                "transport": "http"
            }
        }
        
        magic_print(f"Creating client with config: {client_config}", "cyan")
        client = MultiServerMCPClient(client_config)
        
        magic_print("Fetching tools (with 30s timeout)...", "cyan")
        tools = await asyncio.wait_for(client.get_tools(), timeout=30.0)
        
        if tools:
            magic_print(f"✅ Success! Found {len(tools)} tools", "green")
            for i, tool in enumerate(tools, 1):
                magic_print(f"  {i}. {tool.name} - {getattr(tool, 'description', 'No description')[:50]}...", "green")
        else:
            magic_print("⚠️ No tools found", "yellow")
    except ImportError:
        magic_print("❌ Could not import MultiServerMCPClient", "red")
    except Exception as e:
        magic_print(f"❌ MultiServerMCPClient test failed: {str(e)}", "red")
        magic_print(traceback.format_exc(), "red")
    
    # Method 2: Try single-server client if available
    magic_print("\n3.2 Testing with alternative client methods", "cyan")
    try:
        # Import whatever client is available
        import langchain_mcp_adapters
        
        magic_print(f"Available MCP modules: {dir(langchain_mcp_adapters)}", "cyan")
        
        # Try alternative import if MultiServerMCPClient failed
        if hasattr(langchain_mcp_adapters, 'client') and hasattr(langchain_mcp_adapters.client, 'MCPClient'):
            from langchain_mcp_adapters.client import MCPClient
            
            magic_print("Creating MCPClient...", "cyan")
            alt_client = MCPClient(url=mcp_url, transport="http")
            
            magic_print("Fetching tools...", "cyan")
            alt_tools = await asyncio.wait_for(alt_client.get_tools(), timeout=30.0)
            
            if alt_tools:
                magic_print(f"✅ Success with MCPClient! Found {len(alt_tools)} tools", "green")
            else:
                magic_print("⚠️ No tools found with MCPClient", "yellow")
    except ImportError:
        magic_print("❌ Could not import alternative client", "red")
    except Exception as e:
        magic_print(f"❌ Alternative client test failed: {str(e)}", "red")
    
    magic_print("\nMCP CONNECTION TEST COMPLETE", "blue")

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_mcp_connection()) 