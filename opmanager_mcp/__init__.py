"""OpManager Plus MCP Server - API key authentication with per-request host support.

This package provides a Model Context Protocol (MCP) server for ManageEngine
OpManager Plus network monitoring systems. It automatically generates tools
from OpenAPI specifications and supports both stdio and HTTP/SSE transports.

Features:
    - Automatic tool generation from OpenAPI specs
    - API key authentication with per-request host support
    - Multi-host support for managing multiple OpManager instances
    - Read-only GET operations for safe diagnostics (configurable)
    - SSE transport for n8n and web clients
    - stdio transport for Claude Desktop

Example:
    Using as a CLI tool (stdio transport)::

        $ python -m opmanager_mcp

    Using as HTTP server (SSE transport)::

        $ uvicorn opmanager_mcp.http_server:app --host 0.0.0.0 --port 3000

    Using as a library::

        from opmanager_mcp.config import load_config
        from opmanager_mcp.server import OpManagerMCPServer

        config = load_config()
        server = OpManagerMCPServer(config)
        await server.initialize()

Attributes:
    __version__: Package version following semantic versioning.
    __author__: Package author/maintainer.
"""

__version__ = "1.0.0"
__author__ = "sachdev27"
__all__ = [
    "__version__",
    "__author__",
    "OpManagerMCPServer",
    "OpManagerAPIClient",
    "Config",
    "load_config",
]

# Lazy imports to avoid circular dependencies
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .api_client import OpManagerAPIClient
    from .config import Config, load_config
    from .server import OpManagerMCPServer
