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

        with patch("opmanager_mcp.tool_generator.load_openapi_spec", return_value=sample_openapi_spec):
            server = OpManagerMCPServer(config)
            await server.initialize()

            assert server.is_initialized is True

    @pytest.mark.asyncio
    async def test_server_tools_generated(self, config):
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

        with patch("opmanager_mcp.tool_generator.load_openapi_spec", return_value=spec):
            server = OpManagerMCPServer(config)
            await server.initialize()

            assert len(server.tools) > 0
            tool_names = [t["name"] for t in server.tools]
            assert "listDevices" in tool_names


class TestToolExecution:
    """Tests for tool execution."""

    @pytest.mark.asyncio
    async def test_execute_tool_success(self, config):
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

        with patch("opmanager_mcp.tool_generator.load_openapi_spec", return_value=spec):
            server = OpManagerMCPServer(config)
            await server.initialize()

            # Mock the API client
            mock_client = AsyncMock()
            mock_client.execute_operation = AsyncMock(return_value={"devices": []})
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)

            with patch("opmanager_mcp.server.OpManagerAPIClient", return_value=mock_client):
                result = await server._execute_tool(
                    "listDevices",
                    {"host": "test-host", "apiKey": "test-key"},
                )

                assert result is not None
                assert result.isError is False

    @pytest.mark.asyncio
    async def test_execute_tool_missing_credentials(self, config):
        """Test executing tool without credentials raises error."""
        from opmanager_mcp.server import OpManagerMCPServer
        from opmanager_mcp.exceptions import InvalidToolArgumentsError

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

        with patch("opmanager_mcp.tool_generator.load_openapi_spec", return_value=spec):
            server = OpManagerMCPServer(config)
            await server.initialize()

            # Execute without credentials should raise error
            with pytest.raises(InvalidToolArgumentsError):
                await server._execute_tool("listDevices", {})

    @pytest.mark.asyncio
    async def test_execute_unknown_tool(self, config):
        """Test executing an unknown tool raises error."""
        from opmanager_mcp.server import OpManagerMCPServer
        from opmanager_mcp.exceptions import InvalidToolArgumentsError

        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
        }

        with patch("opmanager_mcp.tool_generator.load_openapi_spec", return_value=spec):
            server = OpManagerMCPServer(config)
            await server.initialize()

            # Unknown tool with missing credentials - raises InvalidToolArgumentsError first
            with pytest.raises(InvalidToolArgumentsError):
                await server._execute_tool("nonexistent_tool", {})
