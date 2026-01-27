# Command Loading Fix - Claude Desktop Compatibility

## Problem

The loco CLI was not finding commands in `.claude/commands/` directory even when they existed as flat `.md` files. The command loading system only supported the subdirectory format (e.g., `commands/commit/COMMAND.md`) but not flat files (e.g., `commands/commit.md`).

This caused the issue where:
```bash
> /commands
No commands found.
Add commands to .loco/commands/, .claude/commands/, or ~/.config/loco/commands/
```

Even though commands existed:
```bash
> ! ls .claude/commands
commit.md
pr.md
...
```

## Solution

Updated `src/loco/commands.py` to support **both** command formats:

### Format 1: Subdirectory (original)
```
.loco/commands/
  commit/
    COMMAND.md
```

### Format 2: Flat files (Claude Desktop compatible)
```
.claude/commands/
  commit.md
  pr.md
```

## Changes Made

### 1. Updated `_load_commands_from_dir()` method
- Now iterates through all items in the commands directory
- Skips hidden files (starting with `.`)
- Handles directories: looks for `COMMAND.md` inside (original behavior)
- Handles `.md` files: loads them directly as commands (new behavior)

### 2. Updated `_parse_command_file()` method
- Extracts command name intelligently:
  - For flat files: uses filename stem (e.g., `commit.md` → `commit`)
  - For subdirectories: uses parent directory name (e.g., `commit/COMMAND.md` → `commit`)
  - Frontmatter `name` field always overrides defaults

### 3. Added comprehensive tests
- Created `tests/test_commands.py` with 13 test cases covering:
  - Flat file loading
  - Subdirectory loading
  - Mixed format loading
  - Hidden file skipping
  - Name extraction logic
  - Frontmatter parsing
  - Command filtering
  - Discovery precedence

### 4. Updated documentation
- Updated `docs/development.md` to explain both formats
- Added examples of YAML frontmatter options

## Testing

All 13 new tests pass:
```bash
pytest tests/test_commands.py -v
# 13 passed in 0.08s
```

Verified with real commands:
```bash
cd /path/to/employer-of-record
python3 -c "
from pathlib import Path
from loco.commands import CommandRegistry
registry = CommandRegistry()
registry.discover(Path.cwd())
print(f'Found {len(registry.commands)} commands')
"
# Output: Found 14 commands
```

## Benefits

1. **Claude Desktop Compatibility**: Existing `.claude/commands/*.md` files now work
2. **Backward Compatible**: Original subdirectory format still works
3. **Flexible**: Projects can use either format or mix both
4. **No Migration Required**: Existing commands continue to work

## Command Precedence

Commands are loaded in this order (later overrides earlier):
1. User commands: `~/.config/loco/commands/`
2. Claude Desktop: `.claude/commands/`
3. Loco project: `.loco/commands/` (highest priority)

This allows users to:
- Share commands via `.claude/` for Claude Desktop compatibility
- Override with project-specific commands in `.loco/`
- Have personal defaults in `~/.config/loco/`
