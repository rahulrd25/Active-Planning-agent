from groq import Groq
from dotenv import load_dotenv
import json
import sys
sys.path.append("src")

from models.plan import Plan
from services.plan_manager import create_plan, add_step, remove_step, diff_plans, snapshot_plan



load_dotenv()

client = Groq()

response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {
            "role": "system",
            "content": """You are a planning assistant. When user describes a goal, create a step by step plan.
            
Always respond in this exact JSON format:
{
    "title": "plan title here",
    "steps": [
        {"title": "step title", "description": "step description"}
    ]
}

Return only JSON. No extra text."""
        },
        {
            "role": "user",
            "content": "I want to build an ecommerce website for selling books"
        }
    ]
)

raw = response.choices[0].message.content
parsed = json.loads(raw)

# feed into our actual model
plan = create_plan(
    title=parsed["title"],
    steps_data=parsed["steps"]
)

print(f"Plan ID: {plan.id}")
print(f"Title: {plan.title}")
print(f"Version: {plan.version}")
print(f"Created at: {plan.created_at}")
print(f"\nSteps:")
for step in plan.steps:
    print(f"  {step.order}. [{step.id}] {step.title}")


# snapshot before editing
old_snapshot = snapshot_plan(plan, "initial plan")

# add a new step
plan = add_step(plan, "Inventory Management", "Track stock levels and automate reordering")

# remove step 1
first_step_id = plan.steps[0].id
plan = remove_step(plan, first_step_id)

# diff
diff = diff_plans(old_snapshot.plan, plan)


print("\nDIFF RESULT:")
print(f"Added: {[s.title for s in diff.added]}")
print(f"Removed: {[s.title for s in diff.removed]}")
print(f"Summary: {diff.change_summary}")
