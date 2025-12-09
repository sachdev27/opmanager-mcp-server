# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Security Design

### Credential-less Architecture

This MCP server is designed with security in mind:

- **No stored credentials**: The server does not store OpManager API keys or host information
- **Per-request authentication**: Users provide `host` and `apiKey` with each tool call
- **No environment variable secrets**: API keys are never read from environment variables
- **Stateless operation**: Each request is independent, no credential caching

### SSL/TLS Support

- **Auto-detection**: Port 8061 automatically uses HTTPS
- **Certificate verification**: SSL verification enabled by default
- **Manual override**: Users can set `verify_ssl: false` for self-signed certificates (not recommended for production)

## Reporting a Vulnerability

If you discover a security vulnerability, please:

1. **Do NOT** open a public issue
2. Email the maintainers directly with:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

We will respond within 48 hours and work with you to:
- Confirm the vulnerability
- Develop a fix
- Coordinate disclosure

## Best Practices for Users

### API Key Security

1. **Rotate keys regularly**: Generate new API keys periodically
2. **Use least privilege**: Create API keys with minimal required permissions
3. **Monitor usage**: Review OpManager audit logs for API key usage
4. **Secure transmission**: Always use HTTPS (port 8061) in production

### Network Security

1. **Firewall rules**: Restrict MCP server access to trusted networks
2. **Internal deployment**: Run the MCP server on internal networks only
3. **Reverse proxy**: Use nginx/traefik with TLS termination for external access

### Docker Security

1. **Non-root user**: The Docker image runs as non-root by default
2. **Read-only filesystem**: Consider `--read-only` flag
3. **Resource limits**: Set CPU/memory limits in production

```bash
docker run -d \
  --read-only \
  --memory=256m \
  --cpus=0.5 \
  -p 3000:3000 \
  opmanager-mcp-server
```

## Acknowledgments

We appreciate responsible disclosure of security issues.
