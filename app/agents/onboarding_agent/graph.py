from typing import Dict, Any, Optional, List
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from app.agents.onboarding_agent.graphstate import GraphState
from app.agents.onboarding_agent.nodes.react_node import onaboarding_agent_node
from app.agents.onboarding_agent.conditionnal_edges.react_conditionnal import tools_condition
from app.utils.magic_print import magic_print
from app.agents.onboarding_agent.tools.tools_wrapper import tools_wrapper
from app.models.conversation import Conversation

REACT_GENERATOR = "coach"

def create_workflow():
    """Create the coaching workflow."""
    magic_print("Creating coaching workflow", "blue")
    workflow = StateGraph(GraphState)
    
    # Add coach node with async wrapper
    async def coach_wrapper(state: GraphState, config: RunnableConfig):
        return await onaboarding_agent_node(state, config)
    
    workflow.set_entry_point(REACT_GENERATOR)

    workflow.add_node(REACT_GENERATOR, action=coach_wrapper)
    workflow.add_node("tools", action=ToolNode(tools_wrapper))
    
    # Add conditional edges for tools
    workflow.add_conditional_edges(
        source=REACT_GENERATOR,
        path=tools_condition,
        path_map={
            "continue": "tools",
            "finish": END,
            "end": END
        }
    )
    
    # Add edge from tools back to coach
    workflow.add_edge("tools", REACT_GENERATOR)
    
    magic_print("Workflow created and compiled", "green")
    return workflow.compile()

def run_agent(
    message: str,
    conversation_id: Optional[str] = None
):
    """Run the coaching workflow with a message."""
    magic_print("Starting simplified agent", "blue")
    
    workflow = create_workflow()
    
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
    
    input = {
        "conversation_id": conversation.id,
        "messages": langchain_messages,
        "next_step": REACT_GENERATOR,
        "recursion_count": 0,
        "recursion_limit": 10,
        "timeout": 100000
    }
    
    magic_print("Invoking workflow", "blue")
    result = workflow.invoke(input)
    magic_print("Workflow completed", "green")

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
