# PyPI Publishing Guide

This guide explains how to publish the OpManager MCP Server to PyPI.

## Prerequisites

1. PyPI account: https://pypi.org/account/register/
2. PyPI API token with upload permissions
3. GitHub repository secrets configured

## Setup GitHub Secrets

### For Trusted Publishing (Recommended)

1. Go to PyPI → Account Settings → Publishing
2. Add a new publisher:
   - **PyPI Project Name**: `opmanager-mcp-server`
   - **Owner**: `sachdev27`
   - **Repository name**: `opmanager-mcp-server`
   - **Workflow name**: `release.yml`
   - **Environment name**: (leave empty)

This allows GitHub Actions to publish without API tokens.

### Alternative: Using API Token

If not using trusted publishing:

1. Generate PyPI API token at https://pypi.org/manage/account/token/
2. Add to GitHub repository secrets:
   - Go to: Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `PYPI_API_TOKEN`
   - Value: Your PyPI API token (starts with `pypi-`)

Then update `.github/workflows/release.yml`:

```yaml
- name: Publish to PyPI
  env:
    TWINE_USERNAME: __token__
    TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
  run: twine upload dist/*
```

## Release Process

### 1. Update Version

Edit `pyproject.toml`:

```toml
[project]
name = "opmanager-mcp-server"
version = "1.0.1"  # Increment version
```

### 2. Update Changelog

Add release notes to `CHANGELOG.md`:

```markdown
## [1.0.1] - 2024-12-10

### Fixed
- Bug fixes...

### Added
- New features...
```

### 3. Commit and Tag

```bash
git add pyproject.toml CHANGELOG.md
git commit -m "Release v1.0.1"
git tag v1.0.1
git push origin main --tags
```

### 4. Automatic Publishing

The GitHub Actions workflow will automatically:
1. Run tests
2. Build the package
3. Publish to PyPI
4. Build and push Docker image to GHCR

## Manual Publishing (Local)

For testing or manual releases:

```bash
# Build the package
python -m build

# Check the package
twine check dist/*

# Upload to Test PyPI (optional)
twine upload --repository testpypi dist/*

# Upload to PyPI
twine upload dist/*
```

## Verify Installation

After publishing, test the package:

```bash
pip install opmanager-mcp-server

# Or with extras
pip install opmanager-mcp-server[http]
pip install opmanager-mcp-server[all]
```

## Versioning

Follow [Semantic Versioning](https://semver.org/):
- **Major** (1.0.0): Breaking changes
- **Minor** (1.1.0): New features, backward compatible
- **Patch** (1.0.1): Bug fixes, backward compatible

## Package Name

- PyPI package: `opmanager-mcp-server` (with hyphens)
- Import name: `opmanager_mcp` (with underscores)
- Command: `opmanager-mcp`

## Troubleshooting

### Build Fails

```bash
# Clean dist folder
rm -rf dist/ build/ *.egg-info

# Rebuild
python -m build
```

### Upload Fails

- Check package name not already taken
- Verify API token has upload permissions
- Ensure version number is unique (never reuse)

### Import Errors

- Verify `openapi.json` is included in package
- Check `tool.hatch.build.targets.sdist` includes all necessary files

## Resources

- PyPI: https://pypi.org/project/opmanager-mcp-server/
- Test PyPI: https://test.pypi.org/project/opmanager-mcp-server/
- PyPI Trusted Publishing: https://docs.pypi.org/trusted-publishers/
- Python Packaging Guide: https://packaging.python.org/
