#!/usr/bin/env bash
# Local CI dry-run script - mirrors GitHub Actions workflow
# Run this before pushing to catch issues early

set -e  # Exit on first error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Track overall status
FAILED=0

print_header() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
    FAILED=1
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Change to project root
cd "$(dirname "$0")/.."

print_header "depswiz Local CI Check"
echo "This script mirrors the GitHub Actions CI workflow"
echo "Running from: $(pwd)"

# 1. Sync dependencies
print_header "Step 1: Sync Dependencies"
if uv sync --dev 2>&1; then
    print_success "Dependencies synced"
else
    print_error "Failed to sync dependencies"
fi

# 2. Ruff linting
print_header "Step 2: Ruff Lint Check"
if uv run ruff check src/depswiz 2>&1; then
    print_success "Ruff lint passed"
else
    print_error "Ruff lint failed"
fi

# 3. Ruff formatting
print_header "Step 3: Ruff Format Check"
if uv run ruff format --check src/depswiz 2>&1; then
    print_success "Ruff format passed"
else
    print_error "Ruff format failed (run 'uv run ruff format src/depswiz' to fix)"
fi

# 4. Mypy type checking
print_header "Step 4: Mypy Type Check"
# Install mypy if not present
uv pip install mypy types-PyYAML >/dev/null 2>&1 || true
if uv run python -m mypy src/depswiz --ignore-missing-imports 2>&1; then
    print_success "Mypy passed"
else
    print_warning "Mypy has warnings (non-blocking in CI)"
fi

# 5. Run tests
print_header "Step 5: Run Tests"
# Install pytest and coverage if not present
uv pip install pytest pytest-asyncio pytest-cov coverage >/dev/null 2>&1 || true
# Override addopts to avoid coverage issues
if uv run python -m pytest tests/ -v --tb=short --override-ini="addopts=" 2>&1; then
    print_success "All tests passed"
else
    print_error "Tests failed"
fi

# 6. Build package
print_header "Step 6: Build Package"
if uv build 2>&1; then
    print_success "Package built successfully"
    ls -la dist/
else
    print_error "Package build failed"
fi

# 7. Pre-commit (optional, if installed)
print_header "Step 7: Pre-commit Hooks (optional)"
if command -v pre-commit &> /dev/null; then
    if pre-commit run --all-files 2>&1; then
        print_success "Pre-commit passed"
    else
        print_warning "Pre-commit has issues"
    fi
else
    print_warning "pre-commit not installed (run 'pip install pre-commit && pre-commit install')"
fi

# Summary
print_header "Summary"
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}"
    echo "  ╔═══════════════════════════════════════════════════════════════╗"
    echo "  ║                                                               ║"
    echo "  ║   ✓ All CI checks passed! Ready to push to GitHub.           ║"
    echo "  ║                                                               ║"
    echo "  ╚═══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    exit 0
else
    echo -e "${RED}"
    echo "  ╔═══════════════════════════════════════════════════════════════╗"
    echo "  ║                                                               ║"
    echo "  ║   ✗ Some CI checks failed. Please fix before pushing.        ║"
    echo "  ║                                                               ║"
    echo "  ╚═══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    exit 1
fi
