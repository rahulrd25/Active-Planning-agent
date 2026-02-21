from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from models.plan import Plan, DiffResult

console = Console()


def render_plan(plan: Plan):
    """Display plan in a nice formatted panel."""
    content = Text()

    for step in plan.steps:
        content.append(f"{step.order}. ", style="bold cyan")
        content.append(f"{step.title}\n", style="white")
        if step.description:
            content.append(f"   {step.description}\n\n", style="dim")
        else:
            content.append("\n", style="dim")

    console.print(Panel(
        content,
        title=f"[bold green]{plan.title}[/] [dim](v{plan.version})[/]",
        border_style="green"
    ))


def render_diff(diff: DiffResult):
    """Display what changed between plan versions."""
    if not diff.added and not diff.removed and not diff.modified:
        return

    content = Text()

    for step in diff.added:
        content.append(f"+ {step.title}\n", style="bold green")

    for step in diff.removed:
        content.append(f"- {step.title}\n", style="bold red")

    for step in diff.modified:
        content.append(f"~ {step.title}\n", style="bold yellow")

    console.print(Panel(
        content,
        title="[bold]Changes[/]",
        border_style="yellow"
    ))


def render_agent_message(content: str):
    """Display agent response."""
    console.print(Panel(
        content,
        title="[bold blue]Agent[/]",
        border_style="blue"
    ))


def render_error(message: str):
    """Display error message."""
    console.print(f"[bold red]Error:[/] {message}")