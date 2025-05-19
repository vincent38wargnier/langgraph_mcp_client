from typing import TypedDict, List, Dict, Optional, Annotated, Sequence, NotRequired
from datetime import datetime
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class GraphState(TypedDict, total=False):
    conversation_id: str
    messages: Annotated[Sequence[BaseMessage], add_messages]
    next_step: str  # Next step in the workflow
    recursion_count: NotRequired[int]  # Making this field optional with default in code
    recursion_limit: NotRequired[int]  # Making this field optional with default in code
    timeout: NotRequired[int]  # Making this field optional with default in code