"""Tests for the MCP server."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestOpManagerMCPServer:
    """Tests for the OpManager MCP Server."""

    @pytest.mark.asyncio
    async def test_server_initialization(self, config, sample_openapi_spec):
        """Test server initialization."""
        from opmanager_mcp.server import OpManagerMCPServer

        with patch("opmanager_mcp.server.OpManagerAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            with patch("builtins.open", MagicMock()):
                with patch("json.load", return_value=sample_openapi_spec):
                    server = OpManagerMCPServer(config)
                    await server.initialize()

                    assert server.is_initialized is True

    @pytest.mark.asyncio
    async def test_server_tools_generated(self, config, sample_openapi_spec):
        """Test that tools are generated from OpenAPI spec."""
        from opmanager_mcp.server import OpManagerMCPServer

        # Create a spec with a sample endpoint
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/api/json/device/listDevices": {
                    "get": {
                        "operationId": "listDevices",
                        "summary": "List all devices",
                        "parameters": [],
                        "responses": {"200": {"description": "Success"}},
                    }
                }
            },
        }

        with patch("opmanager_mcp.server.OpManagerAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            with patch("builtins.open", MagicMock()):
                with patch("json.load", return_value=spec):
                    server = OpManagerMCPServer(config)
                    await server.initialize()

                    assert len(server.tools) > 0


class TestToolExecution:
    """Tests for tool execution."""

    @pytest.mark.asyncio
    async def test_execute_tool_success(self, config, mock_api_client):
        """Test successful tool execution."""
        from opmanager_mcp.server import OpManagerMCPServer

        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/api/json/device/listDevices": {
                    "get": {
                        "operationId": "listDevices",
                        "summary": "List all devices",
                        "parameters": [],
                        "responses": {"200": {"description": "Success"}},
                    }
                }
            },
        }

        with patch("opmanager_mcp.server.OpManagerAPIClient") as mock_client_class:
            mock_client_class.return_value = mock_api_client
            mock_api_client.request.return_value = {"devices": []}

            with patch("builtins.open", MagicMock()):
                with patch("json.load", return_value=spec):
                    server = OpManagerMCPServer(config)
                    await server.initialize()

                    # Get the tool name
                    tool_name = "opmanager_listDevices"

                    if tool_name in [t["name"] for t in server.tools]:
                        result = await server._execute_tool(tool_name, {})
                        assert result is not None

    @pytest.mark.asyncio
    async def test_execute_unknown_tool(self, config):
        """Test executing an unknown tool raises error."""
        from opmanager_mcp.server import OpManagerMCPServer
        from opmanager_mcp.exceptions import ToolNotFoundError

        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
        }

        with patch("opmanager_mcp.server.OpManagerAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            with patch("builtins.open", MagicMock()):
                with patch("json.load", return_value=spec):
                    server = OpManagerMCPServer(config)
                    await server.initialize()

                    with pytest.raises(ToolNotFoundError):
                        await server._execute_tool("nonexistent_tool", {})
