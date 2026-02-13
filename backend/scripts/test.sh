#!/bin/bash
set -e

# Change to script directory (backend)
cd "$(dirname "$0")/.."

echo "=== Running tests ==="
PYTHONPATH=. uv run pytest tests/ -v
