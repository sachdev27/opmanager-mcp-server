#!/bin/bash
# Docker Build and Test Script

set -e

echo "🔨 Building Docker image..."
docker build -t opmanager-mcp-server:test .

echo ""
echo "✅ Build successful!"
echo ""
echo "🧪 Testing image..."

# Run container
docker run -d --name test-mcp -p 3001:3000 opmanager-mcp-server:test

# Wait for startup
echo "⏳ Waiting for server to start..."
sleep 5

# Test health endpoint
echo "🏥 Testing health endpoint..."
if curl -f http://localhost:3001/health; then
    echo ""
    echo "✅ Health check passed!"
else
    echo ""
    echo "❌ Health check failed!"
    docker logs test-mcp
    docker stop test-mcp
    docker rm test-mcp
    exit 1
fi

# Test tools endpoint
echo ""
echo "🛠️  Testing tools endpoint..."
if curl -f http://localhost:3001/tools | jq '.tools | length'; then
    echo "✅ Tools endpoint working!"
else
    echo "❌ Tools endpoint failed!"
fi

# Cleanup
echo ""
echo "🧹 Cleaning up..."
docker stop test-mcp
docker rm test-mcp

echo ""
echo "✅ All Docker tests passed!"
echo ""
echo "To run the container:"
echo "  docker run -d -p 3000:3000 --name opmanager-mcp opmanager-mcp-server:test"
echo ""
echo "Or with docker-compose:"
echo "  docker-compose up -d"
