"""Console wrapper for Rich-based terminal UI."""

import sys
from enum import Enum
from typing import Any

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.filters import Condition
from prompt_toolkit.application import get_app
from rich.console import Console as RichConsole
from rich.live import Live
from rich.markdown import Markdown
from rich.markup import escape as escape_markup
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text

from loco.config import get_config_dir


class InputMode(Enum):
    """Input modes for the TUI."""
    CHAT = "chat"       # Normal AI chat mode
    BASH = "bash"       # Direct bash command execution
    # Future modes can be added here:
    # PLAN = "plan"     # Planning mode
    # EDIT = "edit"     # Edit acceptance mode


# Mode configuration: prompt symbol, color, hint text
MODE_CONFIG = {
    InputMode.CHAT: {
        "symbol": ">",
        "color": "ansibrightcyan",
        "rich_color": "bright_cyan",
        "hint": "",  # No hint for default mode
    },
    InputMode.BASH: {
        "symbol": "!",
        "color": "ansibrightyellow",
        "rich_color": "bright_yellow",
        "hint": "! bash mode (shift+Tab to cycle)",
    },
    # Future modes:
    # InputMode.PLAN: {
    #     "symbol": "⏸",
    #     "color": "ansibrightmagenta",
    #     "rich_color": "bright_magenta",
    #     "hint": "⏸ plan mode (shift+Tab to cycle)",
    # },
}


