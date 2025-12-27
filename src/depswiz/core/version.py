"""Version parsing and comparison utilities."""

from packaging.version import InvalidVersion, Version

from depswiz.core.models import UpdateType


def parse_version(version_str: str) -> Version | None:
    """Parse a version string into a Version object."""
    try:
        return Version(version_str)
    except InvalidVersion:
        return None


def determine_update_type(current: str, latest: str) -> UpdateType | None:
    """Determine the type of update between two versions."""
    current_ver = parse_version(current)
    latest_ver = parse_version(latest)

    if current_ver is None or latest_ver is None:
        return None

    if current_ver >= latest_ver:
        return None

    if latest_ver.major > current_ver.major:
        return UpdateType.MAJOR
    if latest_ver.minor > current_ver.minor:
        return UpdateType.MINOR
    if latest_ver.micro > current_ver.micro:
        return UpdateType.PATCH

    # Handle pre-release/post-release differences
    return UpdateType.PATCH


def is_compatible_update(current: str, latest: str, constraint: str | None = None) -> bool:
    """Check if an update is compatible with the version constraint."""
    current_ver = parse_version(current)
    latest_ver = parse_version(latest)

    if current_ver is None or latest_ver is None:
        return False

    # If no constraint, assume compatible
    if constraint is None:
        return True

    # Parse common constraint patterns
    constraint = constraint.strip()

    # Handle ^ (caret) constraints: ^1.2.3 means >=1.2.3 <2.0.0
    if constraint.startswith("^"):
        base = parse_version(constraint[1:])
        if base is None:
            return True
        # Must be >= base version
        if latest_ver < base:
            return False
        # For 0.x versions: ^0.1.2 means >=0.1.2 <0.2.0 (minor must match)
        if base.major == 0:
            return latest_ver.major == 0 and latest_ver.minor == base.minor
        # For 1.x+ versions: ^1.2.3 means >=1.2.3 <2.0.0 (major must match)
        return latest_ver.major == base.major

    # Handle ~ (tilde) constraints: ~1.2.3 means >=1.2.3 <1.3.0
    if constraint.startswith("~"):
        base = parse_version(constraint[1:].lstrip("="))
        if base is None:
            return True
        # Must be >= base version
        if latest_ver < base:
            return False
        return latest_ver.major == base.major and latest_ver.minor == base.minor

    # Handle >= constraints
    if constraint.startswith(">="):
        base = parse_version(constraint[2:].split(",")[0].strip())
        if base is None:
            return True
        return latest_ver >= base

    return True


def normalize_version(version_str: str) -> str:
    """Normalize a version string to a standard format."""
    ver = parse_version(version_str)
    if ver is None:
        return version_str
    return str(ver)


def extract_version_from_constraint(constraint: str) -> str | None:
    """Extract the base version from a constraint string."""
    constraint = constraint.strip()

    # Remove common prefixes
    for prefix in [">=", "<=", "==", "!=", "~=", "^", "~", ">", "<"]:
        if constraint.startswith(prefix):
            constraint = constraint[len(prefix) :]
            break

    # Take first part if there's a comma
    constraint = constraint.split(",")[0].strip()

    # Validate it's a valid version
    if parse_version(constraint):
        return constraint

    return None
