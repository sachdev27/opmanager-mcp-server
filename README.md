# OpManager MCP Server

A Model Context Protocol (MCP) server for ManageEngine OpManager REST API integration. This server enables AI assistants like Claude to interact with your OpManager infrastructure through natural language.

## Features

- **Full OpManager API Coverage**: 85+ endpoints covering devices, alarms, dashboards, discovery, and more
- **Dynamic Tool Generation**: Automatically generates MCP tools from OpenAPI specification
- **Multiple Transports**: Supports stdio (Claude Desktop) and HTTP/SSE (n8n, web clients)
- **Secure Authentication**: API key-based authentication
- **Comprehensive Logging**: Structured logging with JSON and colored output options
- **Docker Support**: Ready-to-use Docker and Docker Compose configurations

## Installation

### From PyPI (when published)

```bash
pip install opmanager-mcp-server
```

### From Source

```bash
git clone https://github.com/example/opmanager-mcp-server.git
cd opmanager-mcp-server
pip install -e .
```

### With HTTP Server Support

```bash
pip install -e ".[http]"
```

### With All Dependencies

```bash
pip install -e ".[all]"
```

## Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

Configure the following variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `OPMANAGER_HOST` | OpManager server hostname | `localhost` |
| `OPMANAGER_PORT` | OpManager server port | `8060` |
| `OPMANAGER_USE_SSL` | Use HTTPS connection | `false` |
| `OPMANAGER_API_KEY` | API key for authentication | Required |
| `OPMANAGER_VERIFY_SSL` | Verify SSL certificates | `true` |
| `OPMANAGER_TIMEOUT` | Request timeout in seconds | `30` |
| `MCP_SERVER_LOG_LEVEL` | Logging level | `INFO` |
| `MCP_SERVER_LOG_JSON` | Use JSON log format | `false` |

### Getting Your API Key

1. Log in to OpManager web console
2. Navigate to **Settings** → **REST API**
3. Generate a new API key
4. Copy the key to your `.env` file

## Usage

### Claude Desktop Integration

Add to your Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "opmanager": {
      "command": "opmanager-mcp",
      "env": {
        "OPMANAGER_HOST": "your-opmanager-host",
        "OPMANAGER_PORT": "8060",
        "OPMANAGER_API_KEY": "your-api-key"
      }
    }
  }
}
```

Or if running from source:

```json
{
  "mcpServers": {
    "opmanager": {
      "command": "python",
      "args": ["-m", "opmanager_mcp.main"],
      "cwd": "/path/to/opmanager-mcp-server",
      "env": {
        "OPMANAGER_HOST": "your-opmanager-host",
        "OPMANAGER_PORT": "8060",
        "OPMANAGER_API_KEY": "your-api-key"
      }
    }
  }
}
```

### n8n Integration

1. Start the HTTP server:

```bash
uvicorn opmanager_mcp.http_server:app --host 0.0.0.0 --port 3000
```

2. In n8n, add an MCP Client node with:
   - **SSE URL**: `http://localhost:3000/sse`
   - **Messages URL**: `http://localhost:3000/messages`

### HTTP API Endpoints

When running the HTTP server:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/tools` | GET | List available tools |
| `/sse` | GET | SSE connection for MCP |
| `/messages` | POST | MCP message handler |
| `/call` | POST | Direct tool invocation |

### Direct Tool Call Example

```bash
curl -X POST http://localhost:3000/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "opmanager_list_devices",
    "arguments": {}
  }'
```

## Available Tools

The server exposes 85+ tools organized by category:

### Alarms
- `opmanager_list_alarms` - List alarms with filtering options
- `opmanager_get_alarm_details` - Get details for a specific alarm
- `opmanager_acknowledge_alarm` - Acknowledge an alarm
- `opmanager_clear_alarm` - Clear an alarm
- And more...

### Devices
- `opmanager_list_devices` - List all devices
- `opmanager_get_device` - Get device details
- `opmanager_add_device` - Add a new device
- `opmanager_delete_device` - Delete a device
- And more...

### Discovery
- `opmanager_start_discovery` - Start network discovery
- `opmanager_get_discovery_status` - Check discovery progress
- And more...

### Dashboards
- `opmanager_list_dashboards` - List dashboards
- `opmanager_get_dashboard_widgets` - Get dashboard widgets
- And more...

### Reports
- `opmanager_generate_report` - Generate reports
- `opmanager_schedule_report` - Schedule report generation
- And more...

Run `opmanager-mcp` and use the `tools/list` capability to see all available tools.

## Docker

### Build the Image

```bash
docker build -t opmanager-mcp-server .
```

### Run with Docker

```bash
docker run -d \
  --name opmanager-mcp \
  -p 3000:3000 \
  -e OPMANAGER_HOST=your-opmanager-host \
  -e OPMANAGER_PORT=8060 \
  -e OPMANAGER_API_KEY=your-api-key \
  opmanager-mcp-server
```

### Run with Docker Compose

```bash
docker-compose up -d
```

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/example/opmanager-mcp-server.git
cd opmanager-mcp-server

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=opmanager_mcp --cov-report=html

# Run specific test file
pytest tests/test_server.py
```

### Code Quality

```bash
# Format code
black opmanager_mcp tests
isort opmanager_mcp tests

# Lint
ruff check opmanager_mcp tests

# Type checking
mypy opmanager_mcp
```

### Regenerating OpenAPI Spec

If you have an updated OpManager HTML documentation:

```bash
python generate_openapi.py
```

This will regenerate `openapi.json` from `rest-api.html`.

## Architecture

```
opmanager_mcp/
├── __init__.py          # Package exports
├── api_client.py        # HTTP client for OpManager API
├── config.py            # Configuration management
├── exceptions.py        # Custom exceptions
├── http_server.py       # HTTP/SSE server for n8n
├── logging_config.py    # Logging configuration
├── main.py              # CLI entry point
├── server.py            # MCP server implementation
└── tool_generator.py    # OpenAPI to MCP tool converter
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details.

## Acknowledgments

- Inspired by the [Dell Unity MCP Server](https://github.com/example/dell-unity-mcp-server)
- Built with the [Model Context Protocol SDK](https://github.com/modelcontextprotocol/python-sdk)
- OpManager REST API documentation by [ManageEngine](https://www.manageengine.com/network-monitoring/)
