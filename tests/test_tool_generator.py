"""Tests for the tool generator."""

from __future__ import annotations

import pytest


class TestToolGenerator:
    """Tests for the tool generator."""

    def test_generate_tools_from_spec(self, sample_openapi_spec):
        """Test generating tools from OpenAPI spec."""
        from opmanager_mcp.tool_generator import ToolGenerator

        generator = ToolGenerator(sample_openapi_spec)
        tools = generator.generate_tools()

        # Should generate tools for paths with GET method
        assert isinstance(tools, list)

    def test_tool_name_generation(self):
        """Test that tool names are generated correctly."""
        from opmanager_mcp.tool_generator import ToolGenerator

        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/api/json/device/listDevices": {
                    "get": {
                        "operationId": "listDevices",
                        "summary": "List all devices",
                        "parameters": [],
                        "responses": {"200": {"description": "Success"}},
                    }
                }
            },
        }

        generator = ToolGenerator(spec)
        tools = generator.generate_tools()

        assert len(tools) == 1
        # Tool name should be the operationId
        assert tools[0]["name"] == "listDevices"

    def test_tool_includes_parameters(self):
        """Test that tools include parameters."""
        from opmanager_mcp.tool_generator import ToolGenerator

        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/api/json/device/getDevice": {
                    "get": {
                        "operationId": "getDevice",
                        "summary": "Get device by name",
                        "parameters": [
                            {
                                "name": "deviceName",
                                "in": "query",
                                "required": True,
                                "description": "The device name",
                                "schema": {"type": "string"},
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
        input_schema = tools[0]["inputSchema"]

        # Should include host and apiKey as required
        assert "host" in input_schema["properties"]
        assert "apiKey" in input_schema["properties"]
        # Should include the deviceName parameter
        assert "deviceName" in input_schema["properties"]

    def test_tool_description_includes_category(self):
        """Test that tool descriptions include category info."""
        from opmanager_mcp.tool_generator import ToolGenerator

        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/api/json/alarm/listAlarms": {
                    "get": {
                        "operationId": "listAlarms",
                        "summary": "List all alarms",
                        "parameters": [],
                        "responses": {"200": {"description": "Success"}},
                    }
                }
            },
        }

        generator = ToolGenerator(spec)
        tools = generator.generate_tools()

        assert len(tools) == 1
        # Description should include category context for alarms
        assert "alarm" in tools[0]["description"].lower()

    def test_allowed_methods_filter(self):
        """Test that only allowed methods generate tools."""
        from opmanager_mcp.tool_generator import ToolGenerator

        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/api/json/device/listDevices": {
                    "get": {
                        "operationId": "listDevices",
                        "summary": "List all devices",
                    },
                    "post": {
                        "operationId": "addDevice",
                        "summary": "Add a device",
                    },
                }
            },
        }

        # Only GET methods
        generator = ToolGenerator(spec, allowed_methods=["GET"])
        tools = generator.generate_tools()

        tool_names = [t["name"] for t in tools]
        assert "listDevices" in tool_names
        assert "addDevice" not in tool_names

        # Both GET and POST
        generator = ToolGenerator(spec, allowed_methods=["GET", "POST"])
        tools = generator.generate_tools()

        tool_names = [t["name"] for t in tools]
        assert "listDevices" in tool_names
        assert "addDevice" in tool_names


class TestParameterHandling:
    """Tests for parameter handling in tool generation."""

    def test_enum_parameter(self):
        """Test that enum parameters are handled correctly."""
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
                                "required": False,
                                "description": "Alarm severity",
                                "schema": {
                                    "type": "integer",
                                    "enum": [1, 2, 3, 4, 5],
                                },
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
        severity_prop = tools[0]["inputSchema"]["properties"]["severity"]
        assert "enum" in severity_prop

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
                                "name": "deviceName",
                                "in": "query",
                                "required": True,
                                "description": "Device name",
                                "schema": {"type": "string"},
                            },
                            {
                                "name": "includeDetails",
                                "in": "query",
                                "required": False,
                                "description": "Include details",
                                "schema": {"type": "boolean"},
                            },
                        ],
                        "responses": {"200": {"description": "Success"}},
                    }
                }
            },
        }

        generator = ToolGenerator(spec)
        tools = generator.generate_tools()

        required = tools[0]["inputSchema"]["required"]
        # host and apiKey are always required
        assert "host" in required
        assert "apiKey" in required
        # deviceName should be required
        assert "deviceName" in required
        # includeDetails should NOT be required
        assert "includeDetails" not in required
