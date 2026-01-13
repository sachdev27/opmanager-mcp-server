"""MCP server implementation for OpManager - Credential-free mode.

This module provides the core MCP server that handles tool registration
and execution for OpManager operations.

Example:
    >>> from opmanager_mcp.config import load_config
    >>> from opmanager_mcp.server import OpManagerMCPServer
    >>>
    >>> config = load_config()
    >>> server = OpManagerMCPServer(config)
    >>> await server.initialize()
    >>> print(f"Server ready with {len(server.tools)} tools")
"""

from __future__ import annotations

import json
from typing import Any

import mcp.types as types
from mcp.server.lowlevel import Server

from .api_client import OpManagerAPIClient
from .config import Config
from .exceptions import (
    InvalidToolArgumentsError,
    OpenAPILoadError,
    OpManagerAPIError,
    ToolNotFoundError,
)
from .logging_config import get_logger
from .tool_generator import ToolGenerator, load_openapi_spec

logger = get_logger(__name__)

# Parameters to exclude from API calls (MCP/n8n metadata)
EXCLUDED_PARAMS: frozenset[str] = frozenset(
    {
        # Credentials and connection settings (handled separately)
        "host",
        "apiKey",
        "api_key",
        "port",
        "use_ssl",
        "verify_ssl",
        # Our custom query params wrapper
        "queryParams",
        # n8n/MCP metadata that should never go to OpManager
        "sessionId",
        "session_id",
        "action",
        "chatInput",
        "chat_input",
        "toolCallId",
        "tool_call_id",
        "tool",
        "toolName",
        "tool_name",
        # Other potential metadata
        "requestId",
        "request_id",
        "messageId",
        "message_id",
    }
)


