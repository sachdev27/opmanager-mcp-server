"""OpManager API client with API Key authentication.

This module provides an async HTTP client for the OpManager REST API
using API Key authentication on every request.

Example:
    >>> async with OpManagerAPIClient(
    ...     host="opmanager.example.com",
    ...     api_key="your-api-key",
    ... ) as client:
    ...     alarms = await client.execute_operation("/api/json/alarm/listAlarms", "GET")
    ...     print(f"Found {len(alarms)} alarms")

Note:
    OpManager API uses API key authentication which can be passed either
    via header (preferred) or query parameter (deprecated for some endpoints).

    OpManager API URL structure:
    - All endpoints: /api/json/{category}/{operation}
    - Examples:
      - /api/json/alarm/listAlarms
      - /api/json/device/listDevices
      - /api/json/monitor/getPerformanceMonitors
"""

from __future__ import annotations

import asyncio
from typing import Any
from urllib.parse import urljoin

import httpx

from .exceptions import (
    APIResponseError,
    AuthenticationError,
    ConnectionError,
    RateLimitError,
)
from .logging_config import LoggerAdapter, get_logger

logger = get_logger(__name__)


class OpManagerAPIClient:
    """OpManager API client using API Key authentication.

    This client creates HTTP connections using API Key authentication.
    The API key can be passed via header (preferred) or query parameter.

    The OpManager REST API uses a consistent URL structure:
    - All endpoints: /api/json/{category}/{operation}

    Attributes:
        host: OpManager host address.
        base_url: Full base URL for API requests.

    Example:
        >>> client = OpManagerAPIClient(
        ...     host="opmanager.example.com",
        ...     api_key="your-api-key",
        ... )
        >>> try:
        ...     result = await client.execute_operation("/api/json/alarm/listAlarms", "GET")
        ...     print(result)
        ... finally:
        ...     await client.close()
    """

    def __init__(
        self,
        host: str,
        api_key: str,
        port: int = 8060,
        use_https: bool = False,
        tls_verify: bool = False,
        timeout: int = 30,
        max_retries: int = 3,
    ) -> None:
        """Initialize OpManager API client.

        Args:
            host: OpManager host (e.g., "opmanager.example.com").
            api_key: OpManager API key.
            port: OpManager port (default: 8060).
            use_https: Use HTTPS instead of HTTP.
            tls_verify: Whether to verify TLS certificates.
            timeout: Request timeout in seconds.
            max_retries: Maximum number of retry attempts for transient errors.

        Raises:
            ValueError: If host or api_key is empty.
        """
        if not host:
            raise ValueError("host is required")
        if not api_key:
            raise ValueError("api_key is required")

        self.host = host
        self.api_key = api_key
        self.port = port
        self.use_https = use_https
        self.tls_verify = tls_verify
        self.timeout = timeout
        self.max_retries = max_retries

        # Build base URL
        protocol = "https" if use_https else "http"
        self.base_url = f"{protocol}://{host}:{port}"

        # Create logger adapter with host context
        self._logger = LoggerAdapter(logger, {"host": host})

        # HTTP client (created lazily)
        self.client: httpx.AsyncClient | None = None

    async def _ensure_client(self) -> httpx.AsyncClient:
        """Ensure HTTP client is initialized.

        Returns:
            The initialized HTTP client.
        """
        if self.client is None:
            self.client = httpx.AsyncClient(
                verify=self.tls_verify,
                timeout=self.timeout,
                follow_redirects=True,
                headers={
                    "apiKey": self.api_key,
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
            )
        return self.client

    async def execute_operation(
        self,
        path: str,
        method: str = "GET",
        params: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """Execute an API operation with API Key auth.

        This method handles retries for transient errors and provides
        detailed logging for debugging.

        Args:
            path: API endpoint path (e.g., "/api/json/alarm/listAlarms").
            method: HTTP method (GET, POST, PUT, DELETE).
            params: Query parameters.
            body: Request body for POST/PUT requests.

        Returns:
            Parsed JSON response (dict or list).

        Raises:
            AuthenticationError: If API key is invalid.
            ConnectionError: If connection fails.
            APIResponseError: If API returns an error.
            RateLimitError: If rate limit is exceeded.
        """
        client = await self._ensure_client()
        url = urljoin(self.base_url, path)

        self._logger.debug(
            f"Executing {method} {path}",
            extra={"params": params, "has_body": body is not None},
        )

        last_error: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                response = await self._make_request(client, method, url, params, body)
                return self._parse_response(response)

            except (httpx.TimeoutException, httpx.ConnectError) as e:
                last_error = e
                if attempt < self.max_retries:
                    wait_time = (2**attempt) * 0.5  # Exponential backoff
                    self._logger.warning(
                        f"Request failed, retrying in {wait_time}s (attempt {attempt + 1}/{self.max_retries})",
                        extra={"error": str(e)},
                    )
                    await asyncio.sleep(wait_time)
                else:
                    raise ConnectionError(self.host, e) from e

            except AuthenticationError:
                # Don't retry auth errors
                raise

            except RateLimitError as e:
                # Handle rate limiting with retry-after
                if e.retry_after and attempt < self.max_retries:
                    self._logger.warning(
                        f"Rate limited, waiting {e.retry_after}s",
                    )
                    await asyncio.sleep(e.retry_after)
                else:
                    raise

        # Should not reach here, but just in case
        raise ConnectionError(self.host, last_error)

    async def _make_request(
        self,
        client: httpx.AsyncClient,
        method: str,
        url: str,
        params: dict[str, Any] | None,
        body: dict[str, Any] | None,
    ) -> httpx.Response:
        """Make the actual HTTP request.

        Args:
            client: HTTP client.
            method: HTTP method.
            url: Full URL.
            params: Query parameters.
            body: Request body.

        Returns:
            HTTP response.
        """
        method = method.upper()

        if method == "GET":
            response = await client.get(url, params=params)
        elif method == "POST":
            response = await client.post(url, params=params, json=body)
        elif method == "PUT":
            response = await client.put(url, params=params, json=body)
        elif method == "DELETE":
            response = await client.delete(url, params=params)
        elif method == "PATCH":
            response = await client.patch(url, params=params, json=body)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        return response

    def _parse_response(
        self, response: httpx.Response
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """Parse and validate API response.

        Args:
            response: HTTP response object.

        Returns:
            Parsed JSON data.

        Raises:
            AuthenticationError: If authentication failed (401).
            RateLimitError: If rate limit exceeded (429).
            APIResponseError: For other API errors.
        """
        # Handle authentication errors
        if response.status_code == 401:
            raise AuthenticationError(
                "API key authentication failed - check your API key",
                status_code=401,
            )

        # Handle rate limiting
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(retry_after=int(retry_after) if retry_after else None)

        # Handle other errors
        if response.status_code >= 400:
            try:
                error_body = response.json()
                error_message = (
                    error_body.get("error", {}).get("message")
                    or error_body.get("message")
                    or str(error_body)
                )
            except Exception:
                error_message = response.text or f"HTTP {response.status_code}"

            raise APIResponseError(
                message=error_message,
                status_code=response.status_code,
                response_body=response.text,
            )

        # Parse successful response
        try:
            data = response.json()
            self._logger.debug(
                "Request successful",
                extra={"status_code": response.status_code},
            )
            return data
        except Exception as e:
            # If response is not JSON, return as text
            self._logger.warning(
                f"Response is not JSON: {e}",
                extra={"content_type": response.headers.get("content-type")},
            )
            return {"raw_response": response.text}

    async def close(self) -> None:
        """Close the HTTP client and release resources."""
        if self.client:
            await self.client.aclose()
            self.client = None
            self._logger.debug("HTTP client closed")

    async def __aenter__(self) -> OpManagerAPIClient:
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()


async def test_connection(
    host: str,
    api_key: str,
    port: int = 8060,
    use_https: bool = False,
    tls_verify: bool = False,
) -> dict[str, Any]:
    """Test connection to OpManager server.

    Args:
        host: OpManager host.
        api_key: API key.
        port: OpManager port.
        use_https: Use HTTPS.
        tls_verify: Verify TLS certificates.

    Returns:
        Connection test result.

    Example:
        >>> result = await test_connection("opmanager.example.com", "api-key")
        >>> print(result["success"])
    """
    async with OpManagerAPIClient(
        host=host,
        api_key=api_key,
        port=port,
        use_https=use_https,
        tls_verify=tls_verify,
        timeout=10,
        max_retries=1,
    ) as client:
        try:
            # Try to list devices as a connection test
            await client.execute_operation(
                "/api/json/device/listDevices",
                "GET",
            )
            return {
                "success": True,
                "message": "Connection successful",
                "host": host,
            }
        except AuthenticationError:
            return {
                "success": False,
                "message": "Authentication failed - check API key",
                "host": host,
            }
        except ConnectionError as e:
            return {
                "success": False,
                "message": f"Connection failed: {e}",
                "host": host,
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Unexpected error: {e}",
                "host": host,
            }
