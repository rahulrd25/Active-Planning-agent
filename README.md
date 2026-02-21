# Planning Agent

A conversational AI agent that helps users create, refine, and manage structured plans through natural dialogue. Built with LangGraph, Groq (Llama 3.3), and Rich CLI.

---

## Demo
```
You: I want to build a website
Agent: I'd be happy to help! Could you tell me:
       - What type of website? (e-commerce, blog, portfolio)
       - What is the main purpose?
       - Do you have a timeline in mind?

You: It's an e-commerce site for selling books
Agent: Here is your plan: E-commerce Bookstore Website Plan
       1. Define Project Scope
       2. Choose an E-commerce Platform
       ...

You: Add a step for inventory management
Agent: I've updated your plan.
       Changes: Added: Implement Inventory Management System
```

---

## Features

- **Multi-turn conversations** — remembers full context across 10+ turns
- **Clarifying questions** — asks focused questions when requests are ambiguous
- **Plan creation** — generates structured, actionable plans from natural language
- **Plan editing** — add, remove, or modify steps through conversation
- **Version history** — tracks every change made to the plan
- **Diff visibility** — shows exactly what changed after every edit
- **Context compression** — automatically compresses old messages when approaching 8K token limit
- **Summarization** — summarizes plan or full conversation on demand

---

## Tech Stack

| Tool | Purpose |
|---|---|
| LangGraph | Agent state graph and multi-turn memory |
| Groq (Llama 3.3-70b) | LLM for plan generation and intent classification |
| LangChain | LLM tooling and message types |
| Pydantic | Structured data models and validation |
| Rich | CLI interface with formatted output |
| tiktoken | Token counting for context compression |
| UV | Dependency management |

---

## Project Structure
```
Active-planning-agent/
├── src/
│   ├── agent/
│   │   ├── graph.py       # LangGraph state machine — wires all nodes
│   │   ├── nodes.py       # Node functions — each handles one responsibility
│   │   ├── prompts.py     # All LLM prompts in one place
│   │   └── tools.py       # LangChain tools exposed to the LLM
│   ├── models/
│   │   ├── intent.py      # IntentType enum, IntentResult
│   │   ├── plan.py        # Plan, PlanStep, PlanVersion, DiffResult
│   │   └── state.py       # AgentState — shared state across all nodes
│   ├── services/
│   │   ├── context_manager.py  # Token counting and compression logic
│   │   └── plan_manager.py     # Plan CRUD, diffing, versioning
│   ├── ui/
│   │   ├── cli.py         # Main CLI loop
│   │   └── renderer.py    # Rich-based plan and diff rendering
│   └── main.py
├── tests/
│   ├── unit/
│   │   ├── test_plan_manager.py
│   │   └── test_context_manager.py
│   └── integration/
│       └── test_agent.py
├── .env
├── pyproject.toml
└── README.md
```

---

## Setup & Run

### Prerequisites
- Python 3.11+
- UV package manager
- Groq API key (free at console.groq.com)

### Installation
```bash
# clone the repo
git clone https://github.com/rahulrd25/Active-Planning-agent
cd Active-planning-agent

# install dependencies
uv sync

# set up environment
cp .env.example .env
# add your Groq API key to .env
```

### Environment Variables

Create a `.env` file in the project root:
```
GROQ_API_KEY=your_groq_api_key_here
```

### Run the Agent
```bash
uv run python src/main.py
```

### Run Tests
```bash
# all tests
uv run pytest tests/ -v

# unit tests only
uv run pytest tests/unit/ -v

# integration tests only
uv run pytest tests/integration/ -v
```

---

## CLI Commands

| Command | Description |
|---|---|
| `/help` | Show available commands |
| `/summary` | Get executive summary of conversation and plan |
| `/history` | Show plan version history with timestamps |
| `quit` / `bye` / `stop` | Exit the agent |

---

## Design Decisions

### LangGraph over plain LangChain
LangGraph provides a proper stateful graph with conditional routing. This lets the agent dynamically decide what to do each turn rather than following a fixed chain. The `MemorySaver` checkpointer gives multi-turn memory for free using `thread_id`.

### Intent classification as a separate node
Every turn starts with intent classification before any action is taken. This keeps the agent responsive to mid-conversation pivots, if a user switches from creating to editing, the agent handles it cleanly without getting confused.

### Services layer with no LLM dependency
`plan_manager.py` and `context_manager.py` are pure Python with no LLM calls. This makes them fully testable in isolation and keeps business logic separate from AI logic. Diffing plans, tracking versions, and counting tokens are deterministic operations that shouldn't depend on an LLM.

### Plan JSON survives context compression
When old messages are compressed into a summary, the current plan JSON is always re-injected into context as a system message. The plan is the ground truth of all decisions made, losing it would break the agent's continuity.

### Structured outputs via Pydantic
Every LLM call that produces data uses a defined Pydantic model. This catches malformed responses early and gives the rest of the codebase reliable, typed data to work with.

### Diff by ID not by position
Plan steps have UUIDs that persist across edits. When diffing two plan versions, we compare by ID. This correctly identifies genuinely new, removed, or modified steps even when the order changes.

### Prompts in one file
All LLM prompts live in `prompts.py`. When the agent behaves incorrectly, the first debugging step is always prompt tuning, having them in one place makes this fast.

---

## Dependencies
```
langgraph          — agent state graph and memory
langchain-groq     — Groq LLM integration  
langchain-core     — base LangChain types and tools
groq               — Groq API client
pydantic           — data validation and structured models
tiktoken           — token counting for context compression
rich               — CLI formatting and display
python-dotenv      — environment variable loading
pytest             — test framework
pytest-asyncio     — async test support
```

---

## Scoring Checklist

| Requirement | Implementation |
|---|---|
| Clarification requests | `clarification_node` — asks max 3 focused questions |
| Plan creation | `plan_creator_node` — returns structured JSON plan |
| Plan editing | `plan_editor_node` — preserves step IDs, tracks versions |
| Context management | `context_manager_node` — compresses at 6K, hard limit 8K |
| Summarization | `summarizer_node` — plan, changes, or full conversation |
| CLI UI | Rich-based with panels, diffs, version history |
| Agent with tools | Tools defined in `tools.py`, LLM decides when to call |
| Structured output | Pydantic models for all LLM responses |
| Tests | Unit + integration tests with pytest |