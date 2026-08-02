from agent.orchestrator import Agent
from agent.llm import LLMClient
from agent.executor import Executor
from agent.planner import Planner
from agent.verifier import Verifier
from agent.memory import WorkingMemory
from agent.telemetry import TrajectoryLogger

from tools.registry import ToolRegistry
from tools.filesystem import FileSystemTools
from tools.shell import ShellTool


workspace = "./workspace"

registry = ToolRegistry()

fs = FileSystemTools(workspace)
shell = ShellTool(workspace)

registry.register("write_file", fs.write_file)
registry.register("read_file", fs.read_file)
registry.register("run_shell", shell.run)

verifier = Verifier()

agent = Agent(
    llm=LLMClient(),
    planner=Planner(),
    executor=Executor(registry, verifier=verifier),
    verifier=verifier,
    memory=WorkingMemory(),
    telemetry=TrajectoryLogger(),
)


if __name__ == "__main__":
    EXIT_COMMANDS = {"exit", "quit", "q"}

    while True:
        try:
            task = input("Task: ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not task:
            continue

        if task.lower() in EXIT_COMMANDS:
            break

        result = agent.run(task)