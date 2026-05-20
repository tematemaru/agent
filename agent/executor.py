from .models import ToolResult

class Executor:
    def __init__(self, registry):
        self.registry = registry

    def run_tool(self, tool_name, args):
        try:
            result = self.registry.execute(tool_name, **args)

            return ToolResult(
                tool=tool_name,
                success=True,
                output=str(result),
            )

        except Exception as e:
            return ToolResult(
                tool=tool_name,
                success=False,
                output=str(e),
            )