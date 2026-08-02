from .models import AgentState


class Planner:
    def build_prompt(self, runtime_state, memory=None):
        scratchpad = "\n".join(runtime_state.scratchpad) or "(empty)"
        recent_tool_outputs = memory.render() if memory else "(empty)"

        return f"""
Goal:
{runtime_state.goal}

Current step:
{runtime_state.current_step}

Scratchpad (reasoning history):
{scratchpad}

Recent tool outputs:
{recent_tool_outputs}

You must decide:
- next tool call
- verification
- or final answer

Allowed states:
- {AgentState.ACT}
- {AgentState.VERIFY}
- {AgentState.FINAL}
"""