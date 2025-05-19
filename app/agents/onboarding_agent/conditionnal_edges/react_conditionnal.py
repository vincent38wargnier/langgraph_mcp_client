from ..graphstate import GraphState
from ....utils.magic_print import magic_print
import json

def tools_condition(state: GraphState):
    """Determine the next step based on the presence of tool calls."""
    messages = state["messages"]
    last_message = messages[-1]
    recursion_count = state["recursion_count"]
    recursion_limit = state["recursion_limit"]

    magic_print("\n" + "="*30, "blue")
    magic_print("🔄 WORKFLOW TRANSITION", "blue")
    magic_print("="*30, "blue")

    # Check for tool_calls in additional_kwargs
    tool_calls = None
    if hasattr(last_message, 'additional_kwargs'):
        tool_calls = last_message.additional_kwargs.get('tool_calls', None)
        if tool_calls:
            magic_print("📋 TOOLS REQUESTED", "cyan")
            for idx, tool in enumerate(tool_calls, 1):
                magic_print(f"Tool #{idx}: {tool['function']['name']}", "green")
                try:
                    args = json.loads(tool['function'].get('arguments', '{}'))
                    for arg_name, arg_value in args.items():
                        if isinstance(arg_value, str) and len(arg_value) > 50:
                            arg_value_display = arg_value[:47] + "..."
                        else:
                            arg_value_display = str(arg_value)
                        magic_print(f"  • {arg_name}: {arg_value_display}", "green")
                except json.JSONDecodeError:
                    magic_print(f"  • Raw arguments: {tool['function'].get('arguments', '{}')}", "green")
        else:
            magic_print("❌ NO TOOL CALLED", "red")

    # Decision making
    magic_print("🔀 TRANSITION DECISION", "yellow")

    # Check recursion limit
    if recursion_count >= recursion_limit:
        magic_print(f"⚠️ Recursion limit reached ({recursion_count}/{recursion_limit})", "red")
        return "finish"

    # Check for MCP tool responses
    if hasattr(last_message, 'content') and last_message.content:
        try:
            # See if we can detect a tool result in the message content
            if "tool result:" in last_message.content.lower() or "tool response:" in last_message.content.lower():
                magic_print("🔧 MCP Tool Response Detected", "cyan")
                content_snippet = last_message.content[:100] + "..." if len(last_message.content) > 100 else last_message.content
                magic_print(f"Response: {content_snippet}", "cyan")
        except Exception as e:
            magic_print(f"Error parsing message content: {str(e)}", "red")

    # If tool calls exist, proceed to tools
    if tool_calls:
        magic_print("• Tools requested - Proceeding to tools execution", "yellow")
        return "continue"
    else:
        magic_print("• No tools requested - Completing workflow", "yellow")
        magic_print(f"• Final iteration: {recursion_count}/{recursion_limit}", "yellow")
        return "finish"
