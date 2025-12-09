"""Tests for the tool generator."""

from __future__ import annotations

from typing import Any

import pytest


class TestToolGenerator:
    """Tests for the OpenAPI to MCP tool generator."""

    def test_generate_tools_from_spec(self, sample_openapi_spec):
        """Test generating tools from OpenAPI spec."""
        from opmanager_mcp.tool_generator import ToolGenerator

        generator = ToolGenerator(sample_openapi_spec)
        tools = generator.generate_tools()

        assert isinstance(tools, list)

    def test_tool_name_generation(self):
        """Test that tool names are properly formatted."""
        from opmanager_mcp.tool_generator import ToolGenerator

        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/api/json/device/listDevices": {
                    "get": {
                        "operationId": "listDevices",
                        "summary": "List devices",
                        "responses": {"200": {"description": "Success"}},
                    }
                }
            },
        }

        generator = ToolGenerator(spec)
        tools = generator.generate_tools()

        assert len(tools) > 0
        tool = tools[0]
        assert tool["name"].startswith("opmanager_")

    def test_tool_includes_parameters(self):
        """Test that tools include parameter definitions."""
        from opmanager_mcp.tool_generator import ToolGenerator

        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/api/json/device/getDevice": {
                    "get": {
                        "operationId": "getDevice",
                        "summary": "Get device by ID",
                        "parameters": [
                            {
                                "name": "deviceId",
                                "in": "query",
                                "required": True,
                                "schema": {"type": "integer"},
                                "description": "Device ID",
                            }
                        ],
                        "responses": {"200": {"description": "Success"}},
                    }
                }
            },
        }

        generator = ToolGenerator(spec)
        tools = generator.generate_tools()

        assert len(tools) == 1
        tool = tools[0]
        assert "inputSchema" in tool
        assert "properties" in tool["inputSchema"]
        assert "deviceId" in tool["inputSchema"]["properties"]

    def test_tool_description_includes_category(self):
        """Test that tool descriptions include category information."""
        from opmanager_mcp.tool_generator import ToolGenerator

        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "tags": [{"name": "device", "description": "Device operations"}],
            "paths": {
                "/api/json/device/listDevices": {
                    "get": {
                        "operationId": "listDevices",
                        "tags": ["device"],
                        "summary": "List all devices",
                        "responses": {"200": {"description": "Success"}},
                    }
                }
            },
        }

        generator = ToolGenerator(spec)
        tools = generator.generate_tools()

        assert len(tools) == 1
        tool = tools[0]
        # Check that description exists
        assert "description" in tool
        assert len(tool["description"]) > 0


class TestParameterHandling:
    """Tests for parameter handling in tool generation."""

    def test_enum_parameter(self):
        """Test handling of enum parameters."""
        from opmanager_mcp.tool_generator import ToolGenerator

        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/api/json/alarm/listAlarms": {
                    "get": {
                        "operationId": "listAlarms",
                        "summary": "List alarms",
                        "parameters": [
                            {
                                "name": "severity",
                                "in": "query",
                                "schema": {
                                    "type": "string",
                                    "enum": ["critical", "major", "minor", "warning"],
                                },
                                "description": "Alarm severity",
                            }
                        ],
                        "responses": {"200": {"description": "Success"}},
                    }
                }
            },
        }

        generator = ToolGenerator(spec)
        tools = generator.generate_tools()

        assert len(tools) == 1
        tool = tools[0]
        param_schema = tool["inputSchema"]["properties"]["severity"]
        assert "enum" in param_schema

    def test_required_parameters(self):
        """Test that required parameters are marked correctly."""
        from opmanager_mcp.tool_generator import ToolGenerator

        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/api/json/device/getDevice": {
                    "get": {
                        "operationId": "getDevice",
                        "summary": "Get device",
                        "parameters": [
                            {
                                "name": "deviceId",
                                "in": "query",
                                "required": True,
                                "schema": {"type": "integer"},
                            }
                        ],
                        "responses": {"200": {"description": "Success"}},
                    }
                }
            },
        }

        generator = ToolGenerator(spec)
        tools = generator.generate_tools()

        assert len(tools) == 1
        tool = tools[0]
        assert "required" in tool["inputSchema"]
        assert "deviceId" in tool["inputSchema"]["required"]
