#!/bin/bash
set -e

# Get the root directory of the project
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

echo "=== Fixing Backend ==="
if [ -d "backend" ]; then
    bash backend/scripts/format.sh
fi

echo ""
echo "=== Fixing Frontend ==="
if [ -d "frontend" ]; then
    npm --prefix frontend run lint:fix
    npm --prefix frontend run format
fi

echo ""
echo "=== Fixing Markdown ==="
# Try to use markdownlint-cli2 to fix markdown files
if command -v markdownlint-cli2 >/dev/null 2>&1; then
    markdownlint-cli2 --fix "**/*.md"
elif command -v npx >/dev/null 2>&1; then
    npx markdownlint-cli2 --fix "**/*.md"
else
    echo "Warning: markdownlint-cli2 not found. Skipping markdown fix."
fi

echo ""
echo "=== All fixes applied! ==="
