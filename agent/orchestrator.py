from rich.console import Console

from .ui import AgentUI
from .models import AgentState
from .state import RuntimeState


class Agent:
    def __init__(
        self,
        llm,
        planner,
        executor,
        verifier,
        memory,
        telemetry,
    ):
        self.llm = llm
        self.planner = planner
        self.executor = executor
        self.verifier = verifier
        self.memory = memory
        self.telemetry = telemetry
        self.console = Console()
        self.ui = AgentUI()

    def run(self, goal: str):
        runtime = RuntimeState(goal=goal)

        self.console.print("[bold cyan]Agent started[/bold cyan]"
)

        while not runtime.exhausted():
            self.ui.step(
              runtime.current_step,
              runtime.max_steps,
            )
            runtime.current_step += 1

            prompt = self.planner.build_prompt(runtime, self.memory)
            self.ui.state("Thinking...")
            response = self.llm.invoke(
                [
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ]
            )
            self.ui.state(response.state)

            if response.reasoning:
                runtime.scratchpad.append(
                    f"Step {runtime.current_step}: {response.reasoning}"
                )

            self.telemetry.log(
                {
                    "step": runtime.current_step,
                    "response": response.model_dump(),
                }
            )

            if response.state == AgentState.FINAL:
                self.ui.final(response.final_answer)
                return response.final_answer

            if response.tool_call:
                self.ui.tool_call(
                    response.tool_call.tool,
                    response.tool_call.args,
                )
                result = self.executor.run_tool(
                    response.tool_call.tool,
                    response.tool_call.args,
                )

                self.ui.tool_result(
                    result.success,
                    result.output,
                )

                runtime.tool_results.append(result)

                self.memory.add(result.output)

                self.telemetry.log(
                    {
                        "tool_result": result.model_dump(),
                    }
                )

        return "Max steps exceeded"