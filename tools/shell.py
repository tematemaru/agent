import subprocess


ALLOWED_COMMANDS = {
    "python",
    "pytest",
    "ls",
    "cat",
}


class ShellTool:
    def __init__(self, workspace: str):
        self.workspace = workspace

    def run(self, command: list[str]):
        if command[0] not in ALLOWED_COMMANDS:
            raise PermissionError(
                f"Command not allowed: {command[0]}"
            )

        result = subprocess.run(
            command,
            cwd=self.workspace,
            capture_output=True,
            text=True,
            timeout=30,
            shell=False,
        )

        return {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }