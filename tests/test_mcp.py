#!/usr/bin/env python3
"""Test script for MCP functionality."""

import asyncio
import json
import sys
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from loco.mcp.server import MCPServer
from loco.mcp.client import MCPClient
from loco.mcp.transport import ProcessTransport
from loco.tools import ReadTool, WriteTool, BashTool


async def test_server():
    """Test MCP server functionality."""
    print("Testing MCP Server...")
    
    from loco.tools import tool_registry
    
    # Create server and register tools
    server = MCPServer(name="test-loco", version="0.1.0")
    
    # Register tools in the global registry
    read_tool = ReadTool()
    write_tool = WriteTool()
    bash_tool = BashTool()
    tool_registry.register(read_tool)
    tool_registry.register(write_tool)
    tool_registry.register(bash_tool)
    
    # Test initialize
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "1.0"}
        }
    }
    
    response = await server._handle_request(init_request)
    assert response["id"] == 1
    assert "result" in response
    assert response["result"]["serverInfo"]["name"] == "test-loco"
    print("✓ Initialize works")
    
    # Test list tools
    list_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }
    
    response = await server._handle_request(list_request)
    assert response["id"] == 2
    assert "result" in response
    tools = response["result"]["tools"]
    print(f"DEBUG: Found {len(tools)} tools: {[t['name'] for t in tools]}")
    # The global registry may have other tools already registered
    # So let's just check our tools are present
    tool_names = [t["name"] for t in tools]
    assert "read" in tool_names
    assert "write" in tool_names
    assert "bash" in tool_names
    print("✓ List tools works")
    
    # Test call tool
    call_request = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "bash",
            "arguments": {"command": "echo 'Hello MCP'"}
        }
    }
    
    response = await server._handle_request(call_request)
    assert response["id"] == 3
    assert "result" in response
    content = response["result"]["content"]
    assert len(content) > 0
    assert "Hello MCP" in content[0]["text"]
    print("✓ Call tool works")
    
    print("\n✅ MCP Server tests passed!\n")


async def test_protocol():
    """Test MCP protocol types."""
    print("Testing MCP Protocol...")
    
    from loco.mcp.protocol import (
        MCPRequest, MCPResponse, ToolInfo, CallToolParams, ToolResult
    )
    
    # Test request
    req = MCPRequest(
        id=1,
        method="tools/list",
        params={"test": "value"}
    )
    assert req.jsonrpc == "2.0"
    assert req.method == "tools/list"
    print("✓ MCPRequest works")
    
    # Test response
    resp = MCPResponse(
        id=1,
        result={"tools": []}
    )
    assert resp.jsonrpc == "2.0"
    print("✓ MCPResponse works")
    
    # Test tool info
    tool = ToolInfo(
        name="test",
        description="A test tool",
        inputSchema={"type": "object", "properties": {}}
    )
    assert tool.name == "test"
    print("✓ ToolInfo works")
    
    # Test call params
    params = CallToolParams(
        name="bash",
        arguments={"command": "ls"}
    )
    assert params.name == "bash"
    print("✓ CallToolParams works")
    
    # Test tool result
    result = ToolResult(
        content=[{"type": "text", "text": "output"}],
        isError=False
    )
    assert not result.isError
    print("✓ ToolResult works")
    
    print("\n✅ MCP Protocol tests passed!\n")


async def test_client_server_integration():
    """Test MCP client-server integration."""
    print("Testing MCP Client-Server Integration...")
    
    # Note: This test requires a running MCP server process
    # For now, we just test that the client can be instantiated
    
    from loco.mcp.client import MCPClient, MCPClientTool
    from loco.mcp.protocol import ToolInfo
    
    # Create a mock client (no real transport)
    class MockTransport:
        async def send(self, msg):
            pass
        async def receive(self):
            yield {"jsonrpc": "2.0", "id": 1, "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "serverInfo": {"name": "mock", "version": "1.0"}
            }}
        async def close(self):
            pass
    
    client = MCPClient(MockTransport())
    print("✓ Client instantiation works")
    
    # Test tool wrapper
    tool_info = ToolInfo(
        name="test_tool",
        description="Test tool",
        inputSchema={"type": "object"}
    )
    client._tools["test_tool"] = tool_info
    
    tool_wrapper = client.get_tool("test_tool")
    assert tool_wrapper is not None
    assert tool_wrapper.name == "test_tool"
    print("✓ Client tool wrapper works")
    
    print("\n✅ MCP Integration tests passed!\n")


async def main():
    """Run all tests."""
    print("=" * 60)
    print("MCP Test Suite")
    print("=" * 60)
    print()
    
    try:
        await test_protocol()
        await test_server()
        await test_client_server_integration()
        
        print("=" * 60)
        print("✅ All MCP tests passed!")
        print("=" * 60)
        return 0
    
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
