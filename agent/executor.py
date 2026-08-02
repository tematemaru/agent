from .models import ToolResult


class Executor:
    def __init__(self, registry, verifier=None):
        self.registry = registry
        self.verifier = verifier

    def run_tool(self, tool_name, args):
        try:
            result = self.registry.execute(tool_name, **args)
            success = self._verify(tool_name, args, result)

            return ToolResult(
                tool=tool_name,
                success=success,
                output=str(result),
            )

        except Exception as e:
            return ToolResult(
                tool=tool_name,
                success=False,
                output=str(e),
            )

    def _verify(self, tool_name, args, result) -> bool:
        if not self.verifier:
            return True

        if tool_name == "write_file":
            actual = self.registry.execute("read_file", path=args["path"])
            return self.verifier.verify_write(actual, args.get("content", ""))

        if tool_name == "run_shell":
            return self.verifier.verify_shell(result)

        return True