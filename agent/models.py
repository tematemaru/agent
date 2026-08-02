from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class AgentState(str, Enum):
    PLAN = "PLAN"
    ACT = "ACT"
    VERIFY = "VERIFY"
    RECOVER = "RECOVER"
    FINAL = "FINAL"


class ToolCall(BaseModel):
    tool: str
    args: Dict[str, Any] = Field(default_factory=dict)


class AgentResponse(BaseModel):
    reasoning: str | None = None
    state: AgentState
    tool_call: Optional[ToolCall] = None
    final_answer: Optional[str] = None


class ToolResult(BaseModel):
    tool: str
    success: bool
    output: str