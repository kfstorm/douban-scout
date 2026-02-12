#!/bin/bash
set -e

echo "=== Running tests ==="
uv run pytest tests/ -v