class Console:
    """Wrapper around Rich console with loco-specific functionality."""

    # Horizontal padding for the TUI (number of spaces on each side)
    PADDING = 2

    def __init__(self) -> None:
        self.console = RichConsole()
        self._current_mode = InputMode.CHAT
        self._setup_prompt_session()

    @property
    def current_mode(self) -> InputMode:
        """Get the current input mode."""
        return self._current_mode

    @current_mode.setter
    def current_mode(self, mode: InputMode) -> None:
        """Set the current input mode and update prompt style."""
        self._current_mode = mode
        self._update_prompt_style()

    def cycle_mode(self) -> InputMode:
        """Cycle to the next input mode."""
        modes = list(InputMode)
        current_index = modes.index(self._current_mode)
        next_index = (current_index + 1) % len(modes)
        self.current_mode = modes[next_index]
        return self._current_mode

    def _update_prompt_style(self) -> None:
        """Update prompt style based on current mode."""
        mode_cfg = MODE_CONFIG[self._current_mode]
        self.prompt_style = Style.from_dict({
            "prompt": f"bold {mode_cfg['color']}",
            "prompt-suffix": "",
            "separator": "ansibrightblack",
        })

    def _setup_prompt_session(self) -> None:
        """Set up the prompt toolkit session with history."""
        history_dir = get_config_dir() / "history"
        history_dir.mkdir(parents=True, exist_ok=True)
        history_file = history_dir / "prompt_history"

        # Initialize prompt style based on current mode
        self._update_prompt_style()

        # Create key bindings that work like Claude Code
        # - Enter submits (like single-line mode)
        # - Shift+Enter or Alt+Enter adds a newline (for explicit multi-line)
        # - Shift+Tab cycles through modes
        # - Pasting multiline content works
        self.kb = KeyBindings()

        @self.kb.add('enter')
        def _(event):
            """Enter submits the input."""
            event.current_buffer.validate_and_handle()

        @self.kb.add('c-j')
        def _(event):
            """Ctrl+J inserts a newline for multiline input."""
            event.current_buffer.insert_text('\n')

        @self.kb.add('escape', 'enter')
        def _(event):
            """Alt+Enter inserts a newline for multiline input."""
            event.current_buffer.insert_text('\n')

        @self.kb.add('s-tab')
        def _(event):
            """Shift+Tab cycles through input modes."""
            self.cycle_mode()
            # Signal that mode changed - the prompt will update on next get_input

        # Continuation prompt aligns with the input after padding + "> "
        continuation = " " * (self.PADDING + 2)
        self.prompt_session: PromptSession[str] = PromptSession(
            history=FileHistory(str(history_file)),
            style=self.prompt_style,
            multiline=True,  # Allow multiline (for pasting), but Enter submits
            key_bindings=self.kb,
            prompt_continuation=continuation,
        )

    def print(self, *args: Any, **kwargs: Any) -> None:
        """Print to console."""
        self.console.print(*args, **kwargs)

    def print_markdown(self, text: str) -> None:
        """Render and print markdown text."""
        md = Markdown(text)
        self.console.print(md)

    def print_code(self, code: str, language: str = "python") -> None:
        """Print syntax-highlighted code."""
        syntax = Syntax(code, language, theme="monokai", line_numbers=True)
        self.console.print(syntax)

    def print_error(self, message: str) -> None:
        """Print an error message (escapes Rich markup in message)."""
        self.console.print(f"[bold red]Error:[/bold red] {escape_markup(str(message))}")

    def print_warning(self, message: str) -> None:
        """Print a warning message."""
        self.console.print(f"[yellow]Warning:[/yellow] {message}")

    def print_success(self, message: str) -> None:
        """Print a success message."""
        self.console.print(f"[green]{message}[/green]")

    def print_info(self, message: str) -> None:
        """Print an info message."""
        self.console.print(f"[dim]{message}[/dim]")

    def print_model_info(self, model: str) -> None:
        """Print current model information."""
        self.console.print(f"[dim]Model: {model}[/dim]")

    def _pad(self, text: str) -> str:
        """Add horizontal padding to text."""
        padding = " " * self.PADDING
        return f"{padding}{text}"

    def _separator(self) -> str:
        """Create a separator line with padding."""
        padding = " " * self.PADDING
        line_width = max(1, self.console.width - (self.PADDING * 2))
        return f"{padding}[dim]{'─' * line_width}[/dim]"

    def print_welcome(self, model: str, cwd: str) -> None:
        """Print welcome message - minimal Claude Code style."""
        self.console.print()
        self.console.print(self._pad("[bold]loco[/bold] [dim]v0.1.0[/dim]"))
        self.console.print(self._pad(f"[dim]cwd:[/dim] {cwd}"))
        self.console.print(self._pad(f"[dim]model:[/dim] {model}"))
        self.console.print()
        self.console.print(self._pad("[dim]/help for commands · shift+tab for modes · ctrl+c to exit[/dim]"))
        self.console.print()

    def _get_mode_prompt(self) -> str:
        """Get the prompt symbol for the current mode."""
        return MODE_CONFIG[self._current_mode]["symbol"]

    def _get_mode_hint(self) -> str:
        """Get the hint text for the current mode."""
        return MODE_CONFIG[self._current_mode]["hint"]

    def _get_mode_color(self) -> str:
        """Get the Rich color for the current mode."""
        return MODE_CONFIG[self._current_mode]["rich_color"]

    def _print_colored_separator(self) -> None:
        """Print a separator line with the current mode's color."""
        padding = " " * self.PADDING
        line_width = max(1, self.console.width - (self.PADDING * 2))
        color = self._get_mode_color()

        # Use Text object for robust color handling
        separator_text = Text()
        separator_text.append(padding)
        separator_text.append('─' * line_width, style=color)
        self.console.print(separator_text)

    def get_input(self, prompt: str | None = None) -> tuple[str | None, InputMode]:
        """Get user input with prompt toolkit.
        
        Returns:
            A tuple of (input_text, mode) where mode is the InputMode that was active.
            input_text is None if the user cancelled (Ctrl+C/Ctrl+D).
        """
        try:
            # Update prompt style for current mode
            self._update_prompt_style()
            
            # Get mode-specific prompt and styling
            mode_prompt = prompt if prompt is not None else self._get_mode_prompt()
            mode_hint = self._get_mode_hint()
            mode_color = self._get_mode_color()
            
            # Print top separator line with mode color
            self.console.print()
            if self._current_mode == InputMode.CHAT:
                self.console.print(self._separator())
            else:
                self._print_colored_separator()

            # Use formatted prompt with style and padding
            padding = " " * self.PADDING
            result = self.prompt_session.prompt(
                [("", padding), ("class:prompt", mode_prompt), ("", " ")],
                style=self.prompt_style,  # Use updated style
            )

            # Print bottom separator line (only if we got input)
            if result is not None:
                if self._current_mode == InputMode.CHAT:
                    self.console.print(self._separator())
                else:
                    self._print_colored_separator()

                # Show mode hint if not in default chat mode
                if mode_hint:
                    hint_text = Text()
                    hint_text.append(" " * self.PADDING)
                    hint_text.append(mode_hint, style=mode_color)
                    self.console.print(hint_text)

                # Check if pasted content (multiline)
                if '\n' in result:
                    line_count = result.count('\n') + 1
                    self.console.print(self._pad(f"[dim]Pasted {line_count} lines[/dim]"))
                self.console.print()

            # Return both the input and the mode it was captured in
            return result, self._current_mode
        except (EOFError, KeyboardInterrupt):
            return None, self._current_mode

    def get_multiline_input(self, prompt: str = "> ") -> str | None:
        """Get multiline user input (Meta+Enter or Esc+Enter to submit)."""
        try:
            # Create temporary key bindings for explicit multiline mode
            kb = KeyBindings()

            @kb.add('enter')
            def _(event):
                """Enter inserts a newline in multiline mode."""
                event.current_buffer.insert_text('\n')

            @kb.add('escape', 'enter')  # Alt/Meta+Enter to submit
            def _(event):
                """Alt+Enter submits."""
                event.current_buffer.validate_and_handle()

            # Print top separator line
            self.console.print(self._separator())
            self.console.print(self._pad("[dim]Alt+Enter to submit, Enter for new line[/dim]"))

            padding = " " * self.PADDING
            result = self.prompt_session.prompt(
                [("", padding), ("class:prompt", prompt)],
                multiline=True,
                key_bindings=kb,
            )

            # Print bottom separator line
            self.console.print(self._separator())

            return result
        except (EOFError, KeyboardInterrupt):
            return None

    def create_live(self) -> Live:
        """Create a Live context for streaming output."""
        return Live(
            "",
            console=self.console,
            refresh_per_second=10,
            transient=True,
        )

    def clear(self) -> None:
        """Clear the console."""
        self.console.clear()

    @property
    def width(self) -> int:
        """Get console width."""
        return self.console.width


# Global console instance
_console: Console | None = None


def get_console() -> Console:
    """Get the global console instance."""
    global _console
    if _console is None:
        _console = Console()
    return _console
