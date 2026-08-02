from dataclasses import dataclass, field
from typing import List

from .models import ToolResult


@dataclass
class RuntimeState:
    goal: str
    current_step: int = 0
    max_steps: int = 10
    scratchpad: List[str] = field(default_factory=list)
    tool_results: List[ToolResult] = field(default_factory=list)

    def exhausted(self) -> bool:
        return self.current_step >= self.max_steps