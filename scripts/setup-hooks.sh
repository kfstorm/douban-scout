#!/bin/bash
set -e

# Get the root directory of the project
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

echo "=== Setting up Git pre-commit hooks ==="

if ! command -v pre-commit >/dev/null 2>&1; then
    echo "Error: 'pre-commit' is not installed."
    echo "Please install it first using one of the following commands:"
    echo "  pip install pre-commit"
    echo "  brew install pre-commit"
    exit 1
fi

pre-commit install

echo ""
echo "=== Git pre-commit hooks installed successfully! ==="
