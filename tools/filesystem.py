import os
from pathlib import Path


class FileSystemTools:
    def __init__(self, workspace: str):
        self.workspace = os.path.realpath(workspace)
        os.makedirs(self.workspace, exist_ok=True)

    def _safe_path(self, path: str) -> str:
        full_path = os.path.realpath(
            os.path.join(self.workspace, path)
        )

        if os.path.commonpath([full_path, self.workspace]) != self.workspace:
            raise PermissionError("Path traversal detected")

        return full_path

    def write_file(self, path: str, content: str):
        safe = self._safe_path(path)

        Path(safe).parent.mkdir(parents=True, exist_ok=True)

        with open(safe, "w", encoding="utf-8") as f:
            f.write(content)

        return f"Wrote {len(content)} chars"

    def read_file(self, path: str):
        safe = self._safe_path(path)

        with open(safe, "r", encoding="utf-8") as f:
            return f.read()