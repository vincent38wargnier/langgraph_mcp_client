#!/usr/bin/env python3
"""
Quick script to fix the MCP endpoint in your .env file.
Run with: python fix_mcp_endpoint.py
"""
import os
import sys
import requests
from app.utils.magic_print import magic_print

def test_endpoint(url):
    """Test if an endpoint is accessible"""
    try:
        magic_print(f"Testing endpoint: {url}", "blue")
        response = requests.head(url, timeout=5)
        status = response.status_code
        magic_print(f"Status code: {status}", "cyan")
        return status < 400  # Any 2xx or 3xx status is considered OK
    except Exception as e:
        magic_print(f"Connection error: {str(e)}", "yellow")
        return False

def fix_env_file():
    """Fix the MCP endpoint in the .env file for proper MCP connection."""
    # Check if .env file exists
    if not os.path.exists('.env'):
        magic_print("❌ .env file not found", "red")
        magic_print("Please copy .env.example to .env and add your API keys", "yellow")
        return False
    
    # Read the .env file
    with open('.env', 'r') as f:
        lines = f.readlines()
    
    # Check if we have a working configuration from test_mcp_server.py
    mcp_endpoint = "https://magify.app.n8n.cloud/mcp/d36d2dcd-b620-4efb-aab0-972d691a8550"
    mcp_transport = "sse"
    
    if os.path.exists(".mcp_config"):
        magic_print("Found saved MCP configuration, using it", "green")
        with open(".mcp_config", "r") as f:
            config_lines = f.readlines()
            for line in config_lines:
                if line.startswith("MCP_ENDPOINT="):
                    mcp_endpoint = line.strip().split("=", 1)[1]
                    magic_print(f"Using saved endpoint: {mcp_endpoint}", "green")
                elif line.startswith("MCP_TRANSPORT="):
                    mcp_transport = line.strip().split("=", 1)[1]
                    magic_print(f"Using saved transport: {mcp_transport}", "green")
    else:
        magic_print(f"Using default endpoint: {mcp_endpoint}", "blue")
        magic_print(f"Using default transport: {mcp_transport}", "blue")
        magic_print("Tip: Run 'python test_mcp_server.py' to find a working configuration", "yellow")
    
    # Test the endpoint
    test_endpoint(mcp_endpoint)
    
    # Find and fix MCP_ENDPOINT line
    mcp_fixed = False
    for i, line in enumerate(lines):
        if line.startswith('MCP_ENDPOINT='):
            value = line.strip().split('=', 1)[1]
            
            # Update to the endpoint
            lines[i] = f'MCP_ENDPOINT={mcp_endpoint}\n'
            magic_print(f"✅ Updated MCP endpoint: {value} -> {mcp_endpoint}", "green")
            mcp_fixed = True
    
    # If MCP_ENDPOINT not found, add it
    if not mcp_fixed:
        lines.append('# MCP Server Endpoint\n')
        lines.append(f'MCP_ENDPOINT={mcp_endpoint}\n')
        magic_print(f"✅ Added MCP endpoint: {mcp_endpoint}", "green")
    
    # Fix transport method
    transport_fixed = False
    for i, line in enumerate(lines):
        if line.startswith('MCP_TRANSPORT='):
            lines[i] = f'MCP_TRANSPORT={mcp_transport}\n'
            transport_fixed = True
            magic_print(f"✅ Set MCP transport to '{mcp_transport}'", "green")
    
    if not transport_fixed:
        lines.append('# MCP transport method\n')
        lines.append(f'MCP_TRANSPORT={mcp_transport}\n')
        magic_print(f"✅ Added MCP transport setting: {mcp_transport}", "green")
    
    # Write back to .env file
    with open('.env', 'w') as f:
        f.writelines(lines)
    
    magic_print("✅ .env file updated", "green")
    
    # Also update .env.example for reference
    if os.path.exists('.env.example'):
        with open('.env.example', 'r') as f:
            example_lines = f.readlines()
        
        example_fixed = False
        for i, line in enumerate(example_lines):
            if line.startswith('MCP_ENDPOINT='):
                example_lines[i] = f'MCP_ENDPOINT={mcp_endpoint}\n'
                example_fixed = True
        
        if not example_fixed:
            example_lines.append('# MCP Server Endpoint\n')
            example_lines.append(f'MCP_ENDPOINT={mcp_endpoint}\n')
        
        # Update transport in .env.example too
        transport_fixed = False
        for i, line in enumerate(example_lines):
            if line.startswith('MCP_TRANSPORT='):
                example_lines[i] = f'MCP_TRANSPORT={mcp_transport}\n'
                transport_fixed = True
        
        if not transport_fixed:
            example_lines.append('# MCP transport method\n')
            example_lines.append(f'MCP_TRANSPORT={mcp_transport}\n')
        
        with open('.env.example', 'w') as f:
            f.writelines(example_lines)
        
        magic_print("✅ .env.example file also updated", "green")
    
    return True

if __name__ == "__main__":
    # Add the current directory to path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # Fix the .env file
    if fix_env_file():
        magic_print("\nMCP configuration updated. Please follow these steps:", "blue")
        magic_print("1. Test your MCP connection:", "cyan")
        magic_print("   python test_mcp_server.py", "yellow")
        magic_print("2. If the test finds a working configuration, run:", "cyan")
        magic_print("   python fix_mcp_endpoint.py", "yellow")
        magic_print("3. Run the agent:", "cyan")
        magic_print("   python main.py", "yellow")
    else:
        magic_print("Failed to update MCP endpoint", "red") 