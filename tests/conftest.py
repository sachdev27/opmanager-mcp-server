"""Pytest configuration and fixtures."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

# Add the parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def sample_openapi_spec() -> dict[str, Any]:
    """Load the sample OpenAPI spec for testing."""
    spec_path = Path(__file__).parent.parent / "openapi.json"
    if spec_path.exists():
        with open(spec_path) as f:
            return json.load(f)
    # Return minimal spec if file doesn't exist
    return {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {},
    }


@pytest.fixture
def mock_env_vars() -> Generator[dict[str, str], None, None]:
    """Set up mock environment variables."""
    env_vars = {
        "OPMANAGER_HOST": "test-host",
        "OPMANAGER_PORT": "8060",
        "OPMANAGER_USE_SSL": "false",
        "OPMANAGER_API_KEY": "test-api-key",
        "OPMANAGER_VERIFY_SSL": "false",
        "OPMANAGER_TIMEOUT": "30",
        "MCP_SERVER_LOG_LEVEL": "DEBUG",
    }

    with patch.dict(os.environ, env_vars, clear=False):
        yield env_vars


@pytest.fixture
def config(mock_env_vars: dict[str, str]):
    """Create a test configuration."""
    from opmanager_mcp.config import load_config
    return load_config()


@pytest_asyncio.fixture
async def mock_api_client() -> AsyncGenerator[AsyncMock, None]:
    """Create a mock API client."""
    client = AsyncMock()
    client.request = AsyncMock(return_value={"status": "success"})
    client.get = AsyncMock(return_value={"status": "success"})
    client.post = AsyncMock(return_value={"status": "success"})
    client.close = AsyncMock()
    yield client


@pytest.fixture
def mock_httpx_response() -> MagicMock:
    """Create a mock httpx response."""
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {"status": "success", "data": []}
    response.text = '{"status": "success", "data": []}'
    response.headers = {"content-type": "application/json"}
    response.raise_for_status = MagicMock()
    return response
