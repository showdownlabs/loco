"""UI components for loco - panels, spinners, and tool output."""

from contextlib import contextmanager
from typing import Any, Generator

from rich.console import Console, Group
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.spinner import Spinner as RichSpinner
from rich.syntax import Syntax
from rich.text import Text


class Spinner:
    """A spinner for showing activity."""

    def __init__(self, console: Console, message: str = "Thinking...") -> None:
        self.console = console
        self.message = message
        self._live: Live | None = None

    def __enter__(self) -> "Spinner":
        spinner = RichSpinner("dots", text=Text(self.message, style="dim"))
        self._live = Live(spinner, console=self.console, transient=True)
        self._live.__enter__()
        return self

    def __exit__(self, *args: Any) -> None:
        if self._live:
            self._live.__exit__(*args)
            self._live = None

    def update(self, message: str) -> None:
        """Update the spinner message."""
        if self._live:
            spinner = RichSpinner("dots", text=Text(message, style="dim"))
            self._live.update(spinner)


class ToolPanel:
    """Panel for displaying tool calls and results."""

    @staticmethod
    def tool_call(name: str, arguments: dict[str, Any], console: Console) -> None:
        """Display a tool call panel."""
        # Format arguments
        args_lines = []
        for key, value in arguments.items():
            if isinstance(value, str) and len(value) > 100:
                # Truncate long strings
                display_value = value[:100] + "..."
            else:
                display_value = repr(value)
            args_lines.append(f"  [cyan]{key}[/cyan]: {display_value}")

        content = "\n".join(args_lines) if args_lines else "[dim]No arguments[/dim]"

        panel = Panel(
            content,
            title=f"[bold yellow]Tool:[/bold yellow] {name}",
            border_style="yellow",
            padding=(0, 1),
        )
        console.print(panel)

    @staticmethod
    def tool_result(name: str, result: str, success: bool, console: Console) -> None:
        """Display a tool result panel."""
        # Truncate very long results
        max_lines = 50
        lines = result.split("\n")
        if len(lines) > max_lines:
            truncated = "\n".join(lines[:max_lines])
            truncated += f"\n[dim]... ({len(lines) - max_lines} more lines)[/dim]"
        else:
            truncated = result

        style = "green" if success else "red"
        title = f"[bold {style}]Result:[/bold {style}] {name}"

        panel = Panel(
            truncated,
            title=title,
            border_style=style,
            padding=(0, 1),
        )
        console.print(panel)

    @staticmethod
    def error(message: str, console: Console) -> None:
        """Display an error panel."""
        panel = Panel(
            message,
            title="[bold red]Error[/bold red]",
            border_style="red",
            padding=(0, 1),
        )
        console.print(panel)


class StreamingMarkdown:
    """Helper for streaming markdown content."""

    def __init__(self, console: Console) -> None:
        self.console = console
        self.content = ""
        self._live: Live | None = None

    def __enter__(self) -> "StreamingMarkdown":
        self._live = Live(
            "",
            console=self.console,
            refresh_per_second=10,
            transient=False,
        )
        self._live.__enter__()
        return self

    def __exit__(self, *args: Any) -> None:
        if self._live:
            # Final render
            if self.content:
                self._live.update(Markdown(self.content))
            self._live.__exit__(*args)
            self._live = None

    def update(self, content: str) -> None:
        """Update the streaming content."""
        self.content = content
        if self._live and content:
            self._live.update(Markdown(content))

    def append(self, chunk: str) -> None:
        """Append a chunk to the content."""
        self.content += chunk
        if self._live and self.content:
            self._live.update(Markdown(self.content))


@contextmanager
def thinking_spinner(console: Console) -> Generator[Spinner, None, None]:
    """Context manager for a thinking spinner."""
    with Spinner(console, "Thinking...") as spinner:
        yield spinner
