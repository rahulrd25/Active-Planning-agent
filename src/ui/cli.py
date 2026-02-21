import uuid
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from langchain_core.messages import HumanMessage

from agent.graph import planning_graph
from ui.renderer import render_plan, render_diff, render_agent_message, render_error

console = Console()

# define exit words at module level — not inside loop
EXIT_WORDS = {"/quit", "/exit", "quit", "exit", "bye", "goodbye", "stop", "q"}


def show_help():
    """Display available commands."""
    console.print(Panel(
        "[cyan]/summary[/]  - Get executive summary of conversation and plan\n"
        "[cyan]/history[/]  - Show plan version history\n"
        "[cyan]/help[/]     - Show this help message\n"
        "[cyan]quit/bye[/]  - Exit the agent",
        title="[bold]Available Commands[/]",
        border_style="dim"
    ))


def start():
    """Main CLI loop."""

    # generate unique thread id for this session
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    # define commands dict here so it has access to config
    COMMANDS = {
        "/history": lambda: handle_history(config),
        "/help": lambda: show_help(),
    }

    console.print(Panel(
        "[bold green]Planning Agent[/]\n\n"
        "I can help you:\n"
        "  • Create structured plans from your ideas\n"
        "  • Refine and edit plans through conversation\n"
        "  • Track changes and version history\n\n"
        "[dim]Type /help for commands  •  Type stop or bye to exit[/]",
        border_style="green"
    ))

    while True:
        try:
            # get user input
            user_input = Prompt.ask("\n[bold cyan]You[/]")
            cleaned = user_input.lower().strip()

            # empty input — skip
            if not cleaned:
                continue

            # exit check
            if cleaned in EXIT_WORDS:
                console.print("[dim]Goodbye! Your plan has been saved.[/]")
                break

            # command check
            if cleaned in COMMANDS:
                COMMANDS[cleaned]()
                continue

            # summary shortcut — convert to natural language
            if cleaned == "/summary":
                user_input = "Can you give me an executive summary of our conversation and the current plan?"

            # send to agent
            with console.status("[dim]Thinking...[/]"):
                result = planning_graph.invoke(
                    {"messages": [HumanMessage(content=user_input)]},
                    config=config
                )

            # get last agent message
            last_message = result["messages"][-1].content
            render_agent_message(last_message)

            # show diff if plan was edited
            plan_history = result.get("plan_history", [])
            if len(plan_history) > 1:
                latest = plan_history[-1]
                previous = plan_history[-2]
                from services.plan_manager import diff_plans
                diff = diff_plans(previous.plan, latest.plan)
                if diff.added or diff.removed or diff.modified:
                    render_diff(diff)

        except KeyboardInterrupt:
            console.print("\n[dim]Goodbye![/]")
            break
        except Exception as e:
            render_error(str(e))


def handle_history(config: dict):
    """Show plan version history."""
    result = planning_graph.get_state(config)
    plan_history = result.values.get("plan_history", [])

    if not plan_history:
        console.print("[dim]No plan history yet.[/]")
        return

    console.print(f"\n[bold]Plan History ({len(plan_history)} versions)[/]")
    for version in plan_history:
        console.print(
            f"  [cyan]v{version.version_number}[/] - "
            f"{version.timestamp.strftime('%H:%M:%S')} - "
            f"[dim]{version.change_summary}[/]"
        )