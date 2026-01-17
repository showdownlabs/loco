"""Grep tool for searching file contents."""

import os
import re
from pathlib import Path
from typing import Any

from loco.tools.base import Tool, tool_registry


class GrepTool(Tool):
    """Tool for searching file contents with regex."""

    @property
    def name(self) -> str:
        return "grep"

    @property
    def description(self) -> str:
        return (
            "Search for a pattern in file contents. "
            "Supports regex patterns. "
            "Can search in a specific file, directory, or filter by file glob. "
            "Returns matching lines with file paths and line numbers."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Regex pattern to search for in file contents.",
                },
                "path": {
                    "type": "string",
                    "description": "File or directory to search in. Defaults to current directory.",
                },
                "glob": {
                    "type": "string",
                    "description": "Glob pattern to filter files (e.g., '**/*.py'). Only used if path is a directory.",
                },
                "case_insensitive": {
                    "type": "boolean",
                    "description": "Whether to ignore case. Default is false.",
                },
                "context_lines": {
                    "type": "integer",
                    "description": "Number of lines to show before and after each match. Default is 0.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of matches to return. Default is 50.",
                },
            },
            "required": ["pattern"],
        }

    def execute(
        self,
        pattern: str,
        path: str | None = None,
        glob: str | None = None,
        case_insensitive: bool = False,
        context_lines: int = 0,
        limit: int = 50,
    ) -> str:
        """Search for pattern in files."""
        search_path = Path(path) if path else Path.cwd()

        if not search_path.exists():
            return f"Error: Path does not exist: {search_path}"

        # Compile regex
        flags = re.IGNORECASE if case_insensitive else 0
        try:
            regex = re.compile(pattern, flags)
        except re.error as e:
            return f"Error: Invalid regex pattern: {e}"

        # Collect files to search
        files_to_search: list[Path] = []

        if search_path.is_file():
            files_to_search = [search_path]
        else:
            # Directory - use glob or default to all files
            glob_pattern = glob or "**/*"
            files_to_search = [
                f for f in search_path.glob(glob_pattern)
                if f.is_file() and not self._is_binary(f)
            ]

        matches: list[str] = []
        match_count = 0
        files_with_matches = 0

        for file_path in files_to_search:
            if match_count >= limit:
                break

            try:
                file_matches = self._search_file(
                    file_path, regex, context_lines, limit - match_count
                )
                if file_matches:
                    files_with_matches += 1
                    matches.extend(file_matches)
                    match_count += len(file_matches)
            except Exception:
                # Skip files that can't be read
                continue

        if not matches:
            return f"No matches found for pattern: {pattern}"

        # Format output
        header = f"Found {match_count} match(es) in {files_with_matches} file(s):\n"
        result = header + "\n".join(matches)

        if match_count >= limit:
            result += f"\n\n[Limited to {limit} matches]"

        return result

    def _is_binary(self, path: Path) -> bool:
        """Check if a file is likely binary."""
        # Skip common binary extensions
        binary_extensions = {
            '.pyc', '.pyo', '.so', '.dll', '.exe', '.bin',
            '.png', '.jpg', '.jpeg', '.gif', '.ico', '.pdf',
            '.zip', '.tar', '.gz', '.bz2', '.7z', '.rar',
            '.mp3', '.mp4', '.avi', '.mov', '.wav',
            '.ttf', '.woff', '.woff2', '.eot',
            '.db', '.sqlite', '.sqlite3',
        }
        if path.suffix.lower() in binary_extensions:
            return True

        # Check first few bytes for null characters
        try:
            with open(path, 'rb') as f:
                chunk = f.read(1024)
                return b'\x00' in chunk
        except Exception:
            return True

    def _search_file(
        self,
        file_path: Path,
        regex: re.Pattern,
        context_lines: int,
        remaining_limit: int,
    ) -> list[str]:
        """Search a single file for matches."""
        matches: list[str] = []

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
        except Exception:
            return []

        for i, line in enumerate(lines):
            if len(matches) >= remaining_limit:
                break

            if regex.search(line):
                # Get relative path if possible
                try:
                    display_path = file_path.relative_to(Path.cwd())
                except ValueError:
                    display_path = file_path

                line_num = i + 1
                content = line.rstrip('\n\r')

                if context_lines > 0:
                    # Include context
                    start = max(0, i - context_lines)
                    end = min(len(lines), i + context_lines + 1)

                    context_parts = [f"\n{display_path}:{line_num}:"]
                    for j in range(start, end):
                        prefix = ">" if j == i else " "
                        context_parts.append(
                            f"  {prefix} {j + 1}: {lines[j].rstrip()}"
                        )
                    matches.append("\n".join(context_parts))
                else:
                    # Just the matching line
                    matches.append(f"{display_path}:{line_num}: {content}")

        return matches


# Register the tool
tool_registry.register(GrepTool())
