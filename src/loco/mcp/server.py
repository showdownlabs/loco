"""MCP Server implementation that exposes loco's tools."""

import asyncio
import sys
from typing import Any
from loco.mcp.protocol import (
    MCP_VERSION,
    MCPRequest,
    MCPResponse,
    MCPNotification,
    InitializeResult,
    ToolInfo,
    CallToolParams,
    ToolResult,
)
from loco.mcp.transport import MCPTransport, StdioTransport
from loco.tools import tool_registry, Tool


class MCPServer:
    """MCP server that exposes loco's tools to MCP clients."""

    def __init__(
        self,
        transport: MCPTransport | None = None,
        name: str = "loco",
        version: str = "0.1.0",
    ):
        self.transport = transport or StdioTransport()
        self.name = name
        self.version = version
        self._initialized = False
        self._request_handlers: dict[str, Any] = {
            "initialize": self._handle_initialize,
            "tools/list": self._handle_list_tools,
            "tools/call": self._handle_call_tool,
        }

    def register_tool(self, tool: Tool) -> None:
        """Register a tool to be exposed via MCP."""
        tool_registry.register(tool)

    async def _handle_initialize(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle initialize request."""
        self._initialized = True
        
        result = InitializeResult(
            protocolVersion=MCP_VERSION,
            capabilities={
                "tools": {},  # We support tools
            },
            serverInfo={
                "name": self.name,
                "version": self.version,
            },
        )
        
        return result.model_dump()

    async def _handle_list_tools(self, params: dict[str, Any] | None) -> dict[str, Any]:
        """Handle tools/list request."""
        if not self._initialized:
            raise RuntimeError("Server not initialized")
        
        tools = tool_registry.get_all()
        tool_infos = []
        
        for tool in tools:
            tool_info = ToolInfo(
                name=tool.name,
                description=tool.description,
                inputSchema=tool.parameters,
            )
            tool_infos.append(tool_info.model_dump())
        
        return {"tools": tool_infos}

    async def _handle_call_tool(self, params: dict[str, Any]) -> dict[str, Any]:
        """Handle tools/call request."""
        if not self._initialized:
            raise RuntimeError("Server not initialized")
        
        call_params = CallToolParams(**params)
        tool = tool_registry.get(call_params.name)
        
        if tool is None:
            result = ToolResult(
                content=[{
                    "type": "text",
                    "text": f"Error: Unknown tool '{call_params.name}'"
                }],
                isError=True,
            )
            return result.model_dump()
        
        try:
            # Execute the tool
            arguments = call_params.arguments or {}
            output = tool.execute(**arguments)
            
            result = ToolResult(
                content=[{
                    "type": "text",
                    "text": output,
                }],
                isError=False,
            )
            return result.model_dump()
        
        except Exception as e:
            result = ToolResult(
                content=[{
                    "type": "text",
                    "text": f"Error executing {call_params.name}: {str(e)}"
                }],
                isError=True,
            )
            return result.model_dump()

    async def _handle_request(self, request: dict[str, Any]) -> dict[str, Any] | None:
        """Handle an incoming request."""
        try:
            req = MCPRequest(**request)
            handler = self._request_handlers.get(req.method)
            
            if handler is None:
                # Method not found
                return {
                    "jsonrpc": "2.0",
                    "id": req.id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {req.method}",
                    },
                }
            
            # Call the handler
            result = await handler(req.params or {})
            
            return {
                "jsonrpc": "2.0",
                "id": req.id,
                "result": result,
            }
        
        except Exception as e:
            # Log error to stderr (stdout is for JSON-RPC)
            sys.stderr.write(f"Error handling request: {e}\n")
            sys.stderr.flush()
            
            return {
                "jsonrpc": "2.0",
                "id": request.get("id", 0),
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}",
                },
            }

    async def run(self) -> None:
        """Run the MCP server (receive and handle requests)."""
        try:
            async for message in self.transport.receive():
                # Check if it's a notification (no id) or request (has id)
                if "id" not in message:
                    # It's a notification, we don't respond
                    # (could handle notifications like initialized, etc.)
                    continue
                
                # Handle request and send response
                response = await self._handle_request(message)
                if response:
                    await self.transport.send(response)
        
        except Exception as e:
            sys.stderr.write(f"Server error: {e}\n")
            sys.stderr.flush()
        
        finally:
            await self.transport.close()

    async def start(self) -> None:
        """Start the server (alias for run)."""
        await self.run()
