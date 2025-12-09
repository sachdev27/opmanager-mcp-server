"""Tests for the API client."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestOpManagerAPIClient:
    """Tests for the OpManager API client."""

    @pytest.mark.asyncio
    async def test_client_initialization(self, config):
        """Test client initialization."""
        from opmanager_mcp.api_client import OpManagerAPIClient

        client = OpManagerAPIClient(config.opmanager)

        assert client.config == config.opmanager
        assert client._client is None

    @pytest.mark.asyncio
    async def test_client_request_includes_api_key(self, config, mock_httpx_response):
        """Test that requests include the API key."""
        from opmanager_mcp.api_client import OpManagerAPIClient

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_httpx_response)
            mock_client_class.return_value = mock_client

            client = OpManagerAPIClient(config.opmanager)
            client._client = mock_client

            await client.request("GET", "/api/json/device/listDevices")

            # Verify the request was made with API key in params
            mock_client.request.assert_called_once()
            call_kwargs = mock_client.request.call_args[1]
            assert "apiKey" in call_kwargs.get("params", {})

    @pytest.mark.asyncio
    async def test_client_get_method(self, config, mock_httpx_response):
        """Test the GET method."""
        from opmanager_mcp.api_client import OpManagerAPIClient

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_httpx_response)
            mock_client_class.return_value = mock_client

            client = OpManagerAPIClient(config.opmanager)
            client._client = mock_client

            result = await client.get("/api/json/device/listDevices")

            assert result == {"status": "success", "data": []}

    @pytest.mark.asyncio
    async def test_client_post_method(self, config, mock_httpx_response):
        """Test the POST method."""
        from opmanager_mcp.api_client import OpManagerAPIClient

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_httpx_response)
            mock_client_class.return_value = mock_client

            client = OpManagerAPIClient(config.opmanager)
            client._client = mock_client

            result = await client.post(
                "/api/json/device/addDevice",
                data={"name": "test-device"},
            )

            assert result == {"status": "success", "data": []}

    @pytest.mark.asyncio
    async def test_client_handles_error_response(self, config):
        """Test handling of error responses."""
        from opmanager_mcp.api_client import OpManagerAPIClient
        from opmanager_mcp.exceptions import APIResponseError

        error_response = MagicMock()
        error_response.status_code = 500
        error_response.text = "Internal Server Error"
        error_response.json.side_effect = ValueError("Not JSON")
        error_response.raise_for_status.side_effect = Exception("Server Error")

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=error_response)
            mock_client_class.return_value = mock_client

            client = OpManagerAPIClient(config.opmanager)
            client._client = mock_client

            with pytest.raises(Exception):
                await client.request("GET", "/api/json/device/listDevices")


class TestClientLifecycle:
    """Tests for client lifecycle management."""

    @pytest.mark.asyncio
    async def test_client_close(self, config):
        """Test closing the client."""
        from opmanager_mcp.api_client import OpManagerAPIClient

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.aclose = AsyncMock()
            mock_client_class.return_value = mock_client

            client = OpManagerAPIClient(config.opmanager)
            client._client = mock_client

            await client.close()

            mock_client.aclose.assert_called_once()
