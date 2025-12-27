"""Configuration system for depswiz."""

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from depswiz.core.models import Severity


@dataclass
class LanguageConfig:
    """Configuration for a specific language."""

    manifest: str | None = None
    lockfile: str | None = None
    include_dev: bool = True
    dependency_groups: list[str] = field(default_factory=list)


@dataclass
class CheckConfig:
    """Configuration for the check command."""

    recursive: bool = False
    workspace: bool = True
    strategy: str = "all"
    warn_breaking: bool = True
    fail_outdated: bool = False


@dataclass
class AuditConfig:
    """Configuration for the audit command."""

    severity_threshold: Severity = Severity.LOW
    fail_on: Severity = Severity.HIGH
    sources: list[str] = field(default_factory=lambda: ["osv", "ghsa", "rustsec"])
    ignore_vulnerabilities: list[str] = field(default_factory=list)


@dataclass
class LicensesConfig:
    """Configuration for license compliance."""

    policy_mode: str = "allow"  # "allow" or "deny"
    allowed: list[str] = field(
        default_factory=lambda: [
            "MIT",
            "Apache-2.0",
            "BSD-2-Clause",
            "BSD-3-Clause",
            "ISC",
            "MPL-2.0",
        ]
    )
    denied: list[str] = field(default_factory=lambda: ["GPL-3.0-only", "AGPL-3.0-only"])
    warn_copyleft: bool = True
    fail_on_unknown: bool = False


@dataclass
class SbomConfig:
    """Configuration for SBOM generation."""

    format: str = "cyclonedx"
    spec_version: str = "1.6"
    include_dev: bool = False
    include_transitive: bool = True


@dataclass
class UpdateConfig:
    """Configuration for the update command."""

    strategy: str = "minor"
    require_confirmation: bool = True
    update_lockfile: bool = True


@dataclass
class MonorepoConfig:
    """Configuration for monorepo support."""

    auto_detect: bool = True
    aggregate_report: bool = True


@dataclass
class CacheConfig:
    """Configuration for caching."""

    enabled: bool = True
    ttl_seconds: int = 3600
    directory: str = "~/.cache/depswiz"


@dataclass
class NetworkConfig:
    """Configuration for network settings."""

    timeout_seconds: int = 30
    max_concurrent_requests: int = 10
    retry_count: int = 3


