# OpManager MCP Server

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-32%20passed-brightgreen.svg)]()
[![MCP SDK](https://img.shields.io/badge/MCP%20SDK-1.23+-purple.svg)](https://github.com/modelcontextprotocol/python-sdk)

A **credential-less** Model Context Protocol (MCP) server for ManageEngine OpManager REST API integration. This server enables AI assistants like Claude to interact with your OpManager infrastructure through natural language.

## ✨ Key Features

- **🔐 Credential-less Design**: No hardcoded API keys - users provide `host` and `apiKey` per request
- **🔄 SSL Auto-Detection**: Port 8061 → HTTPS, Port 8060 → HTTP (with manual override)
- **📡 85+ API Endpoints**: Full OpManager API coverage for devices, alarms, dashboards, discovery, and more
- **🛠 Dynamic Tool Generation**: Automatically generates MCP tools from OpenAPI specification
- **🌐 Multiple Transports**: Supports stdio (Claude Desktop) and HTTP/SSE (n8n, web clients)
- **🐳 Docker Ready**: Containerized deployment with Docker and Docker Compose

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/sachdev27/opmanager-mcp-server.git
cd opmanager-mcp-server

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package
pip install -e ".[http]"
```

### Start the HTTP Server

```bash
uvicorn opmanager_mcp.http_server:app --host 0.0.0.0 --port 3000
```

### Test a Tool Call

```bash
curl -X POST http://localhost:3000/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "opmanager_get_allDevices",
    "arguments": {
      "host": "opmanager.example.com",
      "apiKey": "your-api-key-here",
      "port": 8061
    }
  }'
```

## 📋 Configuration

### Environment Variables

Create a `.env` file (optional - for server defaults only):

```bash
cp .env.example .env
```

| Variable | Description | Default |
|----------|-------------|---------|
| `MCP_SERVER_LOG_LEVEL` | Logging level | `INFO` |
| `ALLOWED_HTTP_METHODS` | Allowed HTTP methods for tools | `GET,POST,PUT,DELETE,PATCH` |
| `LOCAL_OPENAPI_SPEC_PATH` | Path to OpenAPI spec | bundled `openapi.json` |

> **Note**: `OPMANAGER_HOST` and `OPMANAGER_API_KEY` are NOT configured server-side. Users provide these per-request for security.

### Getting Your OpManager API Key

1. Log in to OpManager web console
2. Navigate to **Settings** → **REST API**
3. Generate a new API key
4. Use this key in your tool calls

## 🔧 Tool Parameters

Every tool accepts these connection parameters:

| Parameter | Required | Description |
|-----------|----------|-------------|
| `host` | ✅ Yes | OpManager server hostname |
| `apiKey` | ✅ Yes | API key for authentication |
| `port` | No | Server port (default: 8060) |
| `use_ssl` | No | Force SSL (auto-detected from port) |
| `verify_ssl` | No | Verify SSL certificates (default: true) |

### SSL Auto-Detection

- **Port 8061**: Automatically uses HTTPS
- **Port 8060**: Automatically uses HTTP
- Override with `use_ssl: true/false` if needed

## 🌐 HTTP API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check with tool count |
| `/tools` | GET | List all available tools |
| `/sse` | GET | SSE connection for MCP |
| `/messages` | POST | MCP message handler |
| `/call` | POST | Direct tool invocation |

### Health Check

```bash
curl http://localhost:3000/health
# {"status":"healthy","tool_count":60}
```

### List Tools

```bash
curl http://localhost:3000/tools | jq '.tools[].name'
```

## 🤖 n8n Integration

1. Start the HTTP server on port 3000
2. In n8n, add an **AI Agent** node with **MCP Client** tool
3. Configure the MCP Client:
   - **SSE URL**: `http://localhost:3000/sse`
   - **Messages URL**: `http://localhost:3000/messages`

### Example System Prompt for n8n

```
You are an IT operations assistant with access to OpManager for network monitoring.

When using OpManager tools, always include:
- host: "opmanager.company.com"
- apiKey: "your-api-key"
- port: 8061 (for HTTPS)

Available operations:
- List all devices: opmanager_get_allDevices
- Get device details: opmanager_get_device (requires deviceName)
- List alarms: opmanager_get_alarms
- Acknowledge alarm: opmanager_add_alarmNotes
```

## 🖥 Claude Desktop Integration

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "opmanager": {
      "command": "python",
      "args": ["-m", "opmanager_mcp.main"],
      "cwd": "/path/to/opmanager-mcp-server",
      "env": {
        "LOCAL_OPENAPI_SPEC_PATH": "/path/to/opmanager-mcp-server/openapi.json"
      }
    }
  }
}
```

> **Note**: With Claude Desktop, you'll tell Claude your OpManager host and API key in conversation, and it will include them in tool calls.

## 🛠 Available Tools (60+ GET operations)

### Devices
- `opmanager_get_allDevices` - List all monitored devices
- `opmanager_get_device` - Get device details by name
- `opmanager_get_deviceAvailability` - Device availability history

### Alarms
- `opmanager_get_alarms` - List alarms with filtering
- `opmanager_get_alarmDetails` - Get alarm details
- `opmanager_add_alarmNotes` - Add notes/acknowledge alarm

### Discovery
- `opmanager_get_discoveryStatus` - Check discovery progress
- `opmanager_add_discovery` - Start network discovery

### Reports & Dashboards
- `opmanager_get_allDashboards` - List all dashboards
- `opmanager_get_scheduledReports` - List scheduled reports

### And more...
Run `curl http://localhost:3000/tools` to see all available tools.

## 🐳 Docker

### Build and Run

```bash
docker build -t opmanager-mcp-server .
docker run -d -p 3000:3000 --name opmanager-mcp opmanager-mcp-server
```

### Docker Compose

```bash
docker-compose up -d
```

## 🧪 Development

### Run Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with coverage
pytest --cov=opmanager_mcp --cov-report=term-missing

# Current: 32 tests, 50% coverage
```

### Code Quality

```bash
# Format
black opmanager_mcp tests
isort opmanager_mcp tests

# Lint
ruff check opmanager_mcp tests

# Type check
mypy opmanager_mcp
```

### Regenerate OpenAPI Spec

```bash
python generate_openapi.py
```

## 📁 Project Structure

```
opmanager-mcp-server/
├── opmanager_mcp/
│   ├── __init__.py          # Package exports
│   ├── api_client.py        # HTTP client for OpManager API
│   ├── config.py            # Configuration management
│   ├── exceptions.py        # Custom exceptions
│   ├── http_server.py       # HTTP/SSE server (Pure ASGI)
│   ├── logging_config.py    # Logging configuration
│   ├── main.py              # CLI entry point
│   ├── server.py            # MCP server implementation
│   └── tool_generator.py    # OpenAPI to MCP tool converter
├── tests/
│   ├── conftest.py          # Test fixtures
│   ├── test_api_client.py   # API client tests
│   ├── test_config.py       # Config tests
│   ├── test_http_server.py  # HTTP server tests
│   ├── test_server.py       # MCP server tests
│   └── test_tool_generator.py # Tool generation tests
├── openapi.json             # OpManager OpenAPI specification
├── pyproject.toml           # Project configuration
├── Dockerfile               # Container image
├── docker-compose.yml       # Compose configuration
└── README.md                # This file
```

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- Built with [Model Context Protocol SDK](https://github.com/modelcontextprotocol/python-sdk)
- OpManager REST API by [ManageEngine](https://www.manageengine.com/network-monitoring/)