class OpManagerMCPServer:
    """OpManager MCP Server with credential-free initialization.

    This server loads tool definitions from an OpenAPI spec at startup
    but doesn't connect to any OpManager system. Authentication
    happens per-request when tools are called.

    Attributes:
        config: Server configuration.
        server: Underlying MCP server instance.
        tools: List of generated tool definitions.
        tool_generator: Tool generator instance.

    Example:
        >>> server = OpManagerMCPServer(config)
        >>> await server.initialize()
        >>> # Server is now ready to handle tool calls
    """

    def __init__(self, config: Config) -> None:
        """Initialize OpManager MCP Server.

        Args:
            config: Server configuration object.
        """
        self.config = config
        self.server = Server("opmanager-mcp-server")

        self.tools: list[dict[str, Any]] = []
        self.tool_generator: ToolGenerator | None = None
        self._initialized = False

        # Register handlers
        self._setup_handlers()

    @property
    def is_initialized(self) -> bool:
        """Check if the server has been initialized.

        Returns:
            True if initialized, False otherwise.
        """
        return self._initialized

    async def initialize(self) -> None:
        """Initialize server by loading OpenAPI spec and generating tools.

        This method loads the OpenAPI specification and generates MCP tools.
        It does NOT connect to OpManager - authentication happens per-request.

        Raises:
            OpenAPILoadError: If the OpenAPI spec cannot be loaded.
            ConfigurationError: If required configuration is missing.
        """
        if self._initialized:
            logger.debug("Server already initialized, skipping")
            return

        logger.info("Initializing MCP server (credential-free mode)")

        # Load OpenAPI spec from local file
        spec_path = self.config.opmanager.local_spec_path
        if not spec_path:
            raise OpenAPILoadError(
                "unknown",
                message="LOCAL_OPENAPI_SPEC_PATH not configured",
            )

        logger.info(f"Loading OpenAPI spec from {spec_path}")
        try:
            spec = load_openapi_spec(spec_path)
        except Exception as e:
            raise OpenAPILoadError(spec_path, e) from e

        # Generate tools (only for configured HTTP methods)
        logger.info("Generating MCP tools from OpenAPI spec")
        allowed_methods = self.config.server.allowed_http_methods
        self.tool_generator = ToolGenerator(spec, allowed_methods=allowed_methods)
        self.tools = self.tool_generator.generate_tools()

        self._initialized = True
        logger.info(
            "MCP server initialized successfully",
            extra={
                "mode": "credential-free",
                "tool_count": len(self.tools),
            },
        )

    def _setup_handlers(self) -> None:
        """Set up MCP protocol handlers."""

        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            """List all available tools.

            Returns:
                List of MCP tool definitions.
            """
            logger.debug(f"Listing {len(self.tools)} tools")
            return [
                types.Tool(
                    name=tool["name"],
                    description=tool["description"],
                    inputSchema=tool["inputSchema"],
                )
                for tool in self.tools
            ]

        @self.server.call_tool()
        async def handle_call_tool(
            name: str,
            arguments: dict[str, Any] | None,
        ) -> types.CallToolResult:
            """Execute a tool with per-request credentials.

            Per MCP spec, tool execution errors are returned with isError=True
            rather than raised as exceptions. This allows the LLM to understand
            the error and potentially self-correct.

            Args:
                name: Tool name.
                arguments: Tool arguments including host, apiKey.

            Returns:
                CallToolResult with content and isError flag.

            Note:
                Protocol errors (invalid params, unknown tool) are still raised
                as exceptions per MCP spec. Tool execution errors return isError=True.
            """
            return await self._execute_tool(name, arguments)

    async def _execute_tool(
        self,
        name: str,
        arguments: dict[str, Any] | None,
    ) -> types.CallToolResult:
        """Execute a tool with the given arguments.

        Per MCP spec, this method distinguishes between:
        - Protocol errors (invalid params, unknown tool): Raised as exceptions
        - Tool execution errors (API failures): Returned with isError=True

        Args:
            name: Tool name.
            arguments: Tool arguments.

        Returns:
            CallToolResult with content and isError flag.

        Raises:
            InvalidToolArgumentsError: If required arguments are missing (protocol error).
            ToolNotFoundError: If the tool doesn't exist (protocol error).
        """
        if not arguments:
            raise InvalidToolArgumentsError(
                name,
                missing_args=["host", "apiKey"],
            )

        # Extract and validate credentials
        host = arguments.get("host")
        api_key = arguments.get("apiKey") or arguments.get("api_key")
        port = arguments.get("port", self.config.opmanager.port)

        # SSL settings - auto-detect from port if not specified
        use_ssl = arguments.get("use_ssl")
        if use_ssl is None:
            # Auto-detect: port 8061 typically uses HTTPS, 8060 uses HTTP
            use_ssl = port == 8061 if port else self.config.opmanager.use_https
        verify_ssl = arguments.get("verify_ssl", self.config.opmanager.tls_verify)

        missing_creds = []
        if not host:
            missing_creds.append("host")
        if not api_key:
            missing_creds.append("apiKey")

        if missing_creds:
            raise InvalidToolArgumentsError(
                name,
                missing_args=missing_creds,
                message="Missing required credentials",
            )

        # Find the tool definition
        tool = next((t for t in self.tools if t["name"] == name), None)
        if not tool:
            raise ToolNotFoundError(name)

        # Get API path for tool
        path = tool.get("_path") or self._get_path_for_tool(name)
        if not path:
            raise ToolNotFoundError(
                name,
                message=f"Could not determine API path for tool: {name}",
            )

        # Get HTTP method for tool
        method = tool.get("_method", "get").upper()

        # Build API parameters using whitelist from tool schema
        api_params = self._build_api_params(arguments, tool)

        logger.info(
            f"Executing tool: {name}",
            extra={"host": host, "path": path, "param_count": len(api_params)},
        )

        try:
            # Create API client with per-request credentials
            async with OpManagerAPIClient(
                host=str(host),
                api_key=str(api_key),
                port=int(port) if port else 8060,
                use_https=bool(use_ssl),
                tls_verify=bool(verify_ssl),
                timeout=self.config.server.request_timeout // 1000,
                max_retries=self.config.server.max_retries,
            ) as client:
                # Execute the API call
                result = await client.execute_operation(
                    path=path,
                    method=method,
                    params=api_params if api_params else None,
                )

                logger.info(f"Successfully executed tool: {name}")

                # Return success result per MCP spec
                return types.CallToolResult(
                    content=[
                        types.TextContent(
                            type="text",
                            text=json.dumps(result, indent=2),
                        )
                    ],
                    isError=False,
                )

        except OpManagerAPIError as e:
            # Per MCP spec: Tool execution errors return isError=True
            logger.error(
                f"API error executing tool {name}: {e}",
                extra={"tool": name, "error_type": type(e).__name__},
            )
            error_details: dict[str, Any] = {
                "error": type(e).__name__,
                "message": str(e),
                "tool": name,
            }
            if hasattr(e, "status_code") and e.status_code:
                error_details["status_code"] = e.status_code
            if hasattr(e, "details") and e.details:
                error_details["details"] = e.details

            return types.CallToolResult(
                content=[
                    types.TextContent(
                        type="text",
                        text=json.dumps(error_details, indent=2),
                    )
                ],
                isError=True,
            )
        except Exception as e:
            # Per MCP spec: Unexpected errors also return isError=True
            logger.error(
                f"Unexpected error executing tool {name}: {e}",
                extra={"tool": name, "error_type": type(e).__name__},
            )
            unexpected_error_details: dict[str, Any] = {
                "error": type(e).__name__,
                "message": str(e),
                "tool": name,
            }
            return types.CallToolResult(
                content=[
                    types.TextContent(
                        type="text",
                        text=json.dumps(unexpected_error_details, indent=2),
                    )
                ],
                isError=True,
            )

    def _build_api_params(
        self,
        arguments: dict[str, Any],
        tool: dict[str, Any],
    ) -> dict[str, Any]:
        """Build API parameters from tool arguments using whitelist approach.

        Only includes parameters that are defined in the tool's inputSchema.
        Also performs type coercion based on the schema.

        Args:
            arguments: Raw tool arguments.
            tool: Tool definition containing inputSchema.

        Returns:
            Cleaned and validated parameters for the API call.
        """
        api_params: dict[str, Any] = {}
        query_params = arguments.get("queryParams", {})

        # Get allowed parameters from tool's inputSchema (whitelist approach)
        input_schema = tool.get("inputSchema", {})
        properties = input_schema.get("properties", {})

        # Only include parameters that are defined in the schema
        for key, value in arguments.items():
            # Skip if value is None
            if value is None:
                continue

            # Skip if not in schema (metadata parameters like tool, toolCallId, etc.)
            if key not in properties:
                continue

            # Skip credential/connection params (handled separately)
            if key in EXCLUDED_PARAMS:
                continue

            # Coerce type based on schema
            schema_info = properties.get(key, {})
            coerced_value = self._coerce_type(value, schema_info)
            api_params[key] = coerced_value

        # Merge queryParams object (but also validate against schema)
        if isinstance(query_params, dict):
            for key, value in query_params.items():
                if value is not None and key in properties:
                    schema_info = properties.get(key, {})
                    api_params[key] = self._coerce_type(value, schema_info)

        return api_params

    def _coerce_type(self, value: Any, schema_info: dict[str, Any]) -> Any:
        """Coerce value to the expected type based on schema.

        Args:
            value: The value to coerce.
            schema_info: Schema information containing type and enum.

        Returns:
            Coerced value.
        """
        expected_type = schema_info.get("type", "string")
        enum_values = schema_info.get("enum", [])

        # If there's an enum, check if the value matches (as string)
        if enum_values:
            str_value = str(value)
            if str_value in enum_values:
                return str_value
            # Try to find a matching enum value
            for enum_val in enum_values:
                if str(enum_val) == str_value:
                    return enum_val

        # Coerce based on expected type
        if expected_type == "string":
            return str(value)
        elif expected_type == "integer":
            try:
                return int(value)
            except (ValueError, TypeError):
                return value
        elif expected_type == "number":
            try:
                return float(value)
            except (ValueError, TypeError):
                return value
        elif expected_type == "boolean":
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.lower() in ("true", "1", "yes")
            return bool(value)

        return value

    def _get_path_for_tool(self, tool_name: str) -> str | None:
        """Get API path for a tool by matching against OpenAPI spec.

        Args:
            tool_name: Name of the tool.

        Returns:
            API path or None if not found.
        """
        if not self.tool_generator:
            return None

        return self.tool_generator.get_path_for_tool(tool_name)
