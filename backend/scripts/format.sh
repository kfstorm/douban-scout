#!/bin/bash
set -e

# Change to script directory (backend)
cd "$(dirname "$0")/.."

echo "=== Auto-fixing with Ruff ==="
uv run ruff check --fix app/

echo ""
echo "=== Formatting with Ruff ==="
uv run ruff format app/

echo ""
echo "=== Done! ==="
