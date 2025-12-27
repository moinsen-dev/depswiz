#!/usr/bin/env bash
# Quick pre-commit check - faster than full CI
# Run this frequently during development

set -e

cd "$(dirname "$0")/.."

echo "🔍 Quick Check for depswiz"
echo ""

# Ruff check and format
echo "→ Ruff check..."
uv run ruff check src/depswiz --fix
echo "→ Ruff format..."
uv run ruff format src/depswiz

# Quick test run (no coverage)
echo "→ Running tests..."
uv run python -m pytest tests/ -q --tb=short -p no:cov 2>/dev/null || uv pip install pytest pytest-asyncio >/dev/null && uv run python -m pytest tests/ -q --tb=short -p no:cov

echo ""
echo "✅ Quick check passed!"
