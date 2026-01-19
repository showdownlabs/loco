"""MCP protocol types and message definitions."""

from typing import Any, Literal
from pydantic import BaseModel, Field


# Protocol version
MCP_VERSION = "2024-11-05"


class MCPRequest(BaseModel):
    """Base MCP request."""
    jsonrpc: str = "2.0"
    id: str | int
    method: str
    params: dict[str, Any] | None = None


class MCPResponse(BaseModel):
    """Base MCP response."""
    jsonrpc: str = "2.0"
    id: str | int
    result: dict[str, Any] | None = None
    error: dict[str, Any] | None = None


class MCPNotification(BaseModel):
    """Base MCP notification (no id, no response expected)."""
    jsonrpc: str = "2.0"
    method: str
    params: dict[str, Any] | None = None


# Initialize request/response
class InitializeParams(BaseModel):
    """Parameters for initialize request."""
    protocolVersion: str
    capabilities: dict[str, Any]
    clientInfo: dict[str, str]


class InitializeResult(BaseModel):
    """Result for initialize response."""
    protocolVersion: str
    capabilities: dict[str, Any]
    serverInfo: dict[str, str]


# Tool types
class ToolInfo(BaseModel):
    """Information about a tool."""
    name: str
    description: str
    inputSchema: dict[str, Any] = Field(
        description="JSON Schema for the tool's input"
    )


class CallToolParams(BaseModel):
    """Parameters for tools/call request."""
    name: str
    arguments: dict[str, Any] | None = None


class ToolResult(BaseModel):
    """Result of a tool execution."""
    content: list[dict[str, Any]]
    isError: bool = False


# Resource types
class ResourceInfo(BaseModel):
    """Information about a resource."""
    uri: str
    name: str
    description: str | None = None
    mimeType: str | None = None


class ReadResourceParams(BaseModel):
    """Parameters for resources/read request."""
    uri: str


class ResourceContent(BaseModel):
    """Content of a resource."""
    uri: str
    mimeType: str | None = None
    text: str | None = None
    blob: str | None = None  # base64 encoded


# Prompt types
class PromptInfo(BaseModel):
    """Information about a prompt."""
    name: str
    description: str | None = None
    arguments: list[dict[str, Any]] | None = None


class GetPromptParams(BaseModel):
    """Parameters for prompts/get request."""
    name: str
    arguments: dict[str, Any] | None = None


class PromptMessage(BaseModel):
    """A message in a prompt."""
    role: Literal["user", "assistant"]
    content: dict[str, Any]


class PromptResult(BaseModel):
    """Result of getting a prompt."""
    description: str | None = None
    messages: list[PromptMessage]


# Logging types
class LoggingLevel(BaseModel):
    """Logging level."""
    level: Literal["debug", "info", "warning", "error"]


class LogEntry(BaseModel):
    """A log entry."""
    level: Literal["debug", "info", "warning", "error"]
    logger: str | None = None
    data: Any
