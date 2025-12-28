"""CLI output formatter using Rich."""

from rich.console import Console
from rich.table import Table

from depswiz import __version__
from depswiz.cli.formatters.base import OutputFormatter
from depswiz.core.models import AuditResult, CheckResult, LicenseResult, Severity, UpdateType


class CliFormatter(OutputFormatter):
    """Rich CLI output formatter."""

    def __init__(self, console: Console | None = None):
        self.console = console or Console()

    def format_check_result(self, result: CheckResult, warn_breaking: bool = True) -> str:
        """Format and display a check result."""
        # Header
        self.console.print(f"\n[bold blue]depswiz[/bold blue] v{__version__} - Dependency Check\n")

        if result.path:
            self.console.print(f"[dim]Scanning: {result.path}[/dim]")

        # Group packages by language
        packages_by_lang: dict[str, list] = {}
        for pkg in result.packages:
            lang = pkg.language or "unknown"
            if lang not in packages_by_lang:
                packages_by_lang[lang] = []
            packages_by_lang[lang].append(pkg)

        # Display each language section
        for lang, packages in packages_by_lang.items():
            self.console.print(f"\n[bold]{lang.title()} Dependencies[/bold]")
            self.console.print("=" * 40)

            table = Table(show_header=True, header_style="bold")
            table.add_column("Package", style="cyan")
            table.add_column("Constraint")
            table.add_column("Current", style="yellow")
            table.add_column("Latest", style="green")
            table.add_column("Status")

            for pkg in packages:
                status = self._get_update_status(pkg.update_type, pkg.is_outdated)
                table.add_row(
                    pkg.display_name,
                    pkg.constraint or "-",
                    pkg.current_version or "?",
                    pkg.latest_version or "?",
                    status,
                )

            self.console.print(table)

        # Summary
        breakdown = result.update_breakdown
        summary_parts = []
        if breakdown[UpdateType.MAJOR]:
            summary_parts.append(f"{breakdown[UpdateType.MAJOR]} major")
        if breakdown[UpdateType.MINOR]:
            summary_parts.append(f"{breakdown[UpdateType.MINOR]} minor")
        if breakdown[UpdateType.PATCH]:
            summary_parts.append(f"{breakdown[UpdateType.PATCH]} patch")

        summary_text = ", ".join(summary_parts) if summary_parts else "none"

        self.console.print(
            f"\n[bold]Summary:[/bold] {result.total_packages} packages checked, "
            f"{len(result.outdated_packages)} updates available ({summary_text})"
        )

        if result.outdated_packages:
            self.console.print("\n[dim]Run `depswiz update` to update dependencies.[/dim]")

        return ""  # CLI formatter prints directly

    def _get_update_status(self, update_type: UpdateType | None, is_outdated: bool) -> str:
        """Get a formatted update status string."""
        if not is_outdated:
            return "[green]ok[/green]"

        type_colors = {
            UpdateType.PATCH: "blue",
            UpdateType.MINOR: "yellow",
            UpdateType.MAJOR: "red",
        }

        if update_type:
            color = type_colors.get(update_type, "white")
            return f"[{color}]{update_type.value}[/{color}]"

        return "[yellow]update[/yellow]"

    def format_audit_result(self, result: AuditResult, show_fix: bool = False) -> str:
        """Format and display an audit result."""
        self.console.print(f"\n[bold blue]depswiz[/bold blue] v{__version__} - Security Audit\n")

        if result.path:
            self.console.print(f"[dim]Scanning: {result.path}[/dim]")

        if not result.vulnerabilities:
            self.console.print("\n[green]No vulnerabilities found![/green]")
            return ""

        # Vulnerability count by severity
        self.console.print(
            f"\n[bold red]{result.total_vulnerabilities} vulnerabilities found[/bold red]"
        )

        counts = []
        if result.critical_count:
            counts.append(f"[red]{result.critical_count} critical[/red]")
        if result.high_count:
            counts.append(f"[orange1]{result.high_count} high[/orange1]")
        if result.medium_count:
            counts.append(f"[yellow]{result.medium_count} medium[/yellow]")
        if result.low_count:
            counts.append(f"[blue]{result.low_count} low[/blue]")

        if counts:
            self.console.print(" | ".join(counts))

        # Vulnerability table
        table = Table(show_header=True, header_style="bold")
        table.add_column("Package", style="cyan")
        table.add_column("Installed")
        table.add_column("Severity")
        table.add_column("Vulnerability")

        for pkg, vuln in result.vulnerabilities:
            severity_style = self._get_severity_style(vuln.severity)
            table.add_row(
                pkg.name,
                pkg.current_version or "?",
                f"[{severity_style}]{vuln.severity.value.upper()}[/{severity_style}]",
                f"{vuln.id}\n[dim]{vuln.title[:50]}...[/dim]"
                if len(vuln.title) > 50
                else f"{vuln.id}\n[dim]{vuln.title}[/dim]",
            )

        self.console.print(table)

        # Show fixes if requested
        if show_fix:
            self.console.print("\n[bold]Recommendations:[/bold]")
            for pkg, vuln in result.vulnerabilities:
                if vuln.fixed_version:
                    self.console.print(f"  {pkg.name}: upgrade to >= {vuln.fixed_version}")

        return ""

    def _get_severity_style(self, severity: Severity) -> str:
        """Get the Rich style for a severity level."""
        styles = {
            Severity.CRITICAL: "red bold",
            Severity.HIGH: "orange1",
            Severity.MEDIUM: "yellow",
            Severity.LOW: "blue",
            Severity.UNKNOWN: "dim",
        }
        return styles.get(severity, "white")

    def format_license_result(self, result: LicenseResult, summary_only: bool = False) -> str:
        """Format and display a license result."""
        self.console.print(f"\n[bold blue]depswiz[/bold blue] v{__version__} - License Check\n")

        if result.path:
            self.console.print(f"[dim]Scanning: {result.path}[/dim]")

        if summary_only:
            # Just show summary
            summary = result.license_summary
            table = Table(title="License Summary")
            table.add_column("License", style="cyan")
            table.add_column("Count", style="green")

            for lic_id, count in sorted(summary.items(), key=lambda x: -x[1]):
                table.add_row(lic_id, str(count))

            self.console.print(table)
        else:
            # Full details
            table = Table(show_header=True, header_style="bold")
            table.add_column("Package", style="cyan")
            table.add_column("Version")
            table.add_column("License", style="green")
            table.add_column("Category")

            for pkg in result.packages:
                license_id = (pkg.license_info.spdx_id if pkg.license_info else None) or "UNKNOWN"
                category = pkg.license_info.category.value if pkg.license_info else "unknown"
                table.add_row(
                    pkg.name,
                    pkg.current_version or "?",
                    license_id,
                    category,
                )

            self.console.print(table)

        # Show violations
        if result.violations:
            self.console.print(
                f"\n[bold red]{len(result.violations)} license violations:[/bold red]"
            )
            for pkg, reason in result.violations:
                self.console.print(f"  [red]- {pkg.name}: {reason}[/red]")

        # Show warnings
        if result.warnings:
            self.console.print(f"\n[bold yellow]{len(result.warnings)} warnings:[/bold yellow]")
            for pkg, reason in result.warnings:
                self.console.print(f"  [yellow]- {pkg.name}: {reason}[/yellow]")

        if not result.violations and not result.warnings:
            self.console.print("\n[green]All licenses are compliant![/green]")

        return ""

    def format_comprehensive_scan(
        self,
        check_result: CheckResult,
        audit_result: AuditResult,
        license_result: LicenseResult,
    ) -> str:
        """Format a comprehensive scan combining all checks."""
        from rich.panel import Panel

        # Header
        self.console.print(
            Panel.fit(
                f"[bold blue]depswiz[/bold blue] v{__version__} - Comprehensive Scan",
                border_style="blue",
            )
        )

        if check_result.path:
            self.console.print(f"[dim]Scanning: {check_result.path}[/dim]\n")

        # Quick summary counts
        outdated_count = len(check_result.outdated_packages)
        vuln_count = audit_result.total_vulnerabilities
        violation_count = len(license_result.violations)

        # Status indicator
        if outdated_count == 0 and vuln_count == 0 and violation_count == 0:
            self.console.print("[bold green]✓ All checks passed![/bold green]\n")
        else:
            issues = []
            if outdated_count > 0:
                issues.append(f"[yellow]{outdated_count} outdated[/yellow]")
            if vuln_count > 0:
                issues.append(f"[red]{vuln_count} vulnerabilities[/red]")
            if violation_count > 0:
                issues.append(f"[red]{violation_count} license violations[/red]")
            self.console.print(f"[bold]Issues found:[/bold] {', '.join(issues)}\n")

        # Section 1: Outdated packages (condensed)
        self.console.print("[bold]📦 Dependencies[/bold]")
        self.console.print("-" * 40)

        if check_result.outdated_packages:
            table = Table(show_header=True, header_style="bold", box=None)
            table.add_column("Package", style="cyan")
            table.add_column("Current", style="yellow")
            table.add_column("Latest", style="green")
            table.add_column("Type")

            for pkg in check_result.outdated_packages[:10]:  # Top 10
                update_type = pkg.update_type.value if pkg.update_type else "update"
                color = {"patch": "blue", "minor": "yellow", "major": "red"}.get(
                    update_type, "white"
                )
                table.add_row(
                    pkg.display_name,
                    pkg.current_version or "?",
                    pkg.latest_version or "?",
                    f"[{color}]{update_type}[/{color}]",
                )

            self.console.print(table)
            if len(check_result.outdated_packages) > 10:
                self.console.print(
                    f"[dim]...and {len(check_result.outdated_packages) - 10} more[/dim]"
                )
        else:
            self.console.print("[green]All packages up to date[/green]")

        # Section 2: Vulnerabilities (condensed)
        self.console.print("\n[bold]🔒 Security[/bold]")
        self.console.print("-" * 40)

        if audit_result.vulnerabilities:
            counts = []
            if audit_result.critical_count:
                counts.append(f"[red]{audit_result.critical_count} critical[/red]")
            if audit_result.high_count:
                counts.append(f"[orange1]{audit_result.high_count} high[/orange1]")
            if audit_result.medium_count:
                counts.append(f"[yellow]{audit_result.medium_count} medium[/yellow]")
            if audit_result.low_count:
                counts.append(f"[blue]{audit_result.low_count} low[/blue]")

            self.console.print(" | ".join(counts))

            # Show top 5 vulnerabilities
            table = Table(show_header=True, header_style="bold", box=None)
            table.add_column("Package", style="cyan")
            table.add_column("Severity")
            table.add_column("ID")

            for pkg, vuln in audit_result.vulnerabilities[:5]:
                severity_style = self._get_severity_style(vuln.severity)
                table.add_row(
                    pkg.name,
                    f"[{severity_style}]{vuln.severity.value.upper()}[/{severity_style}]",
                    vuln.id,
                )

            self.console.print(table)
            if len(audit_result.vulnerabilities) > 5:
                self.console.print(
                    f"[dim]...and {len(audit_result.vulnerabilities) - 5} more[/dim]"
                )
        else:
            self.console.print("[green]No vulnerabilities found[/green]")

        # Section 3: Licenses (condensed)
        self.console.print("\n[bold]📜 Licenses[/bold]")
        self.console.print("-" * 40)

        if license_result.violations:
            for pkg, reason in license_result.violations[:5]:
                self.console.print(f"  [red]✗ {pkg.name}: {reason}[/red]")
            if len(license_result.violations) > 5:
                self.console.print(
                    f"[dim]...and {len(license_result.violations) - 5} more[/dim]"
                )
        elif license_result.warnings:
            for pkg, reason in license_result.warnings[:3]:
                self.console.print(f"  [yellow]⚠ {pkg.name}: {reason}[/yellow]")
            if len(license_result.warnings) > 3:
                self.console.print(
                    f"[dim]...and {len(license_result.warnings) - 3} more[/dim]"
                )
        else:
            self.console.print("[green]All licenses compliant[/green]")

        # Footer with next steps
        self.console.print("\n" + "=" * 40)
        breakdown = check_result.update_breakdown
        self.console.print(
            f"[bold]Summary:[/bold] {check_result.total_packages} packages, "
            f"{outdated_count} outdated ({breakdown[UpdateType.MAJOR]} major, "
            f"{breakdown[UpdateType.MINOR]} minor, {breakdown[UpdateType.PATCH]} patch), "
            f"{vuln_count} vulnerabilities, {violation_count} license issues"
        )

        if outdated_count > 0 or vuln_count > 0:
            self.console.print(
                "\n[dim]Run `depswiz check` for details or `depswiz update` to update[/dim]"
            )

        return ""
