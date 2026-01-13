#!/bin/bash

# OpManager MCP Server Startup Script
# This script provides an easy way to start the MCP server in different modes

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/venv"
DEFAULT_HOST="0.0.0.0"
DEFAULT_PORT="3000"

# Functions
print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

show_usage() {
    cat << EOF
Usage: $0 [MODE] [OPTIONS]

MODES:
    http        Start HTTP/SSE server (default)
    stdio       Start stdio server for Claude Desktop
    help        Show this help message

HTTP OPTIONS:
    --host      Host to bind to (default: ${DEFAULT_HOST})
    --port      Port to bind to (default: ${DEFAULT_PORT})
    --reload    Enable auto-reload for development

EXAMPLES:
    $0                              # Start HTTP server on 0.0.0.0:3000
    $0 http                         # Start HTTP server on 0.0.0.0:3000
    $0 http --port 8080             # Start HTTP server on port 8080
    $0 http --host 127.0.0.1        # Start HTTP server on localhost only
    $0 http --reload                # Start with auto-reload (development)
    $0 stdio                        # Start stdio server

EOF
}

check_venv() {
    if [ ! -d "${VENV_DIR}" ]; then
        print_error "Virtual environment not found at ${VENV_DIR}"
        print_info "Creating virtual environment..."
        python3 -m venv "${VENV_DIR}"
    fi
}

activate_venv() {
    print_info "Activating virtual environment..."
    if [ -f "${VENV_DIR}/bin/activate" ]; then
        source "${VENV_DIR}/bin/activate"
    else
        print_error "Could not find venv activation script"
        exit 1
    fi
}

check_dependencies() {
    print_info "Checking dependencies..."
    if ! "${VENV_DIR}/bin/python" -c "import opmanager_mcp" 2>/dev/null; then
        print_warning "Package not installed. Installing..."
        "${VENV_DIR}/bin/pip" install -e "${SCRIPT_DIR}[http]"
    fi
    print_success "Dependencies OK"
}

start_http_server() {
    local host="${1:-${DEFAULT_HOST}}"
    local port="${2:-${DEFAULT_PORT}}"
    local reload_flag="$3"

    print_success "Starting OpManager MCP HTTP Server"
    print_info "Host: ${host}"
    print_info "Port: ${port}"
    print_info "Access URL: http://localhost:${port}"
    print_info ""
    print_info "Press Ctrl+C to stop the server"
    print_info ""

    if [ -n "${reload_flag}" ]; then
        "${VENV_DIR}/bin/python" -m uvicorn opmanager_mcp.http_server:app --host "${host}" --port "${port}" --reload
    else
        "${VENV_DIR}/bin/python" -m uvicorn opmanager_mcp.http_server:app --host "${host}" --port "${port}"
    fi
}

start_stdio_server() {
    print_success "Starting OpManager MCP Server (stdio mode)"
    print_info "This mode is for Claude Desktop integration"
    print_info "Press Ctrl+C to stop the server"
    print_info ""

    "${VENV_DIR}/bin/python" -m opmanager_mcp
}

# Main script
main() {
    cd "${SCRIPT_DIR}"

    # Parse mode
    MODE="${1:-http}"
    shift || true

    # Show help
    if [ "${MODE}" = "help" ] || [ "${MODE}" = "-h" ] || [ "${MODE}" = "--help" ]; then
        show_usage
        exit 0
    fi

    # Parse options
    HOST="${DEFAULT_HOST}"
    PORT="${DEFAULT_PORT}"
    RELOAD=""

    while [ $# -gt 0 ]; do
        case "$1" in
            --host)
                HOST="$2"
                shift 2
                ;;
            --port)
                PORT="$2"
                shift 2
                ;;
            --reload)
                RELOAD="--reload"
                shift
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done

    # Setup environment
    check_venv
    activate_venv
    check_dependencies

    # Start server based on mode
    case "${MODE}" in
        http)
            start_http_server "${HOST}" "${PORT}" "${RELOAD}"
            ;;
        stdio)
            start_stdio_server
            ;;
        *)
            print_error "Unknown mode: ${MODE}"
            show_usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
