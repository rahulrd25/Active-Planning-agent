import sys
sys.path.append("src")

import uuid
import pytest
from langchain_core.messages import HumanMessage
from agent.graph import planning_graph


@pytest.fixture
def config():
    """
    Generate a unique thread id for each test run.
    This ensures tests don't share state.
    """
    thread_id = str(uuid.uuid4())
    return {"configurable": {"thread_id": thread_id}}


def chat(user_input: str, config: dict):
    """
    Helper function to send a message and get result.
    """
    result = planning_graph.invoke(
        {"messages": [HumanMessage(content=user_input)]},
        config=config
    )
    return result


def test_clarification_on_vague_input(config):
    """Agent should ask questions when input is vague."""
    result = chat("I want to build something", config)
    last_message = result["messages"][-1].content

    # agent should ask questions not create a plan
    assert result.get("current_plan") is None
    assert "?" in last_message
    print(f"\nAgent response: {last_message}")


def test_plan_creation(config):
    """Agent should create a plan when given clear goal."""
    result = chat("I want to build an ecommerce website for selling books", config)

    assert result.get("current_plan") is not None
    assert len(result["current_plan"].steps) > 0
    print(f"\nPlan created: {result['current_plan'].title}")
    print(f"Steps: {len(result['current_plan'].steps)}")


def test_plan_editing(config):
    """Agent should edit plan when user requests a change."""
    # first create a plan
    chat("I want to build an ecommerce website for selling books", config)

    # then edit it
    result = chat("Add a step for inventory management", config)

    assert result.get("current_plan") is not None
    titles = [s.title.lower() for s in result["current_plan"].steps]
    assert any("inventory" in t for t in titles)
    print(f"\nUpdated steps: {titles}")


def test_multi_turn_memory(config):
    """Agent should remember context across multiple turns."""
    # turn 1
    chat("I want to build an ecommerce website for selling books", config)

    # turn 2
    chat("Add a step for inventory management", config)

    # turn 3
    result = chat("Remove the first step", config)

    # should still have a plan with history
    assert result.get("current_plan") is not None
    assert len(result.get("plan_history", [])) > 1
    print(f"\nPlan version: {result['current_plan'].version}")
    print(f"History entries: {len(result['plan_history'])}")


def test_summarization(config):
    """Agent should summarize plan when asked."""
    # create a plan first
    chat("I want to build an ecommerce website for selling books", config)

    # ask for summary
    result = chat("Can you summarize the plan?", config)
    last_message = result["messages"][-1].content

    assert len(last_message) > 0
    print(f"\nSummary: {last_message}")