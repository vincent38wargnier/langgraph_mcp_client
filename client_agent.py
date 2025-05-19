from datetime import datetime
from uuid import uuid4
import asyncio
import json
import os
from dotenv import load_dotenv

from uagents import Agent, Protocol, Context
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    TextContent,
    chat_protocol_spec,
)

# Import the MCP client tools (if available)
try:
    from app.agents.onboarding_agent.tools.tools_wrapper import tools_wrapper, echo_tool
    has_mcp_tools = True
except ImportError:
    has_mcp_tools = False
    print("MCP tools not available. Running in standalone mode.")

# Load environment variables
load_dotenv()

# Initialise agent
client_agent = Agent(
    name="client_agent",
    port=8082,
    mailbox=True,
)

# Initialize the chat protocol
chat_proto = Protocol(spec=chat_protocol_spec)

# Your LangGraph Agent's address - Update with the correct address
langgraph_agent_address = "agent1q0zyxrneyaury3f5c7aj67hfa5w65cykzplxkst5f5mnyf4y3em3kplxn4t"

# Set up available tools if MCP is installed
available_tools = {}
if has_mcp_tools:
    for tool in tools_wrapper:
        tool_name = getattr(tool, 'name', str(tool))
        available_tools[tool_name] = tool
    print(f"Loaded {len(available_tools)} tools: {', '.join(available_tools.keys())}")

# Startup Handler - Print agent details
@client_agent.on_event("startup")
async def startup_handler(ctx: Context):
    # Print agent details
    ctx.logger.info(f"My name is {ctx.agent.name} and my address is {ctx.agent.address}")
    
    if has_mcp_tools:
        ctx.logger.info(f"MCP tools available: {', '.join(available_tools.keys())}")
    else:
        ctx.logger.info("Running without MCP tools")

    # Send initial message to LangGraph agent
    initial_message = ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=[TextContent(
            type="text", 
            text="I want to send query to tavily agent that Give me a list of latest agentic AI trends"
        )]
    )
    await ctx.send(langgraph_agent_address, initial_message)

# Process tool requests (if MCP tools are available)
async def execute_tool(tool_name, params):
    if not has_mcp_tools:
        return {
            "success": False,
            "error": "MCP tools not available"
        }
        
    if tool_name in available_tools:
        tool = available_tools[tool_name]
        try:
            print(f"Executing tool: {tool_name} with params: {params}")
            result = await tool(**params)
            return {
                "success": True,
                "tool": tool_name,
                "result": result
            }
        except Exception as e:
            return {
                "success": False,
                "tool": tool_name,
                "error": str(e)
            }
    else:
        return {
            "success": False,
            "error": f"Tool '{tool_name}' not found. Available tools: {list(available_tools.keys())}"
        }

# Message Handler - Process received messages and send acknowledgements
@chat_proto.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    for item in msg.content:
        if isinstance(item, TextContent):
            message_text = item.text
            ctx.logger.info(f"Received message from {sender}: {message_text}")
            
            # Send acknowledgment
            ack = ChatAcknowledgement(
                timestamp=datetime.utcnow(),
                acknowledged_msg_id=msg.msg_id
            )
            await ctx.send(sender, ack)
            
            # Check if it's a tool request
            if has_mcp_tools and message_text.startswith("/tool"):
                try:
                    # Parse tool request format: /tool tool_name param1=value1 param2=value2
                    parts = message_text.split()
                    tool_name = parts[1]
                    params = {}
                    
                    for part in parts[2:]:
                        if "=" in part:
                            key, value = part.split("=", 1)
                            params[key] = value
                    
                    # Execute the tool
                    result = await execute_tool(tool_name, params)
                    
                    # Send the result back
                    response = ChatMessage(
                        timestamp=datetime.utcnow(),
                        msg_id=uuid4(),
                        content=[TextContent(
                            type="text", 
                            text=f"Tool Result: {json.dumps(result, indent=2)}"
                        )]
                    )
                    await ctx.send(sender, response)
                except Exception as e:
                    # Send error message
                    error_msg = ChatMessage(
                        timestamp=datetime.utcnow(),
                        msg_id=uuid4(),
                        content=[TextContent(
                            type="text", 
                            text=f"Error executing tool: {str(e)}"
                        )]
                    )
                    await ctx.send(sender, error_msg)
            else:
                # For regular messages, simply respond
                response = ChatMessage(
                    timestamp=datetime.utcnow(),
                    msg_id=uuid4(),
                    content=[TextContent(
                        type="text", 
                        text=f"Received your message: {message_text}"
                    )]
                )
                await ctx.send(sender, response)

# Acknowledgement Handler - Process received acknowledgements
@chat_proto.on_message(ChatAcknowledgement)
async def handle_acknowledgement(ctx: Context, sender: str, msg: ChatAcknowledgement):
    ctx.logger.info(f"Received acknowledgement from {sender} for message: {msg.acknowledged_msg_id}")

# Include the protocol in the agent to enable the chat functionality
client_agent.include(chat_proto, publish_manifest=True)

if __name__ == '__main__':
    client_agent.run() 