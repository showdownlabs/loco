"""Glob tool for finding files by pattern."""

import os
from pathlib import Path
from typing import Any

from loco.tools.base import Tool, tool_registry


class GlobTool(Tool):
    """Tool for finding files matching a glob pattern."""

    @property
    def name(self) -> str:
        return "glob"

    @property
    def description(self) -> str:
        return (
            "Find files matching a glob pattern. "
            "Supports patterns like '**/*.py' (all Python files), "
            "'src/**/*.ts' (TypeScript in src), '*.md' (markdown in current dir). "
            "Returns file paths sorted by modification time (newest first)."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Glob pattern to match files (e.g., '**/*.py', 'src/**/*.ts').",
                },
                "path": {
                    "type": "string",
                    "description": "Directory to search in. Defaults to current working directory.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of files to return. Default is 100.",
                },
            },
            "required": ["pattern"],
        }

    def execute(
        self,
        pattern: str,
        path: str | None = None,
        limit: int = 100,
    ) -> str:
        """Find files matching the glob pattern."""
        search_path = Path(path) if path else Path.cwd()

        if not search_path.exists():
            return f"Error: Directory does not exist: {search_path}"

        if not search_path.is_dir():
            return f"Error: Not a directory: {search_path}"

        try:
            # Find matching files
            matches = list(search_path.glob(pattern))

            # Filter to files only (not directories)
            files = [m for m in matches if m.is_file()]

            # Sort by modification time (newest first)
            files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

            # Apply limit
            if len(files) > limit:
                files = files[:limit]
                truncated = True
            else:
                truncated = False

            if not files:
                return f"No files found matching pattern: {pattern}"

            # Format output
            lines = [f"Found {len(files)} file(s) matching '{pattern}':"]
            for f in files:
                # Show relative path if possible
                try:
                    rel_path = f.relative_to(search_path)
                    lines.append(f"  {rel_path}")
                except ValueError:
                    lines.append(f"  {f}")

            if truncated:
                lines.append(f"\n[Limited to {limit} results]")

            return "\n".join(lines)

        except Exception as e:
            return f"Error searching for files: {e}"


# Register the tool
tool_registry.register(GlobTool())
