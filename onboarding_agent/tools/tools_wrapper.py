from typing import Dict, Any, Annotated
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

@tool
async def echo_tool(
    message: str,
    state: Annotated[dict, InjectedState]
) -> Dict[str, Any]:
    """A simple echo tool that returns the message passed to it.
    This is useful for testing the agent's ability to use tools.
    
    Args:
        message: The message to echo back
        
    Returns:
        Dict[str, Any]: A dictionary containing the echoed message
    """
    return {
        "success": True,
        "message": f"Echo: {message}"
    }

# Define the tools wrapper
tools_wrapper = [
    echo_tool
]
