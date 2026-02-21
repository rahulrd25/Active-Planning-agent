import json
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from dotenv import load_dotenv


from models.state import AgentState
from models.plan import Plan, PlanVersion
from models.intent import IntentResult, IntentType
from agent.prompts import (
    SYSTEM_PROMPT,
    INTENT_CLASSIFIER_PROMPT,
    CLARIFICATION_PROMPT,
    PLAN_CREATOR_PROMPT,
    PLAN_EDITOR_PROMPT,
    SUMMARIZER_PROMPT
)
from agent.tools import ALL_TOOLS
from services.plan_manager import create_plan, snapshot_plan, diff_plans, update_plan_from_json
from services.context_manager import maybe_compress, count_tokens

load_dotenv()

def get_llm():
    return ChatGroq(model="llama-3.3-70b-versatile")

# NODE 1: CONTEXT MANAGER
# Runs every turn. Checks token count and compresses if needed.
def context_manager_node(state: AgentState) -> dict:
    # get current messages from state
    messages = state.get("messages", [])

    # if no messages yet, nothing to do
    if not messages:
        return {
            "token_count": 0,
            "plan_history": state.get("plan_history", []),
            "user_preferences": state.get("user_preferences", {}),
            "needs_clarification": state.get("needs_clarification", False)
        }

    # convert to dict format for token counting
    messages_as_dicts = [
        {"role": m.type, "content": m.content}
        for m in messages
    ]
    # check and compress if needed
    compressed_dicts, summary = maybe_compress(messages_as_dicts)

    # count tokens after potential compression
    token_count = count_tokens(compressed_dicts)

    # convert back to LangChain message format
    compressed_messages = []
    for m in compressed_dicts:
        if m["role"] == "human":
            compressed_messages.append(HumanMessage(content=m["content"]))
        elif m["role"] == "ai":
            compressed_messages.append(AIMessage(content=m["content"]))
        else:
            compressed_messages.append(SystemMessage(content=m["content"]))
    # return only what changed
    return {
    "messages": compressed_messages if summary else [],
    "token_count": token_count,
    "conversation_summary": summary or state.get("conversation_summary")
}

# NODE 2: INTENT CLASSIFIER
# Reads user message and classifies what they want to do

def intent_classifier_node(state: AgentState) -> dict:
    llm = get_llm()

    # get the last user message
    last_message = state["messages"][-1].content

    # ask LLM to classify intent
    response = llm.invoke([
        SystemMessage(content=INTENT_CLASSIFIER_PROMPT),
        HumanMessage(content=last_message)
    ])
    try:
        # clean response in case LLM adds extra text
        content = response.content.strip()

        # sometimes LLM wraps in ```json ... ```
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        parsed = json.loads(content)

        intent_value = parsed.get("intent")
        return {"last_intent": intent_value}

    except Exception as e:
        # if parsing fails default to chat
        print(f"Intent classification failed: {e}")
        return {"last_intent": "chat"}

# ROUTER FUNCTION
# Reads last_intent and returns which node to go to next
def route_intent(state: AgentState) -> str:
    intent = state.get("last_intent")

    if not intent:
        return "responder"
    
    # This handles both Enum objects and raw strings from JSON
    intent_str = intent.value if hasattr(intent, 'value') else str(intent)

    # 3. Route based on the string value
    if intent_str == IntentType.create_plan.value:
        return "plan_creator"
    elif intent_str == IntentType.edit_plan.value:
        return "plan_editor"
    elif intent_str == IntentType.clarify.value:
        return "clarification"
    elif intent_str == IntentType.summarize.value:
        return "summarizer"
    else:
        return "responder"

# NODE 3: CLARIFICATION
# Asks user followup questions when request is unclear
def clarification_node(state: AgentState) -> dict:
    llm = get_llm()

    response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        SystemMessage(content=CLARIFICATION_PROMPT),
        *state["messages"] 
    ])
    return {
    "messages": [AIMessage(content=response.content)],
    "needs_clarification": True
}

