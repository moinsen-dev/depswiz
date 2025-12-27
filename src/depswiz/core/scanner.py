"""Core scanning logic for depswiz."""

import asyncio
from collections.abc import Callable
from pathlib import Path

import httpx

from depswiz.core.cache import DepsWizCache
from depswiz.core.config import Config
from depswiz.core.models import AuditResult, CheckResult, LicenseResult, Package
from depswiz.plugins import get_plugin, get_plugins_for_path
from depswiz.plugins.base import LanguagePlugin
from depswiz.security.licenses import LicenseChecker
from depswiz.security.vulnerabilities import VulnerabilityAggregator


async def scan_dependencies(
    path: Path,
    languages: list[str] | None = None,
    recursive: bool = False,
    workspace: bool = False,
    include_dev: bool = True,
    config: Config | None = None,
    progress_callback: Callable[[str], None] | None = None,
) -> CheckResult:
    """Scan dependencies in a project.

    Args:
        path: Path to the project root
        languages: List of languages to scan (None for all detected)
        recursive: Whether to scan subdirectories
        workspace: Whether to detect and scan workspaces
        include_dev: Whether to include dev dependencies
        config: Configuration object
        progress_callback: Callback for progress updates

    Returns:
        CheckResult with all found packages
    """
    if config is None:
        config = Config()

    cache = DepsWizCache(config.cache)
    all_packages: list[Package] = []

    def update_progress(msg: str) -> None:
        if progress_callback:
            progress_callback(msg)

    # Get applicable plugins
    plugins: list[LanguagePlugin] = []
    if languages:
        for lang in languages:
            plugin = get_plugin(lang)
            if plugin is not None:
                plugins.append(plugin)
    else:
        plugins = get_plugins_for_path(path)

    if not plugins:
        update_progress("No supported project files found")
        return CheckResult(packages=[], path=path)

    update_progress(
        f"Found {len(plugins)} language(s): {', '.join(p.display_name for p in plugins)}"
    )

    # Scan each plugin
    async with httpx.AsyncClient(timeout=config.network.timeout_seconds) as client:
        for plugin in plugins:
            update_progress(f"Scanning {plugin.display_name} dependencies...")

            # Find and parse manifest files
            manifest_files = plugin.find_manifest_files(path, recursive=recursive)

            for manifest in manifest_files:
                packages = plugin.parse_manifest(manifest)

                # Filter dev dependencies if needed
                if not include_dev:
                    packages = [p for p in packages if not p.is_dev]

                # Set language and source file
                for pkg in packages:
                    pkg.language = plugin.name
                    pkg.source_file = manifest

                # Fetch latest versions concurrently
                semaphore = asyncio.Semaphore(config.network.max_concurrent_requests)
                current_plugin = plugin  # Capture for closure

                async def fetch_latest(
                    pkg: Package,
                    _plugin: LanguagePlugin = current_plugin,
                    _semaphore: asyncio.Semaphore = semaphore,
                ) -> Package:
                    async with _semaphore:
                        # Check cache first
                        cached = cache.get_package_info(_plugin.name, pkg.name)
                        if cached and "latest_version" in cached:
                            return pkg.with_latest_version(cached["latest_version"])

                        latest = await _plugin.fetch_latest_version(client, pkg)
                        if latest:
                            cache.set_package_info(
                                _plugin.name, pkg.name, {"latest_version": latest}
                            )
                            return pkg.with_latest_version(latest)
                        return pkg

                tasks = [fetch_latest(pkg) for pkg in packages]
                updated_packages = await asyncio.gather(*tasks)
                all_packages.extend(updated_packages)

    update_progress(f"Checked {len(all_packages)} packages")
    cache.close()

    return CheckResult(packages=all_packages, path=path)


async def audit_packages(
    packages: list[Package],
    config: Config | None = None,
    progress_callback: Callable[[str], None] | None = None,
) -> AuditResult:
    """Audit packages for vulnerabilities.

    Args:
        packages: List of packages to audit
        config: Configuration object
        progress_callback: Callback for progress updates

    Returns:
        AuditResult with found vulnerabilities
    """
    if config is None:
        config = Config()

    def update_progress(msg: str) -> None:
        if progress_callback:
            progress_callback(msg)

    update_progress("Querying vulnerability databases...")

    aggregator = VulnerabilityAggregator(config)
    vulnerabilities = await aggregator.check_packages(packages)

    update_progress(f"Found {len(vulnerabilities)} vulnerabilities")

    return AuditResult(
        packages=packages,
        vulnerabilities=vulnerabilities,
    )


async def check_licenses(
    packages: list[Package],
    config: Config | None = None,
    progress_callback: Callable[[str], None] | None = None,
) -> LicenseResult:
    """Check license compliance for packages.

    Args:
        packages: List of packages to check
        config: Configuration object
        progress_callback: Callback for progress updates

    Returns:
        LicenseResult with compliance information
    """
    if config is None:
        config = Config()

    def update_progress(msg: str) -> None:
        if progress_callback:
            progress_callback(msg)

    update_progress("Fetching license information...")

    # Fetch license info for packages that don't have it
    async with httpx.AsyncClient(timeout=config.network.timeout_seconds) as client:
        for pkg in packages:
            if pkg.license_info is None and pkg.language:
                plugin = get_plugin(pkg.language)
                if plugin:
                    license_info = await plugin.fetch_license(client, pkg)
                    pkg.license_info = license_info

    update_progress("Checking license compliance...")

    checker = LicenseChecker(config.licenses)
    violations, warnings = checker.check_packages(packages)

    return LicenseResult(
        packages=packages,
        violations=violations,
        warnings=warnings,
    )
