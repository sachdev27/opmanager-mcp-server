"""Tests for configuration module."""

from __future__ import annotations


class TestOpManagerConfig:
    """Tests for OpManager configuration."""

    def test_default_config_values(self):
        """Test that default values are used when not specified."""
        from opmanager_mcp.config import OpManagerConfig

        config = OpManagerConfig()

        assert config.host == "localhost"
        assert config.port == 8060
        assert config.use_https is False
        assert config.tls_verify is False
        assert config.api_key is None

    def test_config_with_values(self):
        """Test configuration with explicit values."""
        from opmanager_mcp.config import OpManagerConfig

        config = OpManagerConfig(
            host="example.com",
            port=8061,
            use_https=True,
            api_key="test-key",
        )

        assert config.host == "example.com"
        assert config.port == 8061
        assert config.use_https is True
        assert config.api_key == "test-key"

    def test_config_from_env(self, mock_env_vars):
        """Test loading configuration from environment variables."""
        from opmanager_mcp.config import load_config

        config = load_config()

        assert config.opmanager.host == "test-host"
        assert config.opmanager.port == 8060


class TestServerConfig:
    """Tests for server configuration."""

    def test_default_server_config(self):
        """Test default server configuration values."""
        from opmanager_mcp.config import ServerConfig

        config = ServerConfig()

        assert config.port == 3000
        assert config.log_level == "INFO"
        assert config.log_json is False

    def test_server_config_allowed_methods(self):
        """Test allowed HTTP methods configuration."""
        from opmanager_mcp.config import ServerConfig

        config = ServerConfig()

        # Default should include all methods
        assert "GET" in config.allowed_http_methods
        assert isinstance(config.allowed_http_methods, list)


class TestLoadConfig:
    """Tests for the load_config function."""

    def test_load_config_complete(self, mock_env_vars):
        """Test loading complete configuration."""
        from opmanager_mcp.config import load_config

        config = load_config()

        assert config.opmanager is not None
        assert config.server is not None

    def test_load_config_with_spec_path(self, mock_env_vars):
        """Test loading config with OpenAPI spec path."""
        from opmanager_mcp.config import load_config

        # The mock_env_vars fixture sets LOCAL_OPENAPI_SPEC_PATH
        config = load_config()

        assert config.opmanager.local_spec_path is not None
