"""Deprecation scanner using dart analyze."""

from __future__ import annotations

import asyncio
import re
import shutil
from collections.abc import Callable
from pathlib import Path

from depswiz.deprecations.models import (
    Deprecation,
    DeprecationResult,
    DeprecationStatus,
)


async def scan_deprecations(
    path: Path,
    include_internal: bool = True,
    progress_callback: Callable[[str], None] | None = None,
) -> DeprecationResult:
    """Scan a Flutter/Dart project for deprecation warnings.

    Uses `dart analyze` to detect deprecated API usage.

    Args:
        path: Project path to analyze
        include_internal: Include deprecations from same package
        progress_callback: Optional progress callback

    Returns:
        DeprecationResult with all found deprecations
    """
    result = DeprecationResult(path=path)

    # Check if dart is available
    dart_path = shutil.which("dart")
    if not dart_path:
        # Try flutter dart
        flutter_path = shutil.which("flutter")
        if flutter_path:
            dart_path = "flutter"
        else:
            return result  # No dart available

    # Get dart version
    if progress_callback:
        progress_callback("Getting Dart version...")
    result.dart_version = await _get_dart_version(dart_path)
    result.flutter_version = await _get_flutter_version()

    # Run dart analyze
    if progress_callback:
        progress_callback("Running dart analyze...")
    analyze_output = await _run_dart_analyze(path, dart_path)

    # Parse deprecation warnings
    if progress_callback:
        progress_callback("Parsing results...")
    deprecations = _parse_analyze_output(analyze_output, path, include_internal)
    result.deprecations = deprecations

    # Check which are auto-fixable
    if progress_callback:
        progress_callback("Checking auto-fix availability...")
    fixable_rules = await _get_fixable_rules(path, dart_path)
    for dep in result.deprecations:
        if dep.rule_id in fixable_rules:
            dep.fix_available = True
            result.fixable_count += 1

    return result


