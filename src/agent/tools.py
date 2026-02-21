from langchain_core.tools import tool
from services.plan_manager import (
    create_plan,
    add_step,
    edit_step,
    remove_step,
    snapshot_plan,
    diff_plans
)
from models.plan import Plan
import json

@tool
def create_plan_tool(title: str, steps: list[dict]) -> str:
    """
    Use this tool when user wants to create a brand new plan.
    
    Args:
        title: the title of the plan
        steps: list of steps, each with 'title' and 'description'
    
    Returns:
        created plan as JSON string
    """
    # call our existing service function
    plan = create_plan(title=title, steps_data=steps)

    # return as JSON string so LLM can read it
    return plan.model_dump_json()

@tool
def add_step_tool(plan_json: str, title: str, description: str = "") -> str:
    """
    Use this tool when user wants to add a new step to existing plan.
    
    Args:
        plan_json: current plan as JSON string
        title: title of the new step to add
        description: description of the new step
    
    Returns:
        updated plan as JSON string
    """
    # convert JSON string back to Plan object
    plan = Plan.model_validate_json(plan_json)

    # call our service function
    updated_plan = add_step(plan=plan, title=title, description=description)

    return updated_plan.model_dump_json()

@tool
def edit_step_tool(plan_json: str, step_id: str, title: str = None, description: str = None) -> str:
    """
    Use this tool when user wants to edit or modify an existing step.
    
    Args:
        plan_json: current plan as JSON string
        step_id: the unique ID of the step to edit
        title: new title for the step (optional)
        description: new description for the step (optional)
    
    Returns:
        updated plan as JSON string
    """
    plan = Plan.model_validate_json(plan_json)
    updated_plan = edit_step(plan=plan, step_id=step_id, title=title, description=description)
    return updated_plan.model_dump_json()


@tool
def remove_step_tool(plan_json: str, step_id: str) -> str:
    """
    Use this tool when user wants to remove or delete a step from the plan.
    
    Args:
        plan_json: current plan as JSON string
        step_id: the unique ID of the step to remove
    
    Returns:
        updated plan as JSON string
    """
    plan = Plan.model_validate_json(plan_json)
    updated_plan = remove_step(plan=plan, step_id=step_id)
    return updated_plan.model_dump_json()


@tool
def get_diff_tool(old_plan_json: str, new_plan_json: str) -> str:
    """
    Use this tool to compare two versions of a plan and show what changed.
    
    Args:
        old_plan_json: previous version of plan as JSON string
        new_plan_json: updated version of plan as JSON string
    
    Returns:
        diff result showing added, removed, modified steps
    """
    old_plan = Plan.model_validate_json(old_plan_json)
    new_plan = Plan.model_validate_json(new_plan_json)
    diff = diff_plans(old_plan=old_plan, new_plan=new_plan)
    return diff.model_dump_json()

# passed all tools list to LLM so it knows what tools exist
ALL_TOOLS = [
    create_plan_tool,
    add_step_tool,
    edit_step_tool,
    remove_step_tool,
    get_diff_tool
]