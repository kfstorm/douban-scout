#!/bin/bash
set -e

echo "=== Running tests ==="
PYTHONPATH=. uv run pytest tests/ -v
