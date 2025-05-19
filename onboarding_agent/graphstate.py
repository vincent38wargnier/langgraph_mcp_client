from typing import TypedDict, List, Dict, Optional, Annotated, Sequence
from datetime import datetime
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class GraphState(TypedDict):
    conversation_id: str
    messages: Annotated[Sequence[BaseMessage], add_messages]
    next_step: str  # Next step in the workflow
    recursion_count: int
    recursion_limit: int
    timeout: int