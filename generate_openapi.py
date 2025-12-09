#!/usr/bin/env python3
"""
Script to parse OpManager Plus REST API HTML documentation and generate OpenAPI 3.0 specification.
"""

import json
import re
from html.parser import HTMLParser
from pathlib import Path


class APIEndpoint:
    def __init__(self):
        self.name = ""
        self.method = "GET"
        self.description = ""
        self.sample_url = ""
        self.sample_response = ""
        self.parameters = []  # List of {name, description, required, enum}
        self.path = ""
        self.category = ""


class OpManagerHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.endpoints = []
        self.current_endpoint = None
        self.current_category = ""
        self.current_section = ""  # Track what we're parsing
        self.capture_text = False
        self.text_buffer = ""
        self.in_param_table = False
        self.current_param = {}
        self.param_cell_index = 0
        self.div_depth = 0
        self.in_scroll_topic = False

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        # Track category headers
        if tag == "div" and "scroll-parent" in attrs_dict.get("class", ""):
            div_id = attrs_dict.get("id", "")
            if div_id and div_id not in ["GettingStarted"]:
                self.current_category = div_id

        # Track endpoint sections
        if tag == "div" and "scroll-topic" in attrs_dict.get("class", ""):
            self.in_scroll_topic = True
            endpoint_id = attrs_dict.get("id", "")
            if endpoint_id and endpoint_id not in ["Getting-Started", "enable"]:
                self.current_endpoint = APIEndpoint()
                self.current_endpoint.name = endpoint_id
                self.current_endpoint.category = self.current_category

        # Track method
        if tag == "b" and self.current_endpoint:
            self.capture_text = True
            self.current_section = "check_label"

        # Track code blocks for URLs and responses
        if tag == "code" and self.current_endpoint:
            self.capture_text = True
            self.current_section = "code"

        # Track parameter tables
        if tag == "div" and "divTableBody" in attrs_dict.get("class", ""):
            self.in_param_table = True

        if tag == "div" and "divTableRow" in attrs_dict.get("class", "") and self.in_param_table:
            self.current_param = {"name": "", "description": "", "required": False}
            self.param_cell_index = 0

        if tag == "div" and "divTableCell" in attrs_dict.get("class", "") and self.in_param_table:
            self.capture_text = True
            self.current_section = "param_cell"

    def handle_endtag(self, tag):
        if tag == "div" and self.in_scroll_topic:
            if self.current_endpoint and self.current_endpoint.name:
                # Extract path from sample URL
                if self.current_endpoint.sample_url:
                    self.current_endpoint.path = self.extract_path(self.current_endpoint.sample_url)
                if self.current_endpoint.path:
                    self.endpoints.append(self.current_endpoint)
                self.current_endpoint = None

        if tag == "div" and self.in_param_table:
            if self.current_section == "param_cell":
                self.param_cell_index += 1

        if tag == "code" and self.current_section == "code":
            self.capture_text = False
            text = self.text_buffer.strip()
            if self.current_endpoint:
                if "localhost" in text or "api/json" in text:
                    if not self.current_endpoint.sample_url:
                        self.current_endpoint.sample_url = text
                elif text and not self.current_endpoint.sample_response:
                    self.current_endpoint.sample_response = text
            self.text_buffer = ""
            self.current_section = ""

        if tag == "b" and self.current_section == "check_label":
            self.capture_text = False
            text = self.text_buffer.strip()
            if self.current_endpoint:
                if text == "Method:":
                    self.current_section = "method"
                    self.capture_text = True
                elif text == "Description:":
                    self.current_section = "description"
                    self.capture_text = True
            self.text_buffer = ""

    def handle_data(self, data):
        if self.capture_text:
            self.text_buffer += data

        # Capture method after "Method:" label
        if self.current_section == "method" and self.current_endpoint:
            method = data.strip()
            if method in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                self.current_endpoint.method = method
                self.current_section = ""
                self.capture_text = False

        # Capture description
        if self.current_section == "description" and self.current_endpoint:
            desc = data.strip()
            if desc:
                self.current_endpoint.description = desc
                self.current_section = ""
                self.capture_text = False

        # Capture parameter info
        if self.current_section == "param_cell" and self.current_endpoint and self.in_param_table:
            text = data.strip()
            if text and text != "Parameter name" and text != "Description":
                if self.param_cell_index == 0:
                    # Parameter name - check for * indicating required
                    name = text.replace("*", "").strip()
                    required = "*" in text
                    self.current_param["name"] = name
                    self.current_param["required"] = required
                else:
                    # Parameter description
                    self.current_param["description"] = text
                    if self.current_param["name"] and self.current_param["name"] != "apiKey":
                        self.current_endpoint.parameters.append(self.current_param.copy())
                    self.current_param = {}

    def extract_path(self, url):
        """Extract API path from sample URL."""
        # Match /api/json/... path
        match = re.search(r'(/api/json/[^\?&\s]+)', url)
        if match:
            return match.group(1)
        return ""


def parse_html_file(html_path):
    """Parse the HTML file and extract API endpoints."""
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Use regex to extract endpoints more reliably
    endpoints = []

    # First, build a map of endpoint positions to categories
    # Find all scroll-parent sections with their categories
    category_sections = re.finditer(r'<div id="([^"]+)" class="scroll-parent">', content)
    category_positions = []
    for match in category_sections:
        cat_name = match.group(1)
        if cat_name not in ["GettingStarted"]:
            category_positions.append((match.start(), cat_name))

    def get_category_for_position(pos):
        """Find the category for a given position in the file."""
        current_cat = ""
        for cat_pos, cat_name in category_positions:
            if cat_pos < pos:
                current_cat = cat_name
            else:
                break
        return current_cat

    # Find endpoint names and their details
    method_pattern = r'<b>Method:\s*</b>\s*(\w+)'
    desc_pattern = r'<b>Description:\s*</b>\s*([^<]+)'
    url_pattern = r'<b>Sample URL:\s*</b>\s*<code[^>]*>([^<]+)</code>'

    # Find all scroll-topic sections with their positions
    topic_matches = list(re.finditer(r'<div id="([^"]+)" class="scroll-topic">', content))

    for i, match in enumerate(topic_matches):
        endpoint_id = match.group(1)
        start_pos = match.end()

        # Determine end position (start of next topic or end of file)
        if i + 1 < len(topic_matches):
            end_pos = topic_matches[i + 1].start()
        else:
            end_pos = len(content)

        section_content = content[start_pos:end_pos]

        # Skip non-API sections
        if endpoint_id in ["Getting-Started", "enable", "GettingStarted"]:
            continue

        # Find category based on position
        current_category = get_category_for_position(match.start())

        endpoint = APIEndpoint()
        endpoint.name = endpoint_id
        endpoint.category = current_category

        # Extract method
        method_match = re.search(method_pattern, section_content)
        if method_match:
            endpoint.method = method_match.group(1).strip()

        # Extract description
        desc_match = re.search(desc_pattern, section_content)
        if desc_match:
            endpoint.description = desc_match.group(1).strip()

        # Extract sample URL
        url_match = re.search(url_pattern, section_content, re.DOTALL)
        if url_match:
            endpoint.sample_url = url_match.group(1).strip()
            # Clean up HTML entities
            endpoint.sample_url = endpoint.sample_url.replace('&amp;', '&')

        # Extract sample response
        response_pattern = r'<b>Sample Response:\s*</b>\s*<code>(.+?)</code>'
        response_match = re.search(response_pattern, section_content, re.DOTALL)
        if response_match:
            response_text = response_match.group(1).strip()
            # Clean up HTML entities
            response_text = response_text.replace('&quot;', '"')
            response_text = response_text.replace('&lt;', '<')
            response_text = response_text.replace('&gt;', '>')
            response_text = response_text.replace('&amp;', '&')
            # Remove extra whitespace
            response_text = re.sub(r'\s+', ' ', response_text).strip()
            endpoint.sample_response = response_text

        # Extract path from URL
        path_match = re.search(r'(/api/json[^\s\?&]+)', endpoint.sample_url)
        if path_match:
            endpoint.path = path_match.group(1)

        # Extract parameters from table - try multiple patterns
        # Pattern 1: Bold parameter name in cell followed by description cell
        param_rows = re.findall(
            r'<div class="divTableCell">\s*<b>([^<]+)</b>\s*</div>\s*<div class="divTableCell">([^<]*(?:<[^>]*>[^<]*)*?)</div>',
            section_content,
            re.DOTALL
        )

        # Pattern 2: If first pattern didn't work, try alternative
        if not param_rows:
            param_rows = re.findall(
                r'<div class="divTableRow">\s*<div class="divTableCell">\s*<b>([^<]+)</b>\s*</div>\s*<div class="divTableCell">(.+?)</div>\s*</div>',
                section_content,
                re.DOTALL
            )

        for param_name, param_desc in param_rows:
            param_name = param_name.strip()
            # Keep original for enum extraction, then clean
            param_desc_original = param_desc
            # Clean up HTML and whitespace from description
            param_desc = re.sub(r'<[^>]+>', '', param_desc)
            param_desc = re.sub(r'\s+', ' ', param_desc).strip()

            if param_name == "Parameter name" or param_name == "API":
                continue

            required = param_name.endswith('*')
            param_name = param_name.rstrip('*').strip()

            # Try to extract enum values from description
            enum_values = []

            # Pattern 1: Extract from <li> tags in original HTML
            li_values = re.findall(r'<li>\s*<b>([^<]+)</b>', param_desc_original)
            if li_values:
                enum_values = [v.strip() for v in li_values if v.strip()]

            # Pattern 2: "can be any of the following: value1, value2, value3"
            if not enum_values:
                enum_match = re.search(r'(?:can be any of the following|could be any of|following values?):\s*([^.]+)', param_desc, re.IGNORECASE)
                if enum_match:
                    enum_text = enum_match.group(1)
                    # Extract values separated by comma
                    enum_values = [v.strip() for v in re.split(r'[,;]', enum_text) if v.strip()]

            # Pattern 3: "1 = Critical, 2 = Trouble" style
            if not enum_values:
                enum_match = re.findall(r'(\d+)\s*=\s*(\w+)', param_desc)
                if enum_match:
                    enum_values = [m[0] for m in enum_match]  # Use numeric values

            # Pattern 4: Check for common enum parameter names and extract from description
            if not enum_values and param_name.lower() in ['status', 'state', 'type', 'category']:
                # Look for patterns like "status can be: active, inactive"
                status_match = re.search(r'(?:can be|values?)[:=]\s*([^.]+)', param_desc, re.IGNORECASE)
                if status_match:
                    enum_text = status_match.group(1)
                    enum_values = [v.strip() for v in re.split(r'[,;/]', enum_text) if v.strip() and len(v.strip()) < 30]

            if param_name.lower() != "apikey":
                param_data = {
                    "name": param_name,
                    "description": param_desc,
                    "required": required
                }
                if enum_values:
                    param_data["enum"] = enum_values
                endpoint.parameters.append(param_data)

        if endpoint.path:
            endpoints.append(endpoint)

    return endpoints


