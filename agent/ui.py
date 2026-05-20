from rich.console import Console
from rich.panel import Panel


class AgentUI:
    def __init__(self):
        self.console = Console()

    def step(self, step: int, max_steps: int):
        self.console.rule(
            f"[bold cyan]STEP {step}/{max_steps}"
        )

    def state(self, state: str):
        self.console.print(
            f"[yellow]STATE:[/yellow] {state}"
        )

    def tool_call(self, tool: str, args: dict):
        self.console.print(
            Panel.fit(
                f"[bold green]{tool}[/bold green]\n{args}",
                title="TOOL CALL",
            )
        )

    def tool_result(self, success: bool, output: str):
        color = "green" if success else "red"

        self.console.print(
            Panel(
                output[:1000],
                title=f"TOOL RESULT ({success})",
                border_style=color,
            )
        )

    def final(self, text: str):
        self.console.print(
            Panel(
                text,
                title="[bold green]FINAL ANSWER",
            )
        )

    def error(self, text: str):
        self.console.print(
            f"[bold red]ERROR:[/bold red] {text}"
        )