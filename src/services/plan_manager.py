from datetime import datetime
from models.plan import Plan, PlanStep, PlanVersion, DiffResult

def create_plan(title: str, steps_data: list[dict]) -> Plan:
    steps = []
    for i, step in enumerate(steps_data):
        steps.append(PlanStep(
            order= i+1,
            title= step["title"],
            description= step.get("decription", "")
        ))
    return Plan(title=title, steps=steps)

def add_step(Plan: Plan, title: str, description: str = "") -> Plan:
    new_step = PlanStep(
        order=len(Plan.steps) + 1,
        title= title,
        description= description
    )
    Plan.steps.append(new_step)
    Plan.updated_at = datetime.now()
    return Plan

def edit_step(plan: Plan, step_id: str, title: str = None, description: str = None) -> Plan:
    for step in plan.steps:
        if step.id == step_id:
            if title:
                step.title = title
            if description:
                step.description = description
    plan.updated_at = datetime.now()
    return plan


#Update plan from LLM JSON while preserving step IDs where possible.
def update_plan_from_json(existing_plan: Plan, updated_json: dict) -> Plan:
    # build lookup of existing steps by title
    existing_by_title = {s.title.lower(): s for s in existing_plan.steps}

    new_steps = []
    for i, step_data in enumerate(updated_json["steps"]):
        title_key = step_data["title"].lower()

        if title_key in existing_by_title:
            # step exists — reuse same ID
            existing_step = existing_by_title[title_key]
            existing_step.order = i + 1
            existing_step.description = step_data.get("description", existing_step.description)
            new_steps.append(existing_step)
        else:
            # genuinely new step — create with new ID
            new_steps.append(PlanStep(
                order=i + 1,
                title=step_data["title"],
                description=step_data.get("description", "")
            ))

    existing_plan.steps = new_steps
    existing_plan.updated_at = datetime.now()
    return existing_plan


def remove_step(plan: Plan, step_id: str) -> Plan:
    plan.steps = [s for s in plan.steps if s.id != step_id]
    plan = reorder_steps(plan)
    plan.updated_at = datetime.now()
    return plan

def reorder_steps(plan: Plan) -> Plan:
    for i, step in enumerate(plan.steps):
        step.order = i +1
    return plan
    
def diff_plans(old_plan: Plan, new_plan: Plan) -> DiffResult:
    old_ids = {s.id: s for s in old_plan.steps}
    new_ids = {s.id: s for s in new_plan.steps}

    added = [s for id, s in new_ids.items() if id not in old_ids]
    removed = [s for id, s in old_ids.items() if id not in new_ids]
    modified = [
        s for id, s in new_ids.items()
        if id in old_ids and (
            s.title != old_ids[id].title or
            s.description != old_ids[id].description
        )
    ]

    summary_parts = []
    if added:
        summary_parts.append(f"Added: {', '.join(s.title for s in added)}")
    if removed:
        summary_parts.append(f"Removed: {', '.join(s.title for s in removed)}")
    if modified:
        summary_parts.append(f"Modified: {', '.join(s.title for s in modified)}")

    return DiffResult(
        added=added,
        removed=removed,
        modified=modified,
        change_summary=" | ".join(summary_parts) or "No changes"
    )


def snapshot_plan(plan: Plan, change_summary: str) -> PlanVersion:
    return PlanVersion(
        version_number=plan.version,
        plan=plan.model_copy(deep=True),
        change_summary=change_summary
    )