@dataclass
class Config:
    """Main configuration class for depswiz."""

    version: str = "1.0"
    default_format: str = "cli"
    verbose: bool = False
    color: bool = True

    languages_enabled: list[str] = field(
        default_factory=lambda: ["python", "rust", "dart", "javascript"]
    )

    python: LanguageConfig = field(default_factory=LanguageConfig)
    rust: LanguageConfig = field(default_factory=LanguageConfig)
    dart: LanguageConfig = field(default_factory=LanguageConfig)
    javascript: LanguageConfig = field(default_factory=LanguageConfig)

    check: CheckConfig = field(default_factory=CheckConfig)
    audit: AuditConfig = field(default_factory=AuditConfig)
    licenses: LicensesConfig = field(default_factory=LicensesConfig)
    sbom: SbomConfig = field(default_factory=SbomConfig)
    update: UpdateConfig = field(default_factory=UpdateConfig)
    monorepo: MonorepoConfig = field(default_factory=MonorepoConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    network: NetworkConfig = field(default_factory=NetworkConfig)


def _parse_severity(value: str) -> Severity:
    """Parse a severity string into a Severity enum."""
    return Severity[value.upper()]


def _load_language_config(data: dict) -> LanguageConfig:
    """Load language configuration from a dict."""
    return LanguageConfig(
        manifest=data.get("manifest"),
        lockfile=data.get("lockfile"),
        include_dev=data.get("include_dev", True),
        dependency_groups=data.get("dependency_groups", []),
    )


def _load_check_config(data: dict) -> CheckConfig:
    """Load check configuration from a dict."""
    return CheckConfig(
        recursive=data.get("recursive", False),
        workspace=data.get("workspace", True),
        strategy=data.get("strategy", "all"),
        warn_breaking=data.get("warn_breaking", True),
        fail_outdated=data.get("fail_outdated", False),
    )


def _load_audit_config(data: dict) -> AuditConfig:
    """Load audit configuration from a dict."""
    severity_threshold = data.get("severity_threshold", "low")
    fail_on = data.get("fail_on", "high")
    ignore_section = data.get("ignore", {})

    return AuditConfig(
        severity_threshold=_parse_severity(severity_threshold),
        fail_on=_parse_severity(fail_on),
        sources=data.get("sources", ["osv", "ghsa", "rustsec"]),
        ignore_vulnerabilities=ignore_section.get("vulnerabilities", []),
    )


def _load_licenses_config(data: dict) -> LicensesConfig:
    """Load licenses configuration from a dict."""
    return LicensesConfig(
        policy_mode=data.get("policy_mode", "allow"),
        allowed=data.get(
            "allowed", ["MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC", "MPL-2.0"]
        ),
        denied=data.get("denied", ["GPL-3.0-only", "AGPL-3.0-only"]),
        warn_copyleft=data.get("warn_copyleft", True),
        fail_on_unknown=data.get("fail_on_unknown", False),
    )


def _load_sbom_config(data: dict) -> SbomConfig:
    """Load SBOM configuration from a dict."""
    return SbomConfig(
        format=data.get("format", "cyclonedx"),
        spec_version=data.get("spec_version", "1.6"),
        include_dev=data.get("include_dev", False),
        include_transitive=data.get("include_transitive", True),
    )


def _load_update_config(data: dict) -> UpdateConfig:
    """Load update configuration from a dict."""
    return UpdateConfig(
        strategy=data.get("strategy", "minor"),
        require_confirmation=data.get("require_confirmation", True),
        update_lockfile=data.get("update_lockfile", True),
    )


def _load_monorepo_config(data: dict) -> MonorepoConfig:
    """Load monorepo configuration from a dict."""
    return MonorepoConfig(
        auto_detect=data.get("auto_detect", True),
        aggregate_report=data.get("aggregate_report", True),
    )


def _load_cache_config(data: dict) -> CacheConfig:
    """Load cache configuration from a dict."""
    return CacheConfig(
        enabled=data.get("enabled", True),
        ttl_seconds=data.get("ttl_seconds", 3600),
        directory=data.get("directory", "~/.cache/depswiz"),
    )


def _load_network_config(data: dict) -> NetworkConfig:
    """Load network configuration from a dict."""
    return NetworkConfig(
        timeout_seconds=data.get("timeout_seconds", 30),
        max_concurrent_requests=data.get("max_concurrent_requests", 10),
        retry_count=data.get("retry_count", 3),
    )


def load_config_from_toml(data: dict) -> Config:
    """Load configuration from a parsed TOML dict."""
    # Handle both [depswiz] section and [tool.depswiz] section
    config_data = data.get("depswiz", data.get("tool", {}).get("depswiz", {}))
    languages_data = data.get("languages", config_data.get("languages", {}))

    config = Config(
        version=config_data.get("version", "1.0"),
        default_format=config_data.get("default_format", "cli"),
        verbose=config_data.get("verbose", False),
        color=config_data.get("color", True),
        languages_enabled=languages_data.get("enabled", ["python", "rust", "dart", "javascript"]),
    )

    # Load language-specific configs
    if "python" in data:
        config.python = _load_language_config(data["python"])
    if "rust" in data:
        config.rust = _load_language_config(data["rust"])
    if "dart" in data:
        config.dart = _load_language_config(data["dart"])
    if "javascript" in data:
        config.javascript = _load_language_config(data["javascript"])

    # Load command configs
    if "check" in data:
        config.check = _load_check_config(data["check"])
    if "audit" in data:
        config.audit = _load_audit_config(data["audit"])
    if "licenses" in data:
        config.licenses = _load_licenses_config(data["licenses"])
    if "sbom" in data:
        config.sbom = _load_sbom_config(data["sbom"])
    if "update" in data:
        config.update = _load_update_config(data["update"])
    if "monorepo" in data:
        config.monorepo = _load_monorepo_config(data["monorepo"])
    if "cache" in data:
        config.cache = _load_cache_config(data["cache"])
    if "network" in data:
        config.network = _load_network_config(data["network"])

    return config


def find_config_file(start_path: Path | None = None) -> Path | None:
    """Find the configuration file, searching in order of precedence."""
    if start_path is None:
        start_path = Path.cwd()

    # 1. depswiz.toml in current directory
    config_file = start_path / "depswiz.toml"
    if config_file.exists():
        return config_file

    # 2. pyproject.toml with [tool.depswiz] section
    pyproject = start_path / "pyproject.toml"
    if pyproject.exists():
        try:
            with open(pyproject, "rb") as f:
                data = tomllib.load(f)
            if "tool" in data and "depswiz" in data["tool"]:
                return pyproject
        except Exception:
            pass

    # 3. User config
    user_config = Path.home() / ".config" / "depswiz" / "config.toml"
    if user_config.exists():
        return user_config

    # 4. System config
    system_config = Path("/etc/depswiz/config.toml")
    if system_config.exists():
        return system_config

    return None


def load_config(config_path: Path | None = None, start_path: Path | None = None) -> Config:
    """Load configuration from file or use defaults."""
    if config_path is None:
        config_path = find_config_file(start_path)

    if config_path is None:
        return Config()

    try:
        with open(config_path, "rb") as f:
            data = tomllib.load(f)

        # Handle pyproject.toml format
        if config_path.name == "pyproject.toml":
            data = data.get("tool", {}).get("depswiz", {})

        return load_config_from_toml(data)
    except Exception:
        return Config()
