"""Bash command execution tool for loco."""

import os
import subprocess
from typing import Any

from loco.tools.base import Tool, tool_registry


class BashTool(Tool):
    """Tool for executing bash commands."""

    def __init__(self, timeout: int = 120) -> None:
        self._timeout = timeout

    @property
    def name(self) -> str:
        return "bash"

    @property
    def description(self) -> str:
        return (
            "Execute a bash command and return its output. "
            "Use this for running tests, git commands, package managers, etc. "
            "Commands run in the current working directory."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The bash command to execute.",
                },
                "timeout": {
                    "type": "integer",
                    "description": f"Timeout in seconds. Default is {self._timeout}.",
                },
            },
            "required": ["command"],
        }

    def execute(self, command: str, timeout: int | None = None) -> str:
        """Execute a bash command."""
        effective_timeout = timeout or self._timeout

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=effective_timeout,
                cwd=os.getcwd(),
                env=os.environ.copy(),
            )

            output_parts = []

            if result.stdout:
                output_parts.append(result.stdout)

            if result.stderr:
                if output_parts:
                    output_parts.append("\n--- stderr ---\n")
                output_parts.append(result.stderr)

            if result.returncode != 0:
                output_parts.append(f"\n[Exit code: {result.returncode}]")

            output = "".join(output_parts)

            # Truncate very long output
            max_chars = 50000
            if len(output) > max_chars:
                output = output[:max_chars] + f"\n\n[Output truncated at {max_chars} characters]"

            return output if output else "[Command completed with no output]"

        except subprocess.TimeoutExpired:
            return f"Error: Command timed out after {effective_timeout} seconds"
        except Exception as e:
            return f"Error executing command: {e}"


# Register the tool with default timeout
tool_registry.register(BashTool())
