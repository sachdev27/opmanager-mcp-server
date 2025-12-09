# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-12-09

### Added
- Initial release of OpManager MCP Server
- **Credential-less design**: Users provide `host` and `apiKey` per request (no hardcoded credentials)
- **SSL auto-detection**: Port 8061 automatically uses HTTPS, port 8060 uses HTTP
- **85+ API endpoints** from OpManager REST API
- **Dynamic tool generation** from OpenAPI specification
- **Multiple transport support**:
  - stdio for Claude Desktop integration
  - HTTP/SSE for n8n and web client integration
- **Pure ASGI HTTP server** compatible with MCP SDK 1.23+
- **Docker support** with Dockerfile and docker-compose.yml
- **Comprehensive test suite**: 32 tests with 50% code coverage
- OpenAPI spec generator (`generate_openapi.py`) for parsing OpManager HTML docs

### Tools Categories
- **Devices**: List, get details, availability history
- **Alarms**: List, filter, acknowledge, clear
- **Discovery**: Start discovery, check status
- **Dashboards**: List dashboards, get widgets
- **Reports**: Generate and schedule reports
- **Interfaces**: Interface monitoring and statistics
- **Credential Profiles**: Manage SNMP/WMI credentials
- **Business Views**: Manage business view hierarchies

### Technical Details
- Python 3.10+ required
- MCP SDK 1.23+ for SSE transport
- httpx for async HTTP client
- pydantic for configuration validation
- uvicorn for ASGI server

## [Unreleased]

### Planned
- Additional integration tests
- WebSocket transport support
- Caching layer for frequently accessed data
- Rate limiting for API calls
- Metrics and monitoring endpoints
