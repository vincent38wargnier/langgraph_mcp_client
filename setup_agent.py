#!/usr/bin/env python3
"""
Setup script for MCP Client Agent
This script checks dependencies and configuration for the MCP client agent.
"""
import os
import sys
import subprocess
import importlib
from dotenv import load_dotenv, find_dotenv

def check_module(module_name):
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False

def install_requirements():
    print("📦 Installing requirements...")
    if os.path.exists("requirements.txt"):
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Requirements installed")
    else:
        print("❌ requirements.txt not found")
        return False
    return True

def check_env_file():
    dotenv_path = find_dotenv()
    if not dotenv_path:
        print("⚙️ Creating .env file with default settings...")
        with open(".env", "w") as f:
            f.write("MCP_ENDPOINT=https://magify.app.n8n.cloud/mcp/d36d2dcd-b620-4efb-aab0-972d691a8550/sse\n")
            f.write("MCP_TRANSPORT=sse\n")
        dotenv_path = ".env"
        print("✅ Created .env file")
    else:
        print(f"✅ Found .env file at {dotenv_path}")
    
    # Load .env file
    load_dotenv(dotenv_path)
    
    # Check if MCP endpoint is set
    mcp_endpoint = os.getenv("MCP_ENDPOINT")
    if not mcp_endpoint:
        print("⚠️ MCP_ENDPOINT not set in .env file")
        print("Adding default MCP endpoint...")
        with open(dotenv_path, "a") as f:
            f.write("\nMCP_ENDPOINT=https://magify.app.n8n.cloud/mcp/d36d2dcd-b620-4efb-aab0-972d691a8550/sse\n")
        os.environ["MCP_ENDPOINT"] = "https://magify.app.n8n.cloud/mcp/d36d2dcd-b620-4efb-aab0-972d691a8550/sse"
    else:
        print(f"✅ MCP_ENDPOINT is set to {mcp_endpoint}")
    
    # Check if MCP transport is set
    mcp_transport = os.getenv("MCP_TRANSPORT")
    if not mcp_transport:
        print("⚠️ MCP_TRANSPORT not set in .env file")
        print("Adding default MCP transport...")
        with open(dotenv_path, "a") as f:
            f.write("MCP_TRANSPORT=sse\n")
        os.environ["MCP_TRANSPORT"] = "sse"
    else:
        print(f"✅ MCP_TRANSPORT is set to {mcp_transport}")
    
    return True

def test_mcp_connection():
    try:
        import requests
        mcp_endpoint = os.getenv("MCP_ENDPOINT", "https://magify.app.n8n.cloud/mcp/d36d2dcd-b620-4efb-aab0-972d691a8550/sse")
        
        # Test basic connectivity (HEAD request)
        response = requests.head(mcp_endpoint)
        if response.status_code < 400:
            print(f"✅ Successfully connected to MCP endpoint: {mcp_endpoint}")
            print(f"   Status code: {response.status_code}")
            return True
        else:
            print(f"⚠️ MCP endpoint returned status code: {response.status_code}")
            if response.status_code == 404:
                print("   The endpoint might not exist or could be incorrect.")
                print("   Check your MCP_ENDPOINT in the .env file.")
            return False
    except Exception as e:
        print(f"❌ Failed to connect to MCP endpoint: {str(e)}")
        return False

def main():
    print("🤖 Setting up MCP Client Agent")
    print("=" * 50)
    
    # Check and install requirements
    if not install_requirements():
        print("❌ Failed to install requirements")
        return False
    
    # Check for required packages
    missing_modules = []
    required_modules = [
        "uagents", "dotenv", "httpx", "asyncio",
        "langchain_mcp_adapters", "requests", "json"
    ]
    
    for module in required_modules:
        if not check_module(module):
            missing_modules.append(module)
    
    if missing_modules:
        print(f"❌ Missing modules: {', '.join(missing_modules)}")
        print("Please install the missing modules.")
        return False
    
    # Check .env file
    if not check_env_file():
        print("❌ Failed to set up .env file")
        return False
    
    # Test MCP connection
    test_mcp_connection()
    
    print("\n✅ Setup complete!")
    print("You can now run the agent with: python client_agent.py")
    return True

if __name__ == "__main__":
    main() 