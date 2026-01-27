"""Tests for the commands system."""

import tempfile
from pathlib import Path

import pytest

from loco.commands import Command, CommandRegistry


def test_command_creation():
    """Test creating a Command object."""
    cmd = Command(
        name="test-cmd",
        description="A test command",
        content="Do something useful",
    )
    assert cmd.name == "test-cmd"
    assert cmd.description == "A test command"
    assert cmd.user_invocable is True


def test_flat_file_command_loading():
    """Test loading commands from flat .md files (Claude Desktop format)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        commands_dir = Path(tmpdir) / "commands"
        commands_dir.mkdir()

        # Create a flat file command
        command_file = commands_dir / "commit.md"
        command_file.write_text("""---
description: Create a git commit
allowed-tools: Bash(git add:*), Bash(git commit:*)
---

## Your task

Create a commit message following conventional commits.
""")

        # Load commands
        registry = CommandRegistry()
        registry._load_commands_from_dir(commands_dir)

        # Verify command was loaded
        assert "commit" in registry.commands
        cmd = registry.commands["commit"]
        assert cmd.name == "commit"
        assert cmd.description == "Create a git commit"
        assert "Create a commit message" in cmd.content


def test_subdirectory_command_loading():
    """Test loading commands from subdirectories with COMMAND.md."""
    with tempfile.TemporaryDirectory() as tmpdir:
        commands_dir = Path(tmpdir) / "commands"
        commands_dir.mkdir()

        # Create a subdirectory command
        cmd_dir = commands_dir / "pr"
        cmd_dir.mkdir()
        command_file = cmd_dir / "COMMAND.md"
        command_file.write_text("""---
name: pr
description: Generate a PR description
---

## Your task

Create a pull request description.
""")

        # Load commands
        registry = CommandRegistry()
        registry._load_commands_from_dir(commands_dir)

        # Verify command was loaded
        assert "pr" in registry.commands
        cmd = registry.commands["pr"]
        assert cmd.name == "pr"
        assert cmd.description == "Generate a PR description"


def test_mixed_format_loading():
    """Test loading both flat files and subdirectories together."""
    with tempfile.TemporaryDirectory() as tmpdir:
        commands_dir = Path(tmpdir) / "commands"
        commands_dir.mkdir()

        # Create flat file command
        flat_cmd = commands_dir / "commit.md"
        flat_cmd.write_text("---\ndescription: Commit changes\n---\n\nCommit content")

        # Create subdirectory command
        subdir = commands_dir / "pr"
        subdir.mkdir()
        subdir_cmd = subdir / "COMMAND.md"
        subdir_cmd.write_text("---\ndescription: Create PR\n---\n\nPR content")

        # Load commands
        registry = CommandRegistry()
        registry._load_commands_from_dir(commands_dir)

        # Both should be loaded
        assert len(registry.commands) == 2
        assert "commit" in registry.commands
        assert "pr" in registry.commands


def test_hidden_files_skipped():
    """Test that hidden files are skipped during loading."""
    with tempfile.TemporaryDirectory() as tmpdir:
        commands_dir = Path(tmpdir) / "commands"
        commands_dir.mkdir()

        # Create a hidden file
        hidden_file = commands_dir / ".hidden.md"
        hidden_file.write_text("---\ndescription: Hidden\n---\n\nContent")

        # Create a normal file
        normal_file = commands_dir / "visible.md"
        normal_file.write_text("---\ndescription: Visible\n---\n\nContent")

        # Load commands
        registry = CommandRegistry()
        registry._load_commands_from_dir(commands_dir)

        # Only normal file should be loaded
        assert len(registry.commands) == 1
        assert "visible" in registry.commands
        assert ".hidden" not in registry.commands


def test_command_name_from_filename():
    """Test that command name is extracted from filename for flat files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        commands_dir = Path(tmpdir) / "commands"
        commands_dir.mkdir()

        # Create command without name in frontmatter
        command_file = commands_dir / "my-special-command.md"
        command_file.write_text("---\ndescription: A command\n---\n\nContent")

        registry = CommandRegistry()
        registry._load_commands_from_dir(commands_dir)

        # Name should be derived from filename
        assert "my-special-command" in registry.commands


def test_command_name_from_directory():
    """Test that command name is extracted from directory name for COMMAND.md."""
    with tempfile.TemporaryDirectory() as tmpdir:
        commands_dir = Path(tmpdir) / "commands"
        commands_dir.mkdir()

        # Create command without name in frontmatter
        cmd_dir = commands_dir / "my-dir-command"
        cmd_dir.mkdir()
        command_file = cmd_dir / "COMMAND.md"
        command_file.write_text("---\ndescription: A command\n---\n\nContent")

        registry = CommandRegistry()
        registry._load_commands_from_dir(commands_dir)

        # Name should be derived from directory name
        assert "my-dir-command" in registry.commands


