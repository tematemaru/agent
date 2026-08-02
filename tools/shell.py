import os
import subprocess


ALLOWED_COMMANDS = {
    "python",
    "pytest",
    "ls",
    "cat",
}

DISALLOWED_FLAGS = {
    "-c",
    "-m",
}


class ShellTool:
    def __init__(self, workspace: str):
        self.workspace = os.path.realpath(workspace)

    def _check_args(self, command: list[str]):
        for arg in command[1:]:
            if arg in DISALLOWED_FLAGS:
                raise PermissionError(
                    f"Argument not allowed: {arg}"
                )

            if arg.startswith("-"):
                continue

            full_path = os.path.realpath(
                os.path.join(self.workspace, arg)
            )

            if os.path.commonpath([full_path, self.workspace]) != self.workspace:
                raise PermissionError(
                    f"Argument escapes workspace: {arg}"
                )

    def run(self, command: list[str]):
        if not command or command[0] not in ALLOWED_COMMANDS:
            raise PermissionError(
                f"Command not allowed: {command[0] if command else command}"
            )

        self._check_args(command)

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