def generate_openapi_spec(endpoints):
    """Generate OpenAPI 3.0 specification from parsed endpoints."""

    # Group endpoints by category
    categories = set(e.category for e in endpoints if e.category)

    openapi = {
        "openapi": "3.0.3",
        "info": {
            "title": "OpManager Plus REST API",
            "description": "REST API for OpManager Plus - Network monitoring and management solution. This API allows integration with 3rd party IT management/service desk software.",
            "version": "1.0.0",
            "contact": {
                "name": "ManageEngine OpManager Plus",
                "url": "https://www.manageengine.com/network-monitoring/"
            }
        },
        "servers": [
            {
                "url": "http://localhost:8060",
                "description": "OpManager Plus Server (HTTP)"
            },
            {
                "url": "https://localhost:8060",
                "description": "OpManager Plus Server (HTTPS)"
            }
        ],
        "security": [
            {"apiKeyHeader": []},
            {"apiKeyQuery": []}
        ],
        "tags": [],
        "paths": {},
        "components": {
            "securitySchemes": {
                "apiKeyHeader": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "apiKey",
                    "description": "API Key for authentication (preferred method)"
                },
                "apiKeyQuery": {
                    "type": "apiKey",
                    "in": "query",
                    "name": "apiKey",
                    "description": "API Key as query parameter (deprecated for some endpoints)"
                }
            },
            "schemas": {
                "SuccessResponse": {
                    "type": "object",
                    "properties": {
                        "result": {
                            "type": "object",
                            "properties": {
                                "message": {
                                    "type": "string"
                                }
                            }
                        }
                    }
                },
                "ErrorResponse": {
                    "type": "object",
                    "properties": {
                        "error": {
                            "type": "object",
                            "properties": {
                                "message": {
                                    "type": "string"
                                },
                                "code": {
                                    "type": "integer"
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    # Add tags
    for category in sorted(categories):
        if category:
            openapi["tags"].append({
                "name": category,
                "description": f"{category} related operations"
            })

    # Add paths
    for endpoint in endpoints:
        path = endpoint.path
        if not path:
            continue

        if path not in openapi["paths"]:
            openapi["paths"][path] = {}

        method = endpoint.method.lower()

        operation = {
            "operationId": endpoint.name,
            "summary": endpoint.name,
            "description": endpoint.description or f"{endpoint.name} operation",
            "tags": [endpoint.category] if endpoint.category else [],
            "parameters": [],
            "responses": {
                "200": {
                    "description": "Successful response",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object"
                            }
                        }
                    }
                },
                "400": {
                    "description": "Bad request",
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/ErrorResponse"
                            }
                        }
                    }
                },
                "401": {
                    "description": "Unauthorized - Invalid or missing API key",
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/ErrorResponse"
                            }
                        }
                    }
                }
            }
        }

        # Add sample response as example if available
        if endpoint.sample_response:
            try:
                # Try to parse as JSON to include as proper example
                import json as json_module
                example_data = json_module.loads(endpoint.sample_response)
                operation["responses"]["200"]["content"]["application/json"]["example"] = example_data
            except (json_module.JSONDecodeError, ValueError):
                # If not valid JSON, include as string example
                operation["responses"]["200"]["content"]["application/json"]["example"] = endpoint.sample_response

        # Add parameters
        for param in endpoint.parameters:
            param_spec = {
                "name": param["name"],
                "in": "query",
                "required": param.get("required", False),
                "description": param.get("description", ""),
                "schema": {
                    "type": "string"
                }
            }

            # Infer type from description or name
            param_name_lower = param["name"].lower()
            param_desc_lower = param.get("description", "").lower()

            if any(word in param_name_lower for word in ["id", "count", "interval", "port", "severity", "status"]):
                param_spec["schema"]["type"] = "integer"
            elif any(word in param_desc_lower for word in ["true or false", "true/false", "boolean"]):
                param_spec["schema"]["type"] = "boolean"

            # Add enum values if available
            if param.get("enum"):
                param_spec["schema"]["enum"] = param["enum"]

            operation["parameters"].append(param_spec)

        openapi["paths"][path][method] = operation

    return openapi


def main():
    """Main function to generate OpenAPI spec."""
    script_dir = Path(__file__).parent
    html_path = script_dir / "rest-api.html"
    output_path = script_dir / "openapi.json"

    print(f"Parsing HTML file: {html_path}")

    if not html_path.exists():
        print(f"Error: {html_path} not found")
        return

    endpoints = parse_html_file(html_path)
    print(f"Found {len(endpoints)} API endpoints")

    # Print summary by category
    categories = {}
    for ep in endpoints:
        cat = ep.category or "Uncategorized"
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(ep.name)

    print("\nEndpoints by category:")
    for cat in sorted(categories.keys()):
        print(f"  {cat}: {len(categories[cat])} endpoints")
        for name in categories[cat]:
            print(f"    - {name}")

    # Generate OpenAPI spec
    openapi = generate_openapi_spec(endpoints)

    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(openapi, f, indent=2)

    print(f"\nOpenAPI specification written to: {output_path}")
    print(f"Total paths: {len(openapi['paths'])}")


if __name__ == "__main__":
    main()
