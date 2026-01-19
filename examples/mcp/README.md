# MCP Examples

This directory contains example configurations for using loco with the Model Context Protocol (MCP).

## Files

### `config-with-mcp.json`
Example loco configuration with MCP servers configured. Shows how to:
- Connect to filesystem MCP server
- Integrate with GitHub via MCP
- Connect to PostgreSQL database

Copy relevant sections to your `~/.config/loco/config.json`.

### `claude_desktop_config.json`
Configuration for Claude Desktop to use loco as an MCP server. This allows Claude Desktop to use loco's tools (read, write, edit, bash, glob, grep).

**Installation:**
1. Install loco: `pip install git+https://github.com/showdownlabs/loco.git`
2. Copy this file to:
   - macOS/Linux: `~/.config/claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
3. Restart Claude Desktop
4. Loco's tools will now be available in your Claude conversations!

## Quick Start

### 1. Run loco as MCP Server

```bash
# Test it works
loco mcp-server

# It will listen on stdin/stdout for JSON-RPC messages
# Press Ctrl+C to stop
```

### 2. Use External MCP Servers in Loco

Add to your loco config (`~/.config/loco/config.json`):

```json
{
  "mcp_servers": {
    "filesystem": {
      "command": ["npx"],
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/directory"]
    }
  }
}
```

Then start loco normally:

```bash
loco
```

The tools from the filesystem MCP server will be automatically available!

## Popular MCP Servers

### Filesystem
```bash
npx -y @modelcontextprotocol/server-filesystem /path/to/directory
```

### GitHub
```bash
# Requires GITHUB_TOKEN environment variable
npx -y @modelcontextprotocol/server-github
```

### PostgreSQL
```bash
# Requires database connection string
npx -y @modelcontextprotocol/server-postgres postgresql://localhost/mydb
```

### SQLite
```bash
npx -y @modelcontextprotocol/server-sqlite /path/to/database.db
```

### Web Fetch
```bash
npx -y @modelcontextprotocol/server-fetch
```

### Brave Search
```bash
# Requires BRAVE_API_KEY environment variable
npx -y @modelcontextprotocol/server-brave-search
```

## Testing MCP Integration

### Test as Server

1. Start loco as MCP server in one terminal:
   ```bash
   loco mcp-server
   ```

2. In another terminal, send a test request:
   ```bash
   echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | loco mcp-server
   ```

### Test as Client

1. Start a simple MCP server (e.g., filesystem)
2. Configure it in loco's config
3. Start loco and check available tools:
   ```
   $ loco
   > /tools
   ```

## Learn More

See [docs/MCP.md](../../docs/MCP.md) for complete documentation.
