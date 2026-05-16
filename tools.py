import os
import shlex
import subprocess


def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    return f"file written: {path}"


def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def list_files(path="."):
    files = os.listdir(path)
    return "empty" if not files else "\n".join(files)


def run_shell(command, cwd=None):
    args = shlex.split(command)

    result = subprocess.run(
        args,
        cwd=cwd,
        capture_output=True,
        text=True,
        shell=False,
        timeout=20
    )

    return (result.stdout + "\n" + result.stderr).strip()