# MCP (Model Context Protocol) Integration

Loco supports the Model Context Protocol (MCP), allowing it to both expose its tools to other MCP clients and connect to external MCP servers to expand its capabilities.

## What is MCP?

The Model Context Protocol (MCP) is a standardized way for AI assistants to connect to external data sources and tools. It was created by Anthropic and is supported by Claude Desktop and other AI applications.

## Features

- **MCP Server**: Expose loco's tools (read, write, edit, bash, glob, grep) to other MCP clients
- **MCP Client**: Connect to external MCP servers to use their tools within loco
- **Multiple Transports**: Support for stdio (primary), process spawning, and SSE

## Running Loco as an MCP Server

You can run loco as an MCP server to expose its tools to other applications like Claude Desktop.

### Start the Server

```bash
loco mcp-server
```

This runs loco as an MCP server using stdio transport (the standard for MCP).

### Claude Desktop Configuration

To use loco's tools in Claude Desktop, add this to your Claude Desktop config file:

**Location**: `~/.config/claude/claude_desktop_config.json` (Linux/macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows)

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

After restarting Claude Desktop, you'll be able to use loco's file operations, bash execution, and code search tools directly in Claude conversations!

### Available Tools via MCP

When running as an MCP server, loco exposes these tools:

| Tool | Description |
|------|-------------|
| `read` | Read file contents with line numbers |
| `write` | Create or overwrite files |
| `edit` | String replacement editing |
| `bash` | Execute shell commands |
| `glob` | Find files by pattern (`**/*.py`) |
| `grep` | Search file contents with regex |

## Using External MCP Servers in Loco

Loco can connect to external MCP servers to expand its tool capabilities.

### Configuration

Add MCP servers to your loco config file (`~/.config/loco/config.json`):

```json
{
  "default_model": "openai/gpt-4o",
  "mcp_servers": {
    "filesystem": {
      "command": ["npx"],
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/directory"]
    },
    "github": {
      "command": ["npx"],
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    },
    "postgres": {
      "command": ["uvx"],
      "args": ["mcp-server-postgres", "postgresql://localhost/mydb"]
    }
  }
}
```

### Slash Commands for MCP

When MCP servers are configured, loco automatically connects to them on startup and makes their tools available.

```bash
# List all available tools (including MCP server tools)
/tools

# Tools from MCP servers are automatically available
# Just ask the LLM to use them naturally
> "Query the database for all users created today"
```

### Available MCP Servers

Here are some popular MCP servers you can use with loco:

#### Official Anthropic Servers

```bash
# Filesystem operations
npx -y @modelcontextprotocol/server-filesystem /path/to/directory

# GitHub integration
npx -y @modelcontextprotocol/server-github

# PostgreSQL database
npx -y @modelcontextprotocol/server-postgres postgresql://connection-string

# SQLite database
npx -y @modelcontextprotocol/server-sqlite /path/to/database.db

# Fetch web content
npx -y @modelcontextprotocol/server-fetch

# Google Drive
npx -y @modelcontextprotocol/server-gdrive

# Brave Search
npx -y @modelcontextprotocol/server-brave-search

# Slack
npx -y @modelcontextprotocol/server-slack
```

#### Community Servers

Many community-built MCP servers are available on npm and PyPI. Check the [MCP servers repository](https://github.com/modelcontextprotocol/servers) for a full list.

## Example Configurations

### Development Setup

Connect to local filesystem, git, and a development database:

```json
{
  "mcp_servers": {
    "filesystem": {
      "command": ["npx"],
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/projects"]
    },
    "git": {
      "command": ["uvx"],
      "args": ["mcp-server-git"],
      "cwd": "/home/user/projects/myapp"
    },
    "postgres": {
      "command": ["uvx"],
      "args": ["mcp-server-postgres"],
      "env": {
        "DATABASE_URL": "${DATABASE_URL}"
      }
    }
  }
}
```

### Research Setup

Connect to web search and content fetching:

```json
{
  "mcp_servers": {
    "brave": {
      "command": ["npx"],
      "args": ["-y", "@modelcontextprotocol/server-brave-search"],
      "env": {
        "BRAVE_API_KEY": "${BRAVE_API_KEY}"
      }
    },
    "fetch": {
      "command": ["npx"],
      "args": ["-y", "@modelcontextprotocol/server-fetch"]
    }
  }
}
```

### Full-Stack Development

Combine multiple tools for full-stack development:

```json
{
  "mcp_servers": {
    "filesystem": {
      "command": ["npx"],
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/projects/webapp"]
    },
    "postgres": {
      "command": ["uvx"],
      "args": ["mcp-server-postgres", "postgresql://localhost/webapp_dev"]
    },
    "github": {
      "command": ["npx"],
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    },
    "docker": {
      "command": ["uvx"],
      "args": ["mcp-server-docker"]
    }
  }
}
```

## Implementation Details

### Transport Layer

Loco supports multiple MCP transport mechanisms:

1. **Stdio Transport** (primary): JSON-RPC over stdin/stdout
2. **Process Transport**: Spawn and manage MCP server processes
3. **SSE Transport**: Server-Sent Events for HTTP-based connections (planned)

### Protocol Version

Loco implements MCP protocol version `2024-11-05`.

### Tool Registration

Tools from MCP servers are automatically registered in loco's tool registry and exposed to the LLM with the same interface as built-in tools.

### Error Handling

- Connection failures are logged but don't prevent loco from starting
- Tool execution errors are returned to the LLM as error messages
- Async operations are properly managed with timeouts

## Troubleshooting

### MCP Server Won't Start

1. Check that the command is in your PATH:
   ```bash
   which npx  # or uvx
   ```

2. Test the MCP server manually:
   ```bash
   npx -y @modelcontextprotocol/server-filesystem /tmp
   ```

3. Check stderr output - MCP servers log to stderr

### Tools Not Available

1. Verify the server initialized successfully in logs
2. Check that the server supports the tools capability
3. Use `/tools` command to list available tools

### Permission Issues

1. Ensure the MCP server has necessary permissions
2. Check environment variables are set correctly
3. For filesystem servers, verify directory permissions

## Security Considerations

- **Command Execution**: MCP servers can execute arbitrary commands. Only configure servers you trust.
- **Filesystem Access**: Limit filesystem servers to specific directories.
- **API Keys**: Use environment variables (not plain text) for sensitive credentials.
- **Network Access**: Some MCP servers make network requests. Review their functionality.

## Learn More

- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [Official MCP Servers](https://github.com/modelcontextprotocol/servers)
- [Claude Desktop MCP Guide](https://docs.anthropic.com/claude/docs/model-context-protocol)

## Future Enhancements

Planned improvements to loco's MCP support:

- [ ] Web UI for managing MCP server connections
- [ ] Hot-reload MCP server configuration
- [ ] MCP server health monitoring
- [ ] Built-in MCP server discovery
- [ ] Resource and prompt support (not just tools)
- [ ] Sampling support for agentic MCP servers
