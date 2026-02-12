#!/bin/bash
set -e

# Change to script directory (backend)
cd "$(dirname "$0")/.."

echo "=== Running Ruff linter ==="
uv run ruff check app/

echo ""
echo "=== Running Ruff formatter (check mode) ==="
uv run ruff format --check app/

echo ""
echo "=== Running MyPy type checker ==="
uv run mypy app/

echo ""
echo "=== All checks passed! ==="
