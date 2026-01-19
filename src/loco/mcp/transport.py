"""Transport layer for MCP communication."""

import sys
import json
import asyncio
from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Callable
from collections.abc import Awaitable


class MCPTransport(ABC):
    """Abstract base class for MCP transports."""

    @abstractmethod
    async def send(self, message: dict[str, Any]) -> None:
        """Send a message."""
        ...

    @abstractmethod
    async def receive(self) -> AsyncIterator[dict[str, Any]]:
        """Receive messages as an async iterator."""
        ...

    @abstractmethod
    async def close(self) -> None:
        """Close the transport."""
        ...


class StdioTransport(MCPTransport):
    """STDIO transport for MCP (primary method for MCP servers)."""

    def __init__(self):
        self._closed = False
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None

    async def _setup(self) -> None:
        """Setup stdio streams."""
        if self._reader is None:
            loop = asyncio.get_event_loop()
            self._reader = asyncio.StreamReader()
            protocol = asyncio.StreamReaderProtocol(self._reader)
            await loop.connect_read_pipe(lambda: protocol, sys.stdin)
            
            # For writing, we use stdout
            self._writer = None  # We'll write directly to stdout

    async def send(self, message: dict[str, Any]) -> None:
        """Send a JSON-RPC message to stdout."""
        if self._closed:
            raise RuntimeError("Transport is closed")
        
        # MCP uses JSON-RPC over stdio with newline delimiters
        json_str = json.dumps(message)
        sys.stdout.write(json_str + "\n")
        sys.stdout.flush()

    async def receive(self) -> AsyncIterator[dict[str, Any]]:
        """Receive JSON-RPC messages from stdin."""
        await self._setup()
        
        if self._reader is None:
            raise RuntimeError("Reader not initialized")
        
        while not self._closed:
            try:
                line = await self._reader.readline()
                if not line:
                    break
                
                line_str = line.decode('utf-8').strip()
                if line_str:
                    yield json.loads(line_str)
            except Exception as e:
                # Log error and continue
                sys.stderr.write(f"Error receiving message: {e}\n")
                sys.stderr.flush()
                break

    async def close(self) -> None:
        """Close the transport."""
        self._closed = True


class SSETransport(MCPTransport):
    """Server-Sent Events transport for MCP (for HTTP-based connections)."""

    def __init__(self, endpoint: str):
        self.endpoint = endpoint
        self._closed = False
        self._send_queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._receive_queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._session = None

    async def send(self, message: dict[str, Any]) -> None:
        """Send a message via POST."""
        if self._closed:
            raise RuntimeError("Transport is closed")
        
        # In SSE, client sends via POST to a specific endpoint
        # This is a simplified implementation
        await self._send_queue.put(message)

    async def receive(self) -> AsyncIterator[dict[str, Any]]:
        """Receive messages via SSE stream."""
        # This is a placeholder - full implementation would use aiohttp
        # to connect to an SSE endpoint and parse the event stream
        while not self._closed:
            try:
                message = await asyncio.wait_for(
                    self._receive_queue.get(), 
                    timeout=30.0
                )
                yield message
            except asyncio.TimeoutError:
                continue
            except Exception:
                break

    async def close(self) -> None:
        """Close the transport."""
        self._closed = True
        if self._session:
            await self._session.close()


class ProcessTransport(MCPTransport):
    """Transport that spawns and communicates with an MCP server process."""

    def __init__(self, command: list[str], cwd: str | None = None):
        self.command = command
        self.cwd = cwd
        self._process: asyncio.subprocess.Process | None = None
        self._closed = False

    async def _ensure_process(self) -> None:
        """Ensure the process is running."""
        if self._process is None:
            self._process = await asyncio.create_subprocess_exec(
                *self.command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.cwd,
            )

    async def send(self, message: dict[str, Any]) -> None:
        """Send a message to the process stdin."""
        if self._closed:
            raise RuntimeError("Transport is closed")
        
        await self._ensure_process()
        
        if self._process is None or self._process.stdin is None:
            raise RuntimeError("Process stdin not available")
        
        json_str = json.dumps(message) + "\n"
        self._process.stdin.write(json_str.encode('utf-8'))
        await self._process.stdin.drain()

    async def receive(self) -> AsyncIterator[dict[str, Any]]:
        """Receive messages from the process stdout."""
        await self._ensure_process()
        
        if self._process is None or self._process.stdout is None:
            raise RuntimeError("Process stdout not available")
        
        while not self._closed:
            try:
                line = await self._process.stdout.readline()
                if not line:
                    break
                
                line_str = line.decode('utf-8').strip()
                if line_str:
                    yield json.loads(line_str)
            except Exception as e:
                sys.stderr.write(f"Error receiving from process: {e}\n")
                sys.stderr.flush()
                break

    async def close(self) -> None:
        """Close the transport and terminate the process."""
        self._closed = True
        
        if self._process:
            if self._process.stdin:
                self._process.stdin.close()
                await self._process.stdin.wait_closed()
            
            try:
                await asyncio.wait_for(self._process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                self._process.terminate()
                try:
                    await asyncio.wait_for(self._process.wait(), timeout=2.0)
                except asyncio.TimeoutError:
                    self._process.kill()
                    await self._process.wait()
