"""Tests for the HTTP server."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestMCPHttpServer:
    """Tests for the MCP HTTP Server."""

    @pytest.mark.asyncio
    async def test_server_initialization(self):
        """Test server initialization."""
        from opmanager_mcp.http_server import MCPHttpServer

        server = MCPHttpServer()
        assert server._initialized is False
        assert server.mcp_server is None

    @pytest.mark.asyncio
    async def test_server_health_endpoint(self, mock_env_vars):
        """Test health check endpoint."""
        from opmanager_mcp.http_server import MCPHttpServer

        server = MCPHttpServer()
        
        # Mock initialize to avoid loading actual spec
        with patch.object(server, "initialize", new_callable=AsyncMock) as mock_init:
            server._initialized = True
            server.mcp_server = MagicMock()
            server.mcp_server.tools = [{"name": "test"}]

            # Create mock ASGI components
            scope = {"type": "http", "path": "/health", "method": "GET"}
            receive = AsyncMock()
            
            # Capture what gets sent
            sent_messages = []
            async def send(message):
                sent_messages.append(message)
            
            await server._handle_health(scope, receive, send)
            
            # Check response was sent
            assert len(sent_messages) == 2
            assert sent_messages[0]["type"] == "http.response.start"
            assert sent_messages[0]["status"] == 200
            
            # Parse body
            body = json.loads(sent_messages[1]["body"])
            assert body["status"] == "healthy"
            assert body["tool_count"] == 1

    @pytest.mark.asyncio
    async def test_server_tools_endpoint(self, mock_env_vars):
        """Test tools list endpoint."""
        from opmanager_mcp.http_server import MCPHttpServer

        server = MCPHttpServer()
        server._initialized = True
        server.mcp_server = MagicMock()
        server.mcp_server.tools = [
            {"name": "listDevices", "description": "List all devices", "inputSchema": {}},
            {"name": "listAlarms", "description": "List all alarms", "inputSchema": {}},
        ]

        scope = {"type": "http", "path": "/tools", "method": "GET"}
        receive = AsyncMock()
        
        sent_messages = []
        async def send(message):
            sent_messages.append(message)
        
        await server._handle_tools(scope, receive, send)
        
        body = json.loads(sent_messages[1]["body"])
        assert body["count"] == 2
        assert len(body["tools"]) == 2

    @pytest.mark.asyncio
    async def test_server_call_endpoint(self, mock_env_vars):
        """Test direct tool call endpoint."""
        from opmanager_mcp.http_server import MCPHttpServer
        import mcp.types as types

        server = MCPHttpServer()
        server._initialized = True
        server.mcp_server = MagicMock()
        
        # Mock the _execute_tool method
        mock_result = types.CallToolResult(
            content=[types.TextContent(type="text", text='{"devices": []}')],
            isError=False,
        )
        server.mcp_server._execute_tool = AsyncMock(return_value=mock_result)

        # Create request body
        request_body = json.dumps({
            "name": "listDevices",
            "arguments": {"host": "test", "apiKey": "key"}
        }).encode()

        scope = {"type": "http", "path": "/call", "method": "POST"}
        
        # Mock receive to return the body
        receive_calls = 0
        async def receive():
            nonlocal receive_calls
            receive_calls += 1
            if receive_calls == 1:
                return {"body": request_body, "more_body": False}
            return {}
        
        sent_messages = []
        async def send(message):
            sent_messages.append(message)
        
        await server._handle_call(scope, receive, send)
        
        body = json.loads(sent_messages[1]["body"])
        assert body["isError"] is False
        assert len(body["content"]) == 1


class TestCORSMiddleware:
    """Tests for CORS middleware."""

    @pytest.mark.asyncio
    async def test_cors_preflight(self):
        """Test CORS preflight request handling."""
        from opmanager_mcp.http_server import CORSMiddleware

        # Create a simple test app
        async def test_app(scope, receive, send):
            pass

        middleware = CORSMiddleware(test_app)

        scope = {"type": "http", "path": "/sse", "method": "OPTIONS"}
        receive = AsyncMock()
        
        sent_messages = []
        async def send(message):
            sent_messages.append(message)
        
        await middleware(scope, receive, send)
        
        # Should send 204 with CORS headers
        assert sent_messages[0]["status"] == 204
        headers = dict(sent_messages[0]["headers"])
        assert b"access-control-allow-origin" in headers

    @pytest.mark.asyncio
    async def test_cors_headers_added(self):
        """Test CORS headers are added to responses."""
        from opmanager_mcp.http_server import CORSMiddleware

        # Track if app was called
        app_called = False
        
        async def test_app(scope, receive, send):
            nonlocal app_called
            app_called = True
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body", "body": b"test"})

        middleware = CORSMiddleware(test_app)

        scope = {"type": "http", "path": "/health", "method": "GET"}
        receive = AsyncMock()
        
        sent_messages = []
        async def send(message):
            sent_messages.append(message)
        
        await middleware(scope, receive, send)
        
        assert app_called
        # Check CORS headers were added
        headers = dict(sent_messages[0]["headers"])
        assert b"access-control-allow-origin" in headers
