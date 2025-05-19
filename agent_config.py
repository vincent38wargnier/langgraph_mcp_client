from datetime import datetime
from uuid import uuid4
import asyncio
import os
from dotenv import load_dotenv

from uagents import Agent, Protocol, Context
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    TextContent,
    chat_protocol_spec,
)

# Import the MCP client tools
from app.agents.onboarding_agent.tools.tools_wrapper import tools_wrapper, echo_tool
from app.utils.magic_print import magic_print

# Load environment variables
load_dotenv()

# MCP Configuration
MCP_ENDPOINT = os.getenv("MCP_ENDPOINT", "https://magify.app.n8n.cloud/mcp/d36d2dcd-b620-4efb-aab0-972d691a8550/sse")
MCP_TRANSPORT = os.getenv("MCP_TRANSPORT", "sse")

# Initialize agent
client_agent = Agent(
    name="mcp_client_agent",
    port=8082,
    mailbox=True,
    seed="mcp_client_agent_seed"
)

# Initialize the chat protocol
chat_proto = Protocol(spec=chat_protocol_spec)

# Replace with your LangGraph Agent's address
langgraph_agent_address = "agent1q0zyxrneyaury3f5c7aj67hfa5w65cykzplxkst5f5mnyf4y3em3kplxn4t"

# Keep track of available tools
available_tools = {}
for tool in tools_wrapper:
    tool_name = getattr(tool, 'name', str(tool))
    available_tools[tool_name] = tool

# Startup Handler - Print agent details
@client_agent.on_event("startup")
async def startup_handler(ctx: Context):
    # Print agent details
    ctx.logger.info(f"MCP Client Agent started with address: {ctx.agent.address}")
    ctx.logger.info(f"Connected to MCP endpoint: {MCP_ENDPOINT}")
    
    # Log available tools
    tool_names = list(available_tools.keys())
    ctx.logger.info(f"Available tools: {', '.join(tool_names)}")
    
    # Send initial message to LangGraph agent
    initial_message = ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=[TextContent(
            type="text", 
            text="MCP Client Agent is now online and ready to process requests."
        )]
    )
    await ctx.send(langgraph_agent_address, initial_message)

# Process tool requests
async def execute_tool(tool_name, params):
    if tool_name in available_tools:
        tool = available_tools[tool_name]
        try:
            magic_print(f"Executing tool: {tool_name} with params: {params}", "blue")
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
        # Fallback to echo tool
        return {
            "success": False,
            "error": f"Tool '{tool_name}' not found. Available tools: {list(available_tools.keys())}"
        }

# Message Handler - Process received messages
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
            
            # Process the message to determine if it's a tool request
            if message_text.startswith("/tool"):
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
                            text=f"Tool Result: {result}"
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
                # For non-tool requests, use the echo tool
                result = await echo_tool(message=message_text, state={})
                
                response = ChatMessage(
                    timestamp=datetime.utcnow(),
                    msg_id=uuid4(),
                    content=[TextContent(
                        type="text", 
                        text=f"{result['message']}"
                    )]
                )
                await ctx.send(sender, response)

# Acknowledgement Handler
@chat_proto.on_message(ChatAcknowledgement)
async def handle_acknowledgement(ctx: Context, sender: str, msg: ChatAcknowledgement):
    ctx.logger.info(f"Received acknowledgement from {sender} for message: {msg.acknowledged_msg_id}")

# Include the protocol in the agent
client_agent.include(chat_proto, publish_manifest=True)

if __name__ == '__main__':
    client_agent.run() 