from typing import Annotated, List, Optional, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field


class AgentState(TypedDict):
    """Fields persisted by LangGraph for a single conversation thread."""
    messages: Annotated[List[BaseMessage], add_messages]
    summary: str
    answer: str
    is_conversational: bool
    sources_used: List[str]
    cache_hit: bool


class UserRequest(BaseModel):
    """Input accepted by the service layer, independent of any particular UI."""
    query: str = Field(..., min_length=2, max_length=1500, description="User query (must be at least 2 characters)")
    session_id: str = Field(default="default_guest", min_length=3, description="Thread ID for memory tracking")
    user_id: Optional[str] = Field(
        default=None,
        min_length=3,
        description="Persistent student identity for long-term memory; defaults to session_id when omitted",
    )


class RetrieveInternalDocsInput(BaseModel):
    """Validated input contract for the local-document retrieval tool."""
    query: str = Field(..., min_length=3, description="Search keywords")


class FinalAnswerSchema(BaseModel):
    """Structured payload the model supplies when it completes an answer."""
    answer: str = Field(..., description="The final answer to give the student.")
    sources_used: List[str] = Field(
        default_factory=list,
        description="Sources (tool names, or document names/pages) actually used to build the answer.",
    )
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="How confident the agent is in this answer, from 0.0 to 1.0.")
"""Typed graph state and validated shapes shared at application boundaries."""