async def _get_dart_version(dart_path: str) -> str | None:
    """Get Dart SDK version."""
    try:
        proc = await asyncio.create_subprocess_exec(
            dart_path,
            "--version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        output = (stdout or stderr).decode().strip()
        # Parse "Dart SDK version: 3.2.0 (stable) ..."
        match = re.search(r"Dart SDK version:\s*(\S+)", output)
        if match:
            return match.group(1)
        # Flutter outputs differently
        match = re.search(r"Dart\s+(\d+\.\d+\.\d+)", output)
        if match:
            return match.group(1)
    except Exception:
        pass
    return None


async def _get_flutter_version() -> str | None:
    """Get Flutter SDK version if available."""
    flutter_path = shutil.which("flutter")
    if not flutter_path:
        return None
    try:
        proc = await asyncio.create_subprocess_exec(
            flutter_path,
            "--version",
            "--machine",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        import json

        data = json.loads(stdout.decode())
        return data.get("frameworkVersion")
    except Exception:
        pass
    return None


async def _run_dart_analyze(path: Path, dart_path: str) -> str:
    """Run dart analyze and return output."""
    # Use machine-readable format if available
    proc = await asyncio.create_subprocess_exec(
        dart_path,
        "analyze",
        "--format=machine",
        str(path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=str(path),
    )
    stdout, stderr = await proc.communicate()
    # Combine stdout and stderr as analyze writes to stderr
    return stdout.decode() + stderr.decode()


def _parse_analyze_output(
    output: str,
    project_path: Path,
    include_internal: bool,
) -> list[Deprecation]:
    """Parse dart analyze machine-readable output.

    Machine format: SEVERITY|TYPE|ERROR_CODE|FILE|LINE|COLUMN|LENGTH|MESSAGE
    Example: WARNING|DEPRECATED_MEMBER_USE|deprecated_member_use|lib/main.dart|10|5|12|'oldMethod' is deprecated...
    """
    deprecations: list[Deprecation] = []
    deprecation_rules = {
        "deprecated_member_use",
        "deprecated_member_use_from_same_package",
    }

    for line in output.strip().split("\n"):
        if not line or "|" not in line:
            continue

        parts = line.split("|")
        if len(parts) < 8:
            continue

        severity, _error_type, rule_id, file_path, line_num, column, _length, *message_parts = parts
        message = "|".join(message_parts)  # Message might contain |

        # Filter to deprecation rules
        if rule_id not in deprecation_rules:
            continue

        # Skip internal if not requested
        if not include_internal and rule_id == "deprecated_member_use_from_same_package":
            continue

        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.is_absolute():
                file_path_obj = project_path / file_path_obj

            deprecation = Deprecation(
                rule_id=rule_id,
                message=message.strip(),
                file_path=file_path_obj,
                line=int(line_num),
                column=int(column),
                status=DeprecationStatus.from_analyzer_severity(severity),
            )

            # Try to extract replacement from message
            replacement = _extract_replacement(message)
            if replacement:
                deprecation.replacement = replacement

            # Try to extract package from message
            package = _extract_package(message)
            if package:
                deprecation.package = package

            deprecations.append(deprecation)
        except (ValueError, TypeError):
            continue

    return deprecations


def _extract_replacement(message: str) -> str | None:
    """Extract replacement suggestion from deprecation message.

    Common patterns:
    - "Use 'newThing' instead"
    - "Try using 'newThing' instead"
    - "'oldThing' is deprecated. Use 'newThing'."
    """
    patterns = [
        r"[Uu]se\s+'([^']+)'\s+instead",
        r"[Uu]se\s+`([^`]+)`\s+instead",
        r"[Rr]eplace\s+with\s+'([^']+)'",
        r"[Rr]eplace\s+with\s+`([^`]+)`",
        r"[Mm]igrate\s+to\s+'([^']+)'",
        r"[Mm]igrate\s+to\s+`([^`]+)`",
    ]
    for pattern in patterns:
        match = re.search(pattern, message)
        if match:
            return match.group(1)
    return None


def _extract_package(message: str) -> str | None:
    """Extract source package from deprecation message.

    Common patterns:
    - "from package:flutter/..."
    - "package:http/..."
    """
    match = re.search(r"package:([^/]+)/", message)
    if match:
        return match.group(1)
    return None


async def _get_fixable_rules(path: Path, dart_path: str) -> set[str]:
    """Get set of rules that can be auto-fixed.

    Runs `dart fix --dry-run` to see what can be fixed.
    """
    fixable_rules: set[str] = set()
    try:
        proc = await asyncio.create_subprocess_exec(
            dart_path,
            "fix",
            "--dry-run",
            str(path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(path),
        )
        stdout, _ = await proc.communicate()
        output = stdout.decode()

        # Parse output for rule names
        # Example: "deprecated_member_use • 5 fixes"
        for line in output.split("\n"):
            match = re.match(r"\s*(\w+)\s+[•·]\s+\d+\s+fix", line)
            if match:
                fixable_rules.add(match.group(1))

    except Exception:
        pass

    # Known fixable deprecation rules
    fixable_rules.add("deprecated_member_use")

    return fixable_rules


async def apply_fixes(
    path: Path,
    dry_run: bool = False,
    progress_callback: Callable[[str], None] | None = None,
) -> tuple[bool, str]:
    """Apply auto-fixes for deprecations using dart fix.

    Args:
        path: Project path
        dry_run: If True, preview without applying
        progress_callback: Optional progress callback

    Returns:
        Tuple of (success, output_message)
    """
    dart_path = shutil.which("dart")
    if not dart_path:
        flutter_path = shutil.which("flutter")
        if flutter_path:
            dart_path = "flutter"
        else:
            return False, "Dart SDK not found. Please install Dart or Flutter."

    if progress_callback:
        if dry_run:
            progress_callback("Previewing fixes...")
        else:
            progress_callback("Applying fixes...")

    args = [dart_path, "fix"]
    if dry_run:
        args.append("--dry-run")
    else:
        args.append("--apply")
    args.append(str(path))

    try:
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(path),
        )
        stdout, stderr = await proc.communicate()
        output = stdout.decode() + stderr.decode()

        if proc.returncode == 0:
            return True, output
        else:
            return False, f"dart fix failed:\n{output}"

    except Exception as e:
        return False, f"Error running dart fix: {e}"
