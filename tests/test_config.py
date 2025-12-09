"""Tests for configuration module."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest


class TestOpManagerConfig:
    """Tests for OpManager configuration."""

    def test_default_config_values(self, mock_env_vars):
        """Test that default values are used when not specified."""
        from opmanager_mcp.config import OpManagerConfig

        config = OpManagerConfig(api_key="test-key")

        assert config.host == "localhost"
        assert config.port == 8060
        assert config.use_ssl is False
        assert config.verify_ssl is True
        assert config.timeout == 30

    def test_config_from_env(self, mock_env_vars):
        """Test loading configuration from environment variables."""
        from opmanager_mcp.config import load_config

        config = load_config()

        assert config.opmanager.host == "test-host"
        assert config.opmanager.port == 8060
        assert config.opmanager.api_key == "test-api-key"

    def test_base_url_http(self, mock_env_vars):
        """Test base URL generation for HTTP."""
        from opmanager_mcp.config import OpManagerConfig

        config = OpManagerConfig(
            host="example.com",
            port=8060,
            use_ssl=False,
            api_key="test-key",
        )

        assert config.base_url == "http://example.com:8060"

    def test_base_url_https(self, mock_env_vars):
        """Test base URL generation for HTTPS."""
        from opmanager_mcp.config import OpManagerConfig

        config = OpManagerConfig(
            host="example.com",
            port=443,
            use_ssl=True,
            api_key="test-key",
        )

        assert config.base_url == "https://example.com:443"


class TestServerConfig:
    """Tests for server configuration."""

    def test_default_server_config(self, mock_env_vars):
        """Test default server configuration values."""
        from opmanager_mcp.config import ServerConfig

        config = ServerConfig()

        assert config.name == "opmanager-mcp-server"
        assert config.log_level == "INFO"
        assert config.log_json is False


class TestLoadConfig:
    """Tests for the load_config function."""

    def test_load_config_complete(self, mock_env_vars):
        """Test loading complete configuration."""
        from opmanager_mcp.config import load_config

        config = load_config()

        assert config.opmanager is not None
        assert config.server is not None
        assert config.opmanager.api_key == "test-api-key"

    def test_load_config_missing_api_key(self):
        """Test that missing API key raises an error."""
        from opmanager_mcp.config import load_config
        from pydantic import ValidationError

        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValidationError):
                load_config()
