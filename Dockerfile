# Build stage
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies (curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r mcp && useradd -r -g mcp mcp

# Install Python dependencies
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache /wheels/*

# Copy application
COPY opmanager_mcp/ ./opmanager_mcp/
COPY openapi.json .
COPY pyproject.toml .
COPY README.md .

# Install the package
RUN pip install -e .

# Set ownership
RUN chown -R mcp:mcp /app

# Switch to non-root user
USER mcp

# Expose HTTP server port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.path.insert(0, '/app'); from opmanager_mcp.http_server import app; print('OK')" || exit 1

# Default environment variables
# Available HTTP METHODS: GET, POST, PUT, DELETE, PATCH
ENV MCP_SERVER_LOG_LEVEL=INFO \
    MCP_SERVER_LOG_JSON=true \
    ALLOWED_HTTP_METHODS=GET \
    LOCAL_OPENAPI_SPEC_PATH=/app/openapi.json

# Run HTTP server by default
CMD ["uvicorn", "opmanager_mcp.http_server:app", "--host", "0.0.0.0", "--port", "3000"]
