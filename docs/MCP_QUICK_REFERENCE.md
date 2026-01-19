# MCP Quick Reference

Quick reference for using loco with the Model Context Protocol.

## Commands

```bash
# Run loco as MCP server
loco mcp-server

# Start loco normally (auto-connects to configured MCP servers)
loco
```

## Configuration

### Basic MCP Server Config

Add to `~/.config/loco/config.json`:

```json
{
  "mcp_servers": {
    "server_name": {
      "command": ["command"],
      "args": ["arg1", "arg2"],
      "env": {
        "VAR": "${ENV_VAR}"
      },
      "cwd": "/optional/working/directory"
    }
  }
}
```

### Example: GitHub Integration

```json
{
  "mcp_servers": {
    "github": {
      "command": ["npx"],
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    }
  }
}
```

### Example: Database Access

```json
{
  "mcp_servers": {
    "postgres": {
      "command": ["uvx"],
      "args": ["mcp-server-postgres", "postgresql://localhost/mydb"]
    }
  }
}
```

## Claude Desktop Integration

### Config File Location

- **macOS/Linux**: `~/.config/claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

### Config Content

```json
{
  "mcpServers": {
    "loco": {
      "command": "loco",
      "args": ["mcp-server"]
    }
  }
}
```

### Restart Required

After adding the config, restart Claude Desktop to activate loco's tools.

## Available Official MCP Servers

| Server | Command | Description |
|--------|---------|-------------|
| **filesystem** | `npx -y @modelcontextprotocol/server-filesystem <dir>` | File operations |
| **github** | `npx -y @modelcontextprotocol/server-github` | GitHub API |
| **postgres** | `npx -y @modelcontextprotocol/server-postgres <url>` | PostgreSQL |
| **sqlite** | `npx -y @modelcontextprotocol/server-sqlite <db>` | SQLite |
| **fetch** | `npx -y @modelcontextprotocol/server-fetch` | Web fetch |
| **brave-search** | `npx -y @modelcontextprotocol/server-brave-search` | Web search |
| **gdrive** | `npx -y @modelcontextprotocol/server-gdrive` | Google Drive |
| **slack** | `npx -y @modelcontextprotocol/server-slack` | Slack |

## Environment Variables

Common environment variables used by MCP servers:

```bash
# GitHub
export GITHUB_TOKEN="ghp_..."

# Brave Search
export BRAVE_API_KEY="..."

# PostgreSQL (alternative to connection string)
export DATABASE_URL="postgresql://..."

# Google Drive
export GOOGLE_CLIENT_ID="..."
export GOOGLE_CLIENT_SECRET="..."
```

## Loco Tools Exposed via MCP

When running `loco mcp-server`, these tools are available to MCP clients:

| Tool | Description | Parameters |
|------|-------------|------------|
| **read** | Read file contents | `file_path`, `limit?`, `offset?` |
| **write** | Write to file | `file_path`, `content` |
| **edit** | String replacement | `file_path`, `old_string`, `new_string`, `replace_all?` |
| **bash** | Execute command | `command`, `timeout?` |
| **glob** | Find files | `pattern`, `path?`, `limit?` |
| **grep** | Search files | `pattern`, `path?`, `glob?`, `context_lines?` |

## Testing

### Test MCP Server

```bash
# Send test request
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | loco mcp-server
```

### Run Test Suite

```bash
python tests/test_mcp.py
```

### Test Script

```bash
./examples/mcp/test_mcp_server.sh
```

## Troubleshooting

### MCP Server Not Starting

1. Check command is in PATH: `which npx`
2. Test server manually: `npx -y @modelcontextprotocol/server-filesystem /tmp`
3. Check stderr for errors

### Tools Not Appearing

1. Verify server initialized: Check logs
2. Confirm server supports tools capability
3. Restart loco after config changes

### Permission Errors

1. Check filesystem server has directory access
2. Verify environment variables are set
3. Check server process has necessary permissions

### Claude Desktop Not Seeing Tools

1. Verify config file location
2. Check JSON syntax is valid
3. Ensure loco is installed and in PATH
4. Restart Claude Desktop

## Protocol Details

### Message Format

JSON-RPC 2.0 over stdio:

```json
// Request
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list",
  "params": {}
}

// Response
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "tools": [...]
  }
}
```

### Protocol Version

- **Implemented**: `2024-11-05`
- **Compatible with**: Anthropic Claude Desktop, other MCP clients

### Methods Supported

**As Server:**
- `initialize` - Initialize connection
- `tools/list` - List available tools
- `tools/call` - Execute a tool

**As Client:**
- All of the above when connecting to servers

## Resources

- **Full Documentation**: [docs/MCP.md](MCP.md)
- **Examples**: [examples/mcp/](../examples/mcp/)
- **MCP Specification**: https://modelcontextprotocol.io/
- **Official Servers**: https://github.com/modelcontextprotocol/servers

## Common Workflows

### Workflow 1: Local Development

```json
{
  "mcp_servers": {
    "filesystem": {
      "command": ["npx"],
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "${HOME}/projects"]
    },
    "git": {
      "command": ["uvx"],
      "args": ["mcp-server-git"],
      "cwd": "${HOME}/projects/myapp"
    }
  }
}
```

### Workflow 2: Research & Documentation

```json
{
  "mcp_servers": {
    "brave": {
      "command": ["npx"],
      "args": ["-y", "@modelcontextprotocol/server-brave-search"],
      "env": {"BRAVE_API_KEY": "${BRAVE_API_KEY}"}
    },
    "fetch": {
      "command": ["npx"],
      "args": ["-y", "@modelcontextprotocol/server-fetch"]
    }
  }
}
```

### Workflow 3: Full-Stack Development

```json
{
  "mcp_servers": {
    "postgres": {
      "command": ["uvx"],
      "args": ["mcp-server-postgres", "${DATABASE_URL}"]
    },
    "github": {
      "command": ["npx"],
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {"GITHUB_TOKEN": "${GITHUB_TOKEN}"}
    },
    "docker": {
      "command": ["uvx"],
      "args": ["mcp-server-docker"]
    }
  }
}
```

---

**Need more details?** See the [full MCP documentation](MCP.md).
