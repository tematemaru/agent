import json
from pydantic import ValidationError
from ollama import chat
import re

from rich.console import Console

from .models import AgentResponse, AgentState

console = Console()

SYSTEM_PROMPT = """
You are an agent.

OUTPUT RULES (STRICT):
Return ONLY valid JSON.

Schema:
{
  "reasoning": "string",
  "state": "string"
}
If state == FINAL:
YOU MUST include "final_answer" field.
YOU ARE NOT ALLOWED TO WRITE ANYTHING EXCEPT JSON.
ABSOLUTELY NO TEXT OUTSIDE JSON.
NO CODE.
NO EXPLANATIONS.
DO NOT prefix with AgentState.
DO NOT use dots.

You have access to tools:

FileSystemTools:
- read_file(path)
- write_file(path, content)

ShellTool:
- run_shell(command: list[str])

To use a tool:
Return JSON:
{
  "state": "ACT",
  "tool_call": {
    "tool": "...",
    "args": {...}
  }
}

You MUST ALWAYS include:

- reasoning (mandatory)
- state
- tool_call (if ACT)

Even when calling tools, reasoning is required.
"""

class LLMClient:
    def __init__(self, model: str = "qwen3:4b"):
        self.model = model

    def extract_json(self, text: str) -> str:
        start = text.find("{")
        end = text.rfind("}")

        if start == -1 or end == -1:
            raise ValueError("No JSON found")

        return text[start:end + 1]


    def parse(self, content: str):
        clean = self.extract_json(content)
        data = json.loads(clean)
        return AgentResponse.model_validate(data)

    def invoke(self, messages, retries: int = 3) -> AgentResponse:
        last_error = None

        for _ in range(retries):
          with console.status("[bold green]LLM thinking..."):
            response = chat(
                model=self.model,
                messages=[{"role": "system", "content": SYSTEM_PROMPT}] + messages,
            )
            content = response.message.content


            try:
                return self.parse(content)

            except (ValueError, json.JSONDecodeError, ValidationError) as e:
                last_error = e
                messages.append({
                    "role": "user",
                    "content": "Your output was invalid. Output ONLY JSON."
                })

        raise RuntimeError(f"LLM parsing failed: {last_error}")