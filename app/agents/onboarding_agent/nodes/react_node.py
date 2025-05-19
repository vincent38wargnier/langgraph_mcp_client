import json
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import SystemMessage, BaseMessage

from app.agents.onboarding_agent.graphstate import GraphState
from app.utils.magic_print import magic_print
from app.agents.onboarding_agent.tools.tools_wrapper import tools_wrapper
from app.settings.config import settings

load_dotenv()

# Configure the model with higher temperature for more creative responses
model = ChatOpenAI(
    model="gpt-4o",
    temperature=0.5
)

# Bind the tools to the model
model_with_tools = model.bind_tools(tools_wrapper, strict=True)

def onaboarding_agent_node(state: GraphState, config: RunnableConfig) -> GraphState:
    """
    1) Pass the entire conversation to the LLM.
    2) LLM can use tools or respond directly.
    3) Store the final response.
    """
    try:
        magic_print("\n" + "="*50, "blue")
        magic_print("🤖 AGENT - NEW DECISION CYCLE", "blue")
        magic_print("="*50 + "\n", "blue")
        
        # System instructions for the onboarding agent with information about MCP tools
        system_instructions = """
You are a helpful assistant that can engage in conversation with the user.
Respond to their questions and messages in a friendly, concise manner.

You have access to several powerful tools:
1. The echo_tool - A simple test tool that echoes back the message
2. Various MCP tools - These are external tools providing specialized functionality

When a task requires specialized capabilities, use the appropriate MCP tool rather than
trying to solve it yourself. These tools give you powerful capabilities to help the user.

IMPORTANT: Keep your responses brief and to the point. When using tools, provide context
about which tool you're using and why.
        """
        
        recursion_count = state.get("recursion_count", 0)
        recursion_limit = state.get("recursion_limit", 10)
        
        magic_print("🔄 WORKFLOW STATUS", "yellow")
        magic_print("-"*30, "yellow")
        magic_print(f"Iteration: {recursion_count}/{recursion_limit}", "yellow")
        magic_print("")
        
        # Build conversation: system instructions plus prior messages
        conversation = [SystemMessage(content=system_instructions)]
        conversation.extend(state["messages"])

        magic_print("\n" + "📝 "*20, "yellow")
        magic_print("        ╔══════════════════════════════╗", "yellow") 
        magic_print("        ║     CONVERSATION STATE       ║", "yellow")
        magic_print("        ║      Message History         ║", "yellow")
        magic_print("        ╚══════════════════════════════╝", "yellow")
        magic_print("📝 "*20 + "\n", "yellow")
        
        for idx, msg in enumerate(state["messages"], 1):
            magic_print(f"Message #{idx} ({msg.type}):", "yellow")
            magic_print("-"*30, "yellow")
            magic_print(msg, "yellow")
            magic_print("")
            
        magic_print("📝 "*20 + "\n", "yellow")

        magic_print("💭 LLM DECISION PHASE", "green")
        magic_print("-"*30, "green")
        magic_print("Requesting decision from LLM...", "green")
        
        # Invoke the model with tools
        response_msg = model_with_tools.invoke(conversation, config)
        
        # Log tool usage if present
        if hasattr(response_msg, 'additional_kwargs') and response_msg.additional_kwargs.get('tool_calls'):
            tool_calls = response_msg.additional_kwargs['tool_calls']
            magic_print("\n🛠️ TOOL CALLS DETECTED", "magenta")
            for tool in tool_calls:
                magic_print(f"Tool Name: {tool['function']['name']}", "cyan")
                try:
                    arguments = json.loads(tool['function'].get('arguments', '{}'))
                    magic_print(f"Arguments: {json.dumps(arguments, indent=2)}", "cyan")
                except:
                    magic_print(f"Raw Arguments: {tool['function'].get('arguments', '{}')}", "cyan")
        
        # Update recursion count
        state["recursion_count"] = recursion_count + 1
        
        # Add model response to conversation
        state["messages"].append(response_msg)
        
        return state
    except Exception as e:
        magic_print(f"Error in agent node: {str(e)}", "red")
        raise e