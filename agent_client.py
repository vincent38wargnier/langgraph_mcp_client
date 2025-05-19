from datetime import datetime
from uuid import uuid4
from uagents import Agent, Protocol, Context
from dotenv import load_dotenv
import os

# Import the necessary components from the chat protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    TextContent,
    chat_protocol_spec,
)

# Load environment variables
load_dotenv()

# Initialize client agent
client_agent = Agent(
    name="mcp_client_agent",
    port=8082,
    mailbox=True,
)

# Initialize the chat protocol
chat_proto = Protocol(spec=chat_protocol_spec)

# Replace with your onboarding agent's address after running agent.py
onboarding_agent_address = os.environ.get("AGENT_ADDRESS", "")
if not onboarding_agent_address:
    print("⚠️ Warning: AGENT_ADDRESS not set in environment. You need to set this after running agent.py")

# Startup Handler - Print agent details and send initial message
@client_agent.on_event("startup")
async def startup_handler(ctx: Context):
    # Print agent details
    ctx.logger.info(f"Client agent started with address: {ctx.agent.address}")
    
    if onboarding_agent_address:
        # Send initial message to onboarding agent
        initial_message = ChatMessage(
            timestamp=datetime.utcnow(),
            msg_id=uuid4(),
            content=[TextContent(
                type="text", 
                text="Hello! I'm a new user. Can you tell me about the MCP tools available?"
            )]
        )
        await ctx.send(onboarding_agent_address, initial_message)
    else:
        ctx.logger.error("Cannot send message: onboarding agent address not configured")
        ctx.logger.info("Set AGENT_ADDRESS environment variable with the address from agent.py output")

# Message Handler - Process received messages and send acknowledgements
@chat_proto.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    for item in msg.content:
        if isinstance(item, TextContent):
            # Log received message
            ctx.logger.info(f"Received from agent: {item.text}")
            
            # Send acknowledgment
            ack = ChatAcknowledgement(
                timestamp=datetime.utcnow(),
                acknowledged_msg_id=msg.msg_id
            )
            await ctx.send(sender, ack)
            
            # Ask follow-up question after a brief delay
            if "tools" in item.text.lower() and onboarding_agent_address:
                # Send follow-up message
                follow_up = ChatMessage(
                    timestamp=datetime.utcnow(),
                    msg_id=uuid4(),
                    content=[TextContent(
                        type="text", 
                        text="Can you show me an example of how to use one of these tools?"
                    )]
                )
                await ctx.send(onboarding_agent_address, follow_up)

# Acknowledgement Handler - Process received acknowledgements
@chat_proto.on_message(ChatAcknowledgement)
async def handle_acknowledgement(ctx: Context, sender: str, msg: ChatAcknowledgement):
    ctx.logger.info(f"Received acknowledgement from {sender}")

# Include the protocol in the agent
client_agent.include(chat_proto, publish_manifest=True)

if __name__ == '__main__':
    print("🚀 Starting MCP client agent...")
    print("💡 This agent will send messages to the onboarding agent")
    if not onboarding_agent_address:
        print("⚠️ AGENT_ADDRESS not set. Update .env with the address from agent.py output")
    client_agent.run() 