def test_frontmatter_name_override():
    """Test that frontmatter name overrides filename/directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        commands_dir = Path(tmpdir) / "commands"
        commands_dir.mkdir()

        # Create command with explicit name
        command_file = commands_dir / "file-name.md"
        command_file.write_text("""---
name: custom-name
description: A command
---

Content""")

        registry = CommandRegistry()
        registry._load_commands_from_dir(commands_dir)

        # Should use frontmatter name
        assert "custom-name" in registry.commands
        assert "file-name" not in registry.commands


def test_command_without_frontmatter():
    """Test loading a command without YAML frontmatter."""
    with tempfile.TemporaryDirectory() as tmpdir:
        commands_dir = Path(tmpdir) / "commands"
        commands_dir.mkdir()

        command_file = commands_dir / "simple.md"
        command_file.write_text("This is a simple command\n\nWith some content")

        registry = CommandRegistry()
        registry._load_commands_from_dir(commands_dir)

        # Should still load with defaults
        assert "simple" in registry.commands
        cmd = registry.commands["simple"]
        assert cmd.name == "simple"
        assert cmd.description == "This is a simple command"  # First line becomes description


def test_user_invocable_filter():
    """Test filtering user-invocable commands."""
    with tempfile.TemporaryDirectory() as tmpdir:
        commands_dir = Path(tmpdir) / "commands"
        commands_dir.mkdir()

        # User-invocable command
        cmd1 = commands_dir / "visible.md"
        cmd1.write_text("---\nuser-invocable: true\ndescription: Visible\n---\n\nContent")

        # Non-user-invocable command
        cmd2 = commands_dir / "hidden.md"
        cmd2.write_text("---\nuser-invocable: false\ndescription: Hidden\n---\n\nContent")

        registry = CommandRegistry()
        registry._load_commands_from_dir(commands_dir)
        registry._discovered = True  # Mark as discovered to prevent auto-discovery

        # Both loaded
        assert len(registry.commands) == 2

        # Only one is user-invocable
        user_commands = registry.get_user_invocable()
        assert len(user_commands) == 1
        assert user_commands[0].name == "visible"


def test_command_discovery_precedence():
    """Test that commands are discovered with correct precedence."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)

        # Create all three command directories
        user_dir = project_dir / ".config" / "loco" / "commands"
        user_dir.mkdir(parents=True)
        
        claude_dir = project_dir / ".claude" / "commands"
        claude_dir.mkdir(parents=True)
        
        loco_dir = project_dir / ".loco" / "commands"
        loco_dir.mkdir(parents=True)

        # Create same command in all three locations with different descriptions
        (user_dir / "test.md").write_text("---\ndescription: User version\n---\n\nUser")
        (claude_dir / "test.md").write_text("---\ndescription: Claude version\n---\n\nClaude")
        (loco_dir / "test.md").write_text("---\ndescription: Loco version\n---\n\nLoco")

        # Mock get_config_dir to return our test directory
        import loco.commands
        original_get_config_dir = loco.commands.get_config_dir
        loco.commands.get_config_dir = lambda: project_dir / ".config" / "loco"

        try:
            registry = CommandRegistry()
            registry.discover(project_dir)

            # Loco version should win (highest precedence)
            assert registry.commands["test"].description == "Loco version"
        finally:
            loco.commands.get_config_dir = original_get_config_dir


def test_get_system_prompt_addition():
    """Test command system prompt generation."""
    cmd = Command(
        name="test",
        description="Test command",
        content="Do something",
    )
    
    prompt = cmd.get_system_prompt_addition()
    assert "COMMAND: test" in prompt
    assert "Do something" in prompt
    assert "END COMMAND" in prompt


def test_command_match_by_name():
    """Test command matching by name."""
    with tempfile.TemporaryDirectory() as tmpdir:
        commands_dir = Path(tmpdir) / "commands"
        commands_dir.mkdir()

        cmd_file = commands_dir / "commit.md"
        cmd_file.write_text("---\ndescription: Create commits\n---\n\nContent")

        registry = CommandRegistry()
        registry._load_commands_from_dir(commands_dir)

        # Should match when command name is in input
        matches = registry.match_commands("I need to commit my changes")
        assert len(matches) > 0
        assert matches[0].name == "commit"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
