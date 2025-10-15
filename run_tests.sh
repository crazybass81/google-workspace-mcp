#!/bin/bash

# Google Workspace MCP Server - Test Runner Script

set -e

echo "=================================="
echo "Google Workspace MCP Test Suite"
echo "=================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if pytest is installed
if ! python3 -m pytest --version &> /dev/null; then
    echo -e "${RED}Error: pytest not found${NC}"
    echo "Install with: pip3 install pytest pytest-asyncio pytest-cov"
    exit 1
fi

# Default mode
MODE=${1:-"all"}

case "$MODE" in
    "all")
        echo -e "${YELLOW}Running all tests...${NC}"
        python3 -m pytest tests/ -v --tb=short --cov=src --cov-report=term-missing
        ;;

    "quick")
        echo -e "${YELLOW}Running quick integration tests...${NC}"
        python3 -m pytest tests/test_integration.py -v --tb=short
        ;;

    "drive")
        echo -e "${YELLOW}Running Drive service tests...${NC}"
        python3 -m pytest tests/test_drive_service.py -v --tb=short
        ;;

    "docs")
        echo -e "${YELLOW}Running Docs service tests...${NC}"
        python3 -m pytest tests/test_docs_service.py -v --tb=short
        ;;

    "sheets")
        echo -e "${YELLOW}Running Sheets service tests...${NC}"
        python3 -m pytest tests/test_sheets_service.py -v --tb=short
        ;;

    "slides")
        echo -e "${YELLOW}Running Slides service tests...${NC}"
        python3 -m pytest tests/test_slides_service.py -v --tb=short
        ;;

    "forms")
        echo -e "${YELLOW}Running Forms service tests...${NC}"
        python3 -m pytest tests/test_forms_service.py -v --tb=short
        ;;

    "gmail")
        echo -e "${YELLOW}Running Gmail service tests...${NC}"
        python3 -m pytest tests/test_gmail_service.py -v --tb=short
        ;;

    "coverage")
        echo -e "${YELLOW}Running tests with full coverage report...${NC}"
        python3 -m pytest tests/ --cov=src --cov-report=html --cov-report=term-missing
        echo ""
        echo -e "${GREEN}Coverage report generated: htmlcov/index.html${NC}"
        ;;

    "integration")
        echo -e "${YELLOW}Running integration tests...${NC}"
        python3 -m pytest tests/test_integration.py -v --tb=short
        ;;

    "tools")
        echo -e "${YELLOW}Verifying all 34 MCP tools...${NC}"
        python3 -m pytest tests/test_integration.py::TestMCPIntegration::test_all_tools_registered -v
        python3 -m pytest tests/test_integration.py::TestMCPIntegration::test_tool_schemas -v
        ;;

    "help")
        echo "Usage: ./run_tests.sh [MODE]"
        echo ""
        echo "Modes:"
        echo "  all         - Run all tests (default)"
        echo "  quick       - Run quick integration tests"
        echo "  drive       - Run Drive service tests"
        echo "  docs        - Run Docs service tests"
        echo "  sheets      - Run Sheets service tests"
        echo "  slides      - Run Slides service tests"
        echo "  forms       - Run Forms service tests"
        echo "  gmail       - Run Gmail service tests"
        echo "  integration - Run integration tests"
        echo "  tools       - Verify all 34 MCP tools"
        echo "  coverage    - Run with HTML coverage report"
        echo "  help        - Show this help message"
        ;;

    *)
        echo -e "${RED}Unknown mode: $MODE${NC}"
        echo "Run './run_tests.sh help' for usage information"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}Tests completed!${NC}"
