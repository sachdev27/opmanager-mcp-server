"""Tests for the API client."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestOpManagerAPIClient:
    """Tests for the OpManager API client."""

    @pytest.mark.asyncio
    async def test_client_initialization(self):
        """Test client initialization with direct parameters."""
        from opmanager_mcp.api_client import OpManagerAPIClient

        client = OpManagerAPIClient(
            host="test-host",
            api_key="test-api-key",
            port=8060,
            use_https=False,
        )

        assert client.host == "test-host"
        assert client.api_key == "test-api-key"
        assert client.port == 8060
        assert client.base_url == "http://test-host:8060"

    @pytest.mark.asyncio
    async def test_client_initialization_https(self):
        """Test client initialization with HTTPS."""
        from opmanager_mcp.api_client import OpManagerAPIClient

        client = OpManagerAPIClient(
            host="test-host",
            api_key="test-api-key",
            port=8061,
            use_https=True,
        )

        assert client.base_url == "https://test-host:8061"

    @pytest.mark.asyncio
    async def test_client_missing_host_raises_error(self):
        """Test that missing host raises ValueError."""
        from opmanager_mcp.api_client import OpManagerAPIClient

        with pytest.raises(ValueError, match="host is required"):
            OpManagerAPIClient(host="", api_key="test-key")

    @pytest.mark.asyncio
    async def test_client_missing_api_key_raises_error(self):
        """Test that missing api_key raises ValueError."""
        from opmanager_mcp.api_client import OpManagerAPIClient

        with pytest.raises(ValueError, match="api_key is required"):
            OpManagerAPIClient(host="test-host", api_key="")

    @pytest.mark.asyncio
    async def test_client_context_manager(self):
        """Test using client as async context manager."""
        from opmanager_mcp.api_client import OpManagerAPIClient

        async with OpManagerAPIClient(
            host="test-host",
            api_key="test-key",
        ) as client:
            assert client is not None
            # Client should be initialized after entering context
            # The client attribute is created lazily via _ensure_client

    @pytest.mark.asyncio
    async def test_client_execute_operation(self):
        """Test executing an API operation."""
        from opmanager_mcp.api_client import OpManagerAPIClient

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success", "data": []}
        mock_response.headers = {"content-type": "application/json"}

        client = OpManagerAPIClient(
            host="test-host",
            api_key="test-key",
        )

        # Mock the internal method that makes requests
        with patch.object(
            client, "_make_request", new_callable=AsyncMock
        ) as mock_make_request:
            mock_make_request.return_value = mock_response

            # Ensure client is initialized
            client.client = MagicMock()

            result = await client.execute_operation(
                path="/api/json/device/listDevices",
                method="GET",
            )

            assert result == {"status": "success", "data": []}


class TestClientLifecycle:
    """Tests for client lifecycle management."""

    @pytest.mark.asyncio
    async def test_client_close(self):
        """Test closing the client."""
        from opmanager_mcp.api_client import OpManagerAPIClient

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.aclose = AsyncMock()
            mock_client_class.return_value = mock_client

            client = OpManagerAPIClient(
                host="test-host",
                api_key="test-key",
            )
            client.client = mock_client

            await client.close()

            mock_client.aclose.assert_called_once()
