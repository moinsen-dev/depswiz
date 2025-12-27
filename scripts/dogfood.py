#!/usr/bin/env python3
"""Dogfooding script - depswiz checks itself.

This script runs depswiz commands against its own codebase to verify
functionality works correctly in a real-world scenario.

Usage:
    python scripts/dogfood.py
    python scripts/dogfood.py --verbose
    python scripts/dogfood.py --quick  # Skip slow operations
"""

import subprocess
import sys
from pathlib import Path

# Colors for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"


def run_command(name: str, cmd: list[str], expected_exit: int = 0, allow_fail: bool = False) -> bool:
    """Run a command and check the result."""
    print(f"\n{BLUE}{BOLD}[TEST]{RESET} {name}")
    print(f"  Command: {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).parent.parent)

    if result.returncode == expected_exit:
        print(f"  {GREEN}PASS{RESET} (exit code: {result.returncode})")
        if "--verbose" in sys.argv and result.stdout:
            for line in result.stdout.strip().split("\n")[:10]:
                print(f"    {line}")
            if result.stdout.count("\n") > 10:
                print(f"    ... ({result.stdout.count(chr(10)) - 10} more lines)")
        return True
    elif allow_fail:
        print(f"  {YELLOW}SKIP{RESET} (exit code: {result.returncode}, allowed to fail)")
        if result.stderr:
            print(f"    {result.stderr.strip()[:200]}")
        return True
    else:
        print(f"  {RED}FAIL{RESET} (expected: {expected_exit}, got: {result.returncode})")
        if result.stderr:
            print(f"  stderr: {result.stderr.strip()[:500]}")
        if result.stdout:
            print(f"  stdout: {result.stdout.strip()[:500]}")
        return False


def main() -> int:
    """Run dogfooding tests."""
    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}  depswiz Dogfooding Test Suite{RESET}")
    print(f"{BOLD}{'='*60}{RESET}")

    quick_mode = "--quick" in sys.argv
    results: list[tuple[str, bool]] = []

    # Base command - use uv run to ensure we're using the local version
    base = ["uv", "run", "depswiz"]

    # ============================================================
    # Basic CLI tests
    # ============================================================
    print(f"\n{YELLOW}{BOLD}--- Basic CLI Tests ---{RESET}")

    results.append(("Version flag", run_command(
        "Show version with --version flag",
        [*base, "--version"],
    )))

    results.append(("Version short", run_command(
        "Show version with -V flag",
        [*base, "-V"],
    )))

    results.append(("Help", run_command(
        "Show help",
        [*base, "--help"],
    )))

    results.append(("Check help", run_command(
        "Check command help",
        [*base, "check", "--help"],
    )))

    results.append(("Audit help", run_command(
        "Audit command help",
        [*base, "audit", "--help"],
    )))

    results.append(("Tools help", run_command(
        "Tools command help",
        [*base, "tools", "--help"],
    )))

    # ============================================================
    # Check command tests
    # ============================================================
    print(f"\n{YELLOW}{BOLD}--- Check Command Tests ---{RESET}")

    results.append(("Check (default)", run_command(
        "Check dependencies (default format)",
        [*base, "check", "."],
    )))

    results.append(("Check JSON", run_command(
        "Check dependencies (JSON format)",
        [*base, "check", "--format", "json", "."],
    )))

    results.append(("Check Markdown", run_command(
        "Check dependencies (Markdown format)",
        [*base, "check", "--format", "markdown", "."],
    )))

    results.append(("Check Python only", run_command(
        "Check Python dependencies only",
        [*base, "check", "--language", "python", "."],
    )))

    # ============================================================
    # Audit command tests
    # ============================================================
    print(f"\n{YELLOW}{BOLD}--- Audit Command Tests ---{RESET}")

    if not quick_mode:
        # Audit may find vulnerabilities, so allow non-zero exit
        results.append(("Audit (default)", run_command(
            "Audit for vulnerabilities",
            [*base, "audit", "."],
            expected_exit=0,
            allow_fail=True,  # May find vulnerabilities
        )))

        results.append(("Audit JSON", run_command(
            "Audit (JSON format)",
            [*base, "audit", "--format", "json", "."],
            expected_exit=0,
            allow_fail=True,
        )))

        results.append(("Audit severity filter", run_command(
            "Audit with severity filter",
            [*base, "audit", "--severity", "high", "."],
            expected_exit=0,
            allow_fail=True,
        )))
    else:
        print(f"  {YELLOW}SKIPPED{RESET} (quick mode)")

    # ============================================================
    # Licenses command tests
    # ============================================================
    print(f"\n{YELLOW}{BOLD}--- Licenses Command Tests ---{RESET}")

    results.append(("Licenses (default)", run_command(
        "Check licenses",
        [*base, "licenses", "."],
    )))

    results.append(("Licenses JSON", run_command(
        "Check licenses (JSON format)",
        [*base, "licenses", "--format", "json", "."],
    )))

    results.append(("Licenses summary", run_command(
        "Check licenses (summary only)",
        [*base, "licenses", "--summary", "."],
    )))

    # ============================================================
    # SBOM command tests
    # ============================================================
    print(f"\n{YELLOW}{BOLD}--- SBOM Command Tests ---{RESET}")

    results.append(("SBOM CycloneDX", run_command(
        "Generate CycloneDX SBOM",
        [*base, "sbom", "--format", "cyclonedx", "."],
    )))

    results.append(("SBOM SPDX", run_command(
        "Generate SPDX SBOM",
        [*base, "sbom", "--format", "spdx", "."],
    )))

    # ============================================================
    # Tools command tests
    # ============================================================
    print(f"\n{YELLOW}{BOLD}--- Tools Command Tests ---{RESET}")

    results.append(("Tools (auto-detect)", run_command(
        "Check tools (auto-detect)",
        [*base, "tools", "."],
    )))

    results.append(("Tools JSON", run_command(
        "Check tools (JSON format)",
        [*base, "tools", "--format", "json", "."],
    )))

    results.append(("Tools specific", run_command(
        "Check specific tools",
        [*base, "tools", "--tool", "python", "--tool", "uv", "."],
    )))

    results.append(("Tools updates only", run_command(
        "Check tools (updates only)",
        [*base, "tools", "--updates-only", "."],
    )))

    # ============================================================
    # Plugins command tests
    # ============================================================
    print(f"\n{YELLOW}{BOLD}--- Plugins Command Tests ---{RESET}")

    results.append(("Plugins list", run_command(
        "List plugins",
        [*base, "plugins", "list"],
    )))

    results.append(("Plugin info Python", run_command(
        "Plugin info (Python)",
        [*base, "plugins", "info", "python"],
    )))

    results.append(("Plugin info Rust", run_command(
        "Plugin info (Rust)",
        [*base, "plugins", "info", "rust"],
    )))

    # ============================================================
    # Output format tests
    # ============================================================
    print(f"\n{YELLOW}{BOLD}--- Output Format Tests ---{RESET}")

    results.append(("HTML output", run_command(
        "Check with HTML output",
        [*base, "check", "--format", "html", "."],
    )))

    # ============================================================
    # Verbose/Quiet flags (must come BEFORE the subcommand)
    # ============================================================
    print(f"\n{YELLOW}{BOLD}--- Verbose/Quiet Flag Tests ---{RESET}")

    results.append(("Verbose mode", run_command(
        "Check with verbose flag (global option before subcommand)",
        [*base, "--verbose", "check", "."],
    )))

    results.append(("Verbose short", run_command(
        "Check with -v flag",
        [*base, "-v", "check", "."],
    )))

    results.append(("Quiet mode", run_command(
        "Check with quiet flag (global option before subcommand)",
        [*base, "--quiet", "check", "."],
    )))

    results.append(("Quiet short", run_command(
        "Check with -q flag",
        [*base, "-q", "check", "."],
    )))

    # ============================================================
    # Summary
    # ============================================================
    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}  Test Results Summary{RESET}")
    print(f"{BOLD}{'='*60}{RESET}\n")

    passed = sum(1 for _, success in results if success)
    failed = sum(1 for _, success in results if not success)
    total = len(results)

    for name, success in results:
        status = f"{GREEN}PASS{RESET}" if success else f"{RED}FAIL{RESET}"
        print(f"  [{status}] {name}")

    print(f"\n{BOLD}Total:{RESET} {passed}/{total} passed", end="")
    if failed > 0:
        print(f", {RED}{failed} failed{RESET}")
    else:
        print(f" {GREEN}All tests passed!{RESET}")

    print()
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
