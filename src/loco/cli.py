"""CLI entry point for loco."""

import os
import sys
from pathlib import Path

import click
from rich.console import Console

from loco import __version__
from loco.chat import Conversation, ToolCall, chat_turn, get_default_system_prompt
from loco.config import (
    Config,
    get_config_path,
    load_config,
    resolve_model,
    save_config,
)
from loco.tools import tool_registry
from loco.ui.console import get_console


def handle_slash_command(
    command: str,
    conversation: Conversation,
    config: Config,
    console: Console,
) -> bool:
    """Handle slash commands. Returns True if command was handled."""
    parts = command.strip().split(maxsplit=1)
    cmd = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""

    if cmd == "/help":
        console.print("""
[bold]Available Commands:[/bold]

  [cyan]/help[/cyan]           Show this help message
  [cyan]/clear[/cyan]          Clear conversation history
  [cyan]/model[/cyan] [name]   Show or switch the current model
  [cyan]/config[/cyan]         Show configuration file path
  [cyan]/quit[/cyan]           Exit loco (or Ctrl+C)

[bold]Tips:[/bold]
- Use model aliases from config (e.g., /model gpt4)
- Or use full LiteLLM model strings (e.g., /model openai/gpt-4o)
""")
        return True

    elif cmd == "/clear":
        conversation.clear()
        console.print("[dim]Conversation cleared.[/dim]")
        return True

    elif cmd == "/model":
        if args:
            # Switch model
            new_model = resolve_model(args, config)
            conversation.model = new_model
            console.print(f"[dim]Switched to model: {new_model}[/dim]")
        else:
            # Show current model
            console.print(f"[dim]Current model: {conversation.model}[/dim]")
            console.print("\n[dim]Available aliases:[/dim]")
            for alias, model in config.models.items():
                marker = " [green]<-- current[/green]" if model == conversation.model else ""
                console.print(f"  [cyan]{alias}[/cyan]: {model}{marker}")
        return True

    elif cmd == "/config":
        console.print(f"[dim]Config file: {get_config_path()}[/dim]")
        return True

    elif cmd in ("/quit", "/exit", "/q"):
        console.print("[dim]Goodbye![/dim]")
        sys.exit(0)

    return False


def tool_executor(tool_call: ToolCall) -> str:
    """Execute a tool call and return the result."""
    return tool_registry.execute(tool_call.name, tool_call.arguments)


@click.group(invoke_without_command=True)
@click.option(
    "--model", "-m",
    help="Model to use (alias or full LiteLLM model string)",
)
@click.option(
    "--cwd", "-C",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Working directory",
)
@click.version_option(version=__version__)
@click.pass_context
def main(ctx: click.Context, model: str | None, cwd: str | None) -> None:
    """Loco - LLM Coding Assistant CLI.

    An AI-powered coding assistant that works with any OpenAI-compatible LLM.
    """
    # If a subcommand is invoked, let it handle things
    if ctx.invoked_subcommand is not None:
        return

    # Load configuration
    try:
        config = load_config()
    except Exception as e:
        click.echo(f"Error loading config: {e}", err=True)
        sys.exit(1)

    # Change working directory if specified
    if cwd:
        os.chdir(cwd)

    # Resolve model
    effective_model = resolve_model(model or config.default_model, config)

    # Initialize UI
    console = get_console()
    rich_console = console.console

    # Print welcome
    console.print_welcome(effective_model, os.getcwd())

    # Initialize conversation
    conversation = Conversation(
        model=effective_model,
        config=config,
    )
    conversation.add_system_message(get_default_system_prompt(os.getcwd()))

    # Get tools
    tools = tool_registry.get_openai_tools()

    # Main loop
    while True:
        try:
            user_input = console.get_input("> ")

            if user_input is None:
                # Ctrl+C or Ctrl+D
                console.print("\n[dim]Goodbye![/dim]")
                break

            user_input = user_input.strip()

            if not user_input:
                continue

            # Handle slash commands
            if user_input.startswith("/"):
                if handle_slash_command(user_input, conversation, config, rich_console):
                    continue
                else:
                    console.print_error(f"Unknown command: {user_input.split()[0]}")
                    console.print("[dim]Type /help for available commands[/dim]")
                    continue

            # Regular chat
            try:
                chat_turn(
                    conversation=conversation,
                    user_input=user_input,
                    tools=tools,
                    tool_executor=tool_executor,
                    console=rich_console,
                )
            except KeyboardInterrupt:
                console.print("\n[dim]Interrupted[/dim]")
                continue
            except Exception as e:
                console.print_error(f"Error: {e}")
                continue

            console.print()  # Blank line after response

        except KeyboardInterrupt:
            console.print("\n[dim]Goodbye![/dim]")
            break


@main.command()
@click.argument("key", required=False)
@click.argument("value", required=False)
def config(key: str | None, value: str | None) -> None:
    """View or modify configuration.

    Without arguments, shows the config file path.
    With KEY, shows that config value.
    With KEY and VALUE, sets the config value.
    """
    cfg = load_config()

    if key is None:
        # Show config path and summary
        click.echo(f"Config file: {get_config_path()}")
        click.echo(f"Default model: {cfg.default_model}")
        click.echo(f"Model aliases: {len(cfg.models)}")
        return

    if value is None:
        # Show specific key
        if key == "default_model":
            click.echo(cfg.default_model)
        elif key == "models":
            for alias, model in cfg.models.items():
                click.echo(f"  {alias}: {model}")
        else:
            click.echo(f"Unknown config key: {key}", err=True)
        return

    # Set value
    if key == "default_model":
        cfg.default_model = value
        save_config(cfg)
        click.echo(f"Set default_model to: {value}")
    else:
        click.echo(f"Cannot set config key: {key}", err=True)


if __name__ == "__main__":
    main()
