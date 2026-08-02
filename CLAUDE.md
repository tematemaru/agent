# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

A local, tool-using LLM agent PoC built on Ollama (see README.md). The agent runs a single-loop
plan/act/verify/final cycle against a local model, calling sandboxed filesystem and shell tools.

## Setup & running

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Ollama must be running locally with the target model pulled:
ollama pull qwen3:4b

python main.py   # prompts for a task on stdin, then runs the agent loop
```

There is no test suite, lint config, or build step in this repo currently.

## Architecture

The agent is wired together in `main.py`: a `ToolRegistry` is populated with tool functions from
`tools/filesystem.py` and `tools/shell.py`, then injected into an `agent.orchestrator.Agent` along
with an `LLMClient`, `Planner`, `Executor`, `Verifier`, `WorkingMemory`, and `TrajectoryLogger`.

**Main loop (`agent/orchestrator.py`)** — `Agent.run(goal)` creates a `RuntimeState` (step counter,
scratchpad, tool results) and loops until `max_steps` (default 10):
1. `Planner.build_prompt(runtime)` renders the goal/step/scratchpad into a prompt.
2. `LLMClient.invoke(...)` sends it to Ollama and parses the reply into an `AgentResponse`.
3. If `state == FINAL`, returns `final_answer` immediately.
4. If the response includes a `tool_call`, `Executor.run_tool` dispatches it through the
   `ToolRegistry`, the result is appended to `runtime.tool_results` and `WorkingMemory`, and both
   the LLM response and tool result are appended to `trajectory.jsonl` via `TrajectoryLogger`.

**LLM output contract (`agent/models.py`, `agent/llm.py`)** — The model is forced into a strict
JSON-only protocol via `SYSTEM_PROMPT` in `llm.py`: every reply must be `AgentResponse` shaped
(`reasoning`, `state`, optional `tool_call`, optional `final_answer`), where `state` is one of the
`AgentState` enum values (`PLAN`, `ACT`, `VERIFY`, `RECOVER`, `FINAL`). `LLMClient.invoke` strips
any non-JSON text around the `{...}` payload, validates it with Pydantic, and retries (up to 3x)
with a corrective message if parsing/validation fails.

**Tools (`tools/`)** — `ToolRegistry` is a plain name→callable map (`register`/`execute`).
`FileSystemTools` (`read_file`/`write_file`) resolves all paths against a realpath'd `workspace`
root and rejects anything that escapes it (path-traversal guard). `ShellTool.run` only allows
commands whose argv[0] is in `ALLOWED_COMMANDS` (`python`, `pytest`, `ls`, `cat`) and executes with
`shell=False`, `cwd=workspace`, a 30s timeout. Both tools operate under `./workspace`, which is the
agent's sandboxed working directory (gitignored; contains a `docs/` subfolder used as sample
content for the agent to read/summarize).

**Verifier (`agent/verifier.py`)** — `verify_write`/`verify_shell` exist but are not currently
called from the orchestrator loop; the `VERIFY` state is defined in the protocol but not yet
enforced end-to-end.

**Telemetry** — every LLM response and tool result is appended as JSON lines to `trajectory.jsonl`
at the repo root (via `agent/telemetry.py`), timestamped in UTC. `agent/ui.py` renders the same
events to the console with `rich` (step banners, tool call/result panels, final answer panel).

**RAG / chroma_db** — `rag/` is currently an empty placeholder directory. `chroma_db/` holds a
local Chroma vector store (gitignored); `chromadb` is in `requirements.txt` but not yet wired into
`agent/` or `main.py`.

## Notes for changes

- Tool functions registered on `ToolRegistry` are called via `**kwargs` from the LLM's
  `tool_call.args`, so new tools must accept keyword arguments matching what the `SYSTEM_PROMPT` in
  `agent/llm.py` documents to the model — update that prompt whenever tool signatures change.
- New shell commands must be added to `ShellTool.ALLOWED_COMMANDS`; there is no other allowlist
  mechanism.
- `WorkingMemory` is a fixed-size deque (default 8 items) of raw tool outputs, rendered but not
  currently injected into the planner prompt — check `Planner.build_prompt` before assuming
  scratchpad/memory content reaches the model.
