from typing import Dict, Callable


class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, Callable] = {}

    def register(self, name: str, fn: Callable):
        self.tools[name] = fn

    def execute(self, name: str, **kwargs):
        if name not in self.tools:
            raise ValueError(f"Unknown tool: {name}")

        return self.tools[name](**kwargs)