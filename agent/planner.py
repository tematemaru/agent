from .models import AgentState


class Planner:
    def build_prompt(self, runtime_state):
        return f"""
Goal:
{runtime_state.goal}

Current step:
{runtime_state.current_step}

Scratchpad:
{runtime_state.scratchpad}

You must decide:
- next tool call
- verification
- or final answer

Allowed states:
- {AgentState.ACT}
- {AgentState.VERIFY}
- {AgentState.FINAL}
"""