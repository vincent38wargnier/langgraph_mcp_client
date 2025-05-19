import os
import time
import asyncio
from dotenv import load_dotenv
import traceback

from uagents_adapter import LangchainRegisterTool, cleanup_uagent
from app.utils.magic_print import magic_print
from app.agents.onboarding_agent.graph import run_agent
from app.models import connect_to_mongo, close_mongo_connection
from langgraph.prebuilt import ToolNode

# Load environment variables
load_dotenv()

# Get API token for Agentverse
API_TOKEN = os.environ.get("AGENTVERSE_API_KEY", "")

if not API_TOKEN:
    raise ValueError("Please set AGENTVERSE_API_KEY environment variable")

# MongoDB connection
connect_to_mongo()

# Create a modified version of run_agent that uses ainvoke instead
def run_agent_modified(message, conversation_id=None):
    """A modified version of run_agent that uses ainvoke for LangGraph compatibility."""
    from app.agents.onboarding_agent.graphstate import GraphState
    from app.models.conversation import Conversation
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
    from app.agents.onboarding_agent.nodes.react_node import onaboarding_agent_node, model_with_tools
    
    magic_print("Starting simplified agent", "blue")
    
    # Get existing conversation or create new one using MongoDB
    magic_print(f"🔍 Conversation ID: {conversation_id}", "blue")
    conversation = Conversation.get_or_create(conversation_id)
    
    # Add user message to conversation
    magic_print("💾 Saving user message", "yellow")
    conversation.add_message("user", message)
    magic_print("User message added to conversation", "cyan")
    
    # Convert message format to LangChain format
    langchain_messages = []
    for msg in conversation.messages[-15:]:
        if msg['role'] == 'user':
            langchain_messages.append(HumanMessage(content=msg['content']))
        elif msg['role'] == 'assistant':
            langchain_messages.append(AIMessage(content=msg['content']))
        elif msg['role'] == 'system':
            langchain_messages.append(SystemMessage(content=msg['content']))
    
    # Create a simple state with just the messages
    state = GraphState(
        conversation_id=conversation.id,
        messages=langchain_messages,
        recursion_count=0,
        recursion_limit=10,
        timeout=100000
    )
    
    # Call the onboarding_agent_node directly rather than using the workflow
    magic_print("Calling onboarding agent directly", "blue")
    try:
        # Process with the agent node
        result = onaboarding_agent_node(state, {})
        
        # Get the last message
        last_message = result["messages"][-1].content
        
        # Add assistant's response to conversation
        magic_print("💾 Saving assistant message", "yellow")
        conversation.add_message("assistant", last_message)
        magic_print("Assistant response added to conversation", "cyan")
        
        # Check if conversation should end
        if any(word in message.lower() for word in ["goodbye", "bye", "quit", "exit"]):
            conversation.is_active = False
            conversation.save()
            magic_print("Conversation marked as inactive", "yellow")
        
        return {
            "response": last_message,
            "conversation_id": str(conversation.id)
        }
    except Exception as e:
        magic_print(f"Error in agent processing: {str(e)}", "red")
        magic_print(traceback.format_exc(), "red")
        raise

# Function that adapts input for the agent
def sync_agent_wrapper(query):
    """Synchronous wrapper function for the agent that properly handles input format"""
    # Extract the actual query text from different possible formats
    if isinstance(query, dict):
        if 'input' in query:
            query = query['input']
        elif 'message' in query:
            query = query['message']
        elif 'query' in query:
            query = query['query']
        elif 'text' in query:
            query = query['text']
        else:
            # If we can't find a known field, convert the whole dict to a string
            query = str(query)
    
    magic_print(f"📝 Processing query: {query}", "blue")
    
    # Create event loop for this call
    # loop = asyncio.new_event_loop()
    # asyncio.set_event_loop(loop)
    
    try:
        # Run our modified async function instead
        result = run_agent_modified(message=query)
        magic_print(f"💬 Result: {result}", "green")
        return result["response"]
    except Exception as e:
        magic_print(f"❌ Error processing query: {str(e)}", "red")
        return f"I encountered an error: {str(e)}"

# Register the onboarding agent via uAgent
tool = LangchainRegisterTool()
agent_info = tool.invoke(
    {
        "agent_obj": sync_agent_wrapper,
        "name": "mcp_onboarding_agent",
        "port": 8080,
        "description": "An MCP-powered onboarding agent that can access various tools",
        "api_token": API_TOKEN,
        "mailbox": True
    }
)

print(f"✅ Registered onboarding agent: {agent_info}")

# Keep the agent alive
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("🛑 Shutting down onboarding agent...")
    # Close MongoDB connection
    close_mongo_connection()
    # Clean up the uagent
    cleanup_uagent("mcp_onboarding_agent")
    print("✅ Agent stopped.") 