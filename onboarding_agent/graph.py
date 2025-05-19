from typing import Dict, Any, Optional, List
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
import json
import os
import uuid
from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from app.agents.onboarding_agent.graphstate import GraphState
from app.agents.onboarding_agent.nodes.react_node import onaboarding_agent_node
from app.agents.onboarding_agent.conditionnal_edges.react_conditionnal import tools_condition
from app.utils.magic_print import magic_print
from app.agents.onboarding_agent.tools.tools_wrapper import tools_wrapper

REACT_GENERATOR = "coach"
CONVERSATIONS_DIR = "conversations"  # Directory to store conversations

# Ensure conversations directory exists
os.makedirs(CONVERSATIONS_DIR, exist_ok=True)

class LocalConversation:
    def __init__(self, id=None):
        self.id = id or str(uuid.uuid4())
        self.messages = []
        self.is_active = True
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
        self.file_path = os.path.join(CONVERSATIONS_DIR, f"{self.id}.json")
        
        # Create file if it doesn't exist
        if not os.path.exists(self.file_path):
            self.save()
        else:
            self.load()
    
    def load(self):
        """Load conversation from file"""
        try:
            with open(self.file_path, 'r') as f:
                data = json.load(f)
                self.messages = data.get('messages', [])
                self.is_active = data.get('is_active', True)
                self.created_at = data.get('created_at', self.created_at)
                self.updated_at = data.get('updated_at', self.updated_at)
        except Exception as e:
            magic_print(f"Error loading conversation: {str(e)}", "red")
    
    def save(self):
        """Save conversation to file"""
        self.updated_at = datetime.now().isoformat()
        data = {
            'id': self.id,
            'messages': self.messages,
            'is_active': self.is_active,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
        try:
            with open(self.file_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            magic_print(f"Error saving conversation: {str(e)}", "red")
    
    def add_message(self, role, content, task_id=None):
        """Add a message to the conversation"""
        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        }
        if task_id:
            message['task_id'] = task_id
        
        self.messages.append(message)
        self.save()
        return self
    
    @classmethod
    def get_or_create(cls, conversation_id=None):
        """Get existing conversation or create new one"""
        if conversation_id:
            file_path = os.path.join(CONVERSATIONS_DIR, f"{conversation_id}.json")
            if os.path.exists(file_path):
                return cls(conversation_id)
        
        return cls()

async def create_workflow():
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

async def run_agent(
    message: str,
    conversation_id: Optional[str] = None
):
    """Run the coaching workflow with a message."""
    magic_print("Starting simplified agent", "blue")
    
    workflow = await create_workflow()
    
    # Get existing conversation or create new one
    magic_print(f"🔍 Conversation ID: {conversation_id}", "blue")
    conversation = LocalConversation.get_or_create(conversation_id)
    
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
    result = await workflow.ainvoke(input)
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
