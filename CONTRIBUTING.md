# Contributing to OpManager MCP Server

Thank you for your interest in contributing to OpManager MCP Server! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for everyone.

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/sachdev27/opmanager-mcp-server/issues)
2. If not, create a new issue with:
   - Clear, descriptive title
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (Python version, OS, MCP SDK version)

### Suggesting Features

1. Check existing issues for similar suggestions
2. Create a new issue with:
   - Clear description of the feature
   - Use case and benefits
   - Possible implementation approach

### Pull Requests

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes
4. Run tests: `pytest`
5. Run linting: `ruff check opmanager_mcp tests`
6. Commit with clear messages: `git commit -m "Add feature: description"`
7. Push to your fork: `git push origin feature/your-feature-name`
8. Create a Pull Request

## Development Setup

```bash
# Clone your fork
git clone https://github.com/sachdev27/opmanager-mcp-server.git
cd opmanager-mcp-server

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks (optional)
pre-commit install
```

## Code Style

- Follow [PEP 8](https://pep8.org/) style guidelines
- Use [Black](https://black.readthedocs.io/) for formatting
- Use [isort](https://pycqa.github.io/isort/) for import sorting
- Use type hints for all function signatures
- Write docstrings for public functions and classes

### Running Code Quality Tools

```bash
# Format code
black opmanager_mcp tests
isort opmanager_mcp tests

# Lint
ruff check opmanager_mcp tests

# Type check
mypy opmanager_mcp
```

## Testing

- Write tests for all new features
- Maintain or improve code coverage
- Use pytest for testing
- Use pytest-asyncio for async tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=opmanager_mcp --cov-report=term-missing

# Run specific test file
pytest tests/test_server.py -v
```

## Documentation

- Update README.md for user-facing changes
- Update CHANGELOG.md following [Keep a Changelog](https://keepachangelog.com/)
- Add docstrings to new functions and classes

## Commit Messages

Follow conventional commit format:
- `feat: Add new feature`
- `fix: Fix bug description`
- `docs: Update documentation`
- `test: Add tests for feature`
- `refactor: Refactor code without changing behavior`
- `chore: Update dependencies`

## Review Process

1. All PRs require at least one approval
2. CI checks must pass (tests, linting)
3. Code coverage should not decrease significantly
4. Documentation must be updated if needed

## Questions?

Feel free to open an issue for any questions about contributing.

Thank you for helping improve OpManager MCP Server! 🙏