# NODE 4: PLAN CREATOR
# Creates a new plan from conversation context
def plan_creator_node(state: AgentState) -> dict:
    llm = get_llm()

    response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        SystemMessage(content=PLAN_CREATOR_PROMPT),
        *state["messages"]
    ])
    try:
        # clean response in case LLM adds extra text or markdown
        content = response.content.strip()
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        content = content.strip()

        plan_json = json.loads(content)
        plan = create_plan(
            title=plan_json["title"],
            steps_data=plan_json["steps"]
        )

        # take initial snapshot for version history
        version = snapshot_plan(plan, "Initial plan created")

        # format readable response for user
        steps_text = "\n".join(
            f"{i+1}. {s.title}" for i, s in enumerate(plan.steps)
        )
        readable_response = f"Here is your plan: **{plan.title}**\n\n{steps_text}"

        return {
            "messages": [AIMessage(content=readable_response)],
            "current_plan": plan,
            "plan_history": [version],
            "needs_clarification": False
            }

    except Exception as e:
        new_messages = [
            AIMessage(content="I had trouble creating the plan. Could you provide more details?")
    ]
    return {
        "messages": new_messages,
        "needs_clarification": True
    }

# NODE 5: PLAN EDITOR
# Edits existing plan based on user feedback
def plan_editor_node(state: AgentState) -> dict:
    llm = get_llm()

    current_plan = state["current_plan"]
    old_snapshot = snapshot_plan(current_plan, "before edit")

    plan_context = f"Current plan: {current_plan.model_dump_json()}"

    response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        SystemMessage(content=PLAN_EDITOR_PROMPT),
        SystemMessage(content=plan_context),
        *state["messages"]
    ])
    try:
        content = response.content.strip()
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        content = content.strip()

        updated_plan_json = json.loads(content)
        updated_plan = update_plan_from_json(current_plan, updated_plan_json)
        updated_plan.version = current_plan.version + 1


        diff = diff_plans(old_snapshot.plan, updated_plan)
        new_version = snapshot_plan(updated_plan, diff.change_summary)
        updated_history = list(state.get("plan_history", [])) + [new_version]

        steps_text = "\n".join(
            f"{i+1}. {s.title}" for i, s in enumerate(updated_plan.steps)
        )
        readable_response = (
            f"I've updated your plan.\n\n"
            f"**Changes:** {diff.change_summary}\n\n"
            f"**Updated Plan: {updated_plan.title}**\n{steps_text}"
        )

        return {
    "messages": [AIMessage(content=readable_response)],
    "current_plan": updated_plan,
    "plan_history": updated_history
}

    except Exception as e:
        new_messages = list(state["messages"]) + [
            AIMessage(content="I had trouble editing the plan. Could you clarify what you'd like to change?")
        ]
        return {"messages": new_messages}
    
# NODE 6: SUMMARIZER
# Summarizes plan or conversation on demand
def summarizer_node(state: AgentState) -> dict:
    llm = get_llm()

    # build context — include plan if it exists
    context_parts = []

    if state.get("current_plan"):
        context_parts.append(
            f"Current plan: {state['current_plan'].model_dump_json()}"
        )

    if state.get("conversation_summary"):
        context_parts.append(
            f"Conversation summary so far: {state['conversation_summary']}"
        )
    context = "\n".join(context_parts)

    response = llm.invoke([
        SystemMessage(content=SUMMARIZER_PROMPT),
        SystemMessage(content=context),
        *state["messages"]
    ])

    return {"messages": [AIMessage(content=response.content)]}

# NODE 7: RESPONDER
# Final node — handles general chat and formats final response
def responder_node(state: AgentState) -> dict:
    llm = get_llm()

    response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        *state["messages"]
    ])

    return {"messages": [AIMessage(content=response.content)]}
