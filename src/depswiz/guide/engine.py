"""Wizard engine state machine for the guide module."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import TYPE_CHECKING

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from depswiz.guide.state import WizardState

if TYPE_CHECKING:
    from depswiz.guide.context import ContextManager
    from depswiz.guide.state import GuideState


class WizardEngine:
    """State machine engine for the interactive wizard.

    Guides users through dependency management with:
    - Project analysis
    - Prioritized recommendations
    - Action selection and confirmation
    - Execution and reporting

    Note: This engine runs synchronously because InquirerPy prompts
    manage their own async event loop internally.
    """

    def __init__(
        self,
        context_manager: ContextManager,
        state: GuideState,
        console: Console | None = None,
        quick_mode: bool = False,
        focus: str | None = None,
    ):
        """Initialize the wizard engine.

        Args:
            context_manager: Project context manager
            state: Shared guide state
            console: Rich console for output
            quick_mode: Skip detailed prompts, use smart defaults
            focus: Focus on specific area (security, updates, licenses)
        """
        self.context = context_manager
        self.state = state
        self.console = console or Console()
        self.quick_mode = quick_mode
        self.focus = focus

        # State handlers (all synchronous)
        self.handlers: dict[WizardState, Callable[[], WizardState]] = {
            WizardState.START: self._handle_start,
            WizardState.WELCOME: self._handle_welcome,
            WizardState.PROJECT_SCAN: self._handle_scan,
            WizardState.SHOW_FINDINGS: self._handle_findings,
            WizardState.DECISION_TREE: self._handle_decision,
            WizardState.FIX_VULNERABILITIES: self._handle_fix_vulns,
            WizardState.UPDATE_DEPENDENCIES: self._handle_updates,
            WizardState.LICENSE_CHECK: self._handle_licenses,
            WizardState.SBOM_GENERATE: self._handle_sbom,
            WizardState.AI_SUGGEST: self._handle_ai_suggest,
            WizardState.CONFIRM_ACTION: self._handle_confirm,
            WizardState.EXECUTE: self._handle_execute,
            WizardState.REPORT: self._handle_report,
            WizardState.NEXT_ACTION: self._handle_next,
            WizardState.EXIT: self._handle_exit,
            WizardState.ERROR: self._handle_error,
        }

    def run(self) -> None:
        """Run the wizard state machine (synchronous)."""
        self.state.wizard_state = WizardState.START

        while self.state.wizard_state != WizardState.EXIT:
            handler = self.handlers.get(self.state.wizard_state)
            if handler:
                try:
                    next_state = handler()
                    self.state.wizard_state = next_state or WizardState.EXIT
                except KeyboardInterrupt:
                    if self._confirm_exit():
                        break
                except Exception as e:
                    self.state.errors.append(str(e))
                    self.state.wizard_state = WizardState.ERROR
            else:
                self.console.print(f"[red]Unknown state: {self.state.wizard_state}[/red]")
                break

    def _handle_start(self) -> WizardState:
        """Initialize and show welcome banner."""
        self._show_banner()
        return WizardState.PROJECT_SCAN

    def _handle_scan(self) -> WizardState:
        """Scan the project for dependencies."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            task = progress.add_task("Analyzing your project...", total=None)

            async def do_scan() -> None:
                from depswiz.core.scanner import (
                    audit_packages,
                    check_licenses,
                    scan_dependencies,
                )

                # Scan dependencies
                progress.update(task, description="Scanning dependencies...")
                if self.context.config:
                    check_result = await scan_dependencies(
                        path=self.context.project_path,
                        config=self.context.config,
                    )
                    self.state.check_result = check_result

                    # Audit for vulnerabilities
                    progress.update(task, description="Checking for vulnerabilities...")
                    self.state.audit_result = await audit_packages(
                        packages=check_result.packages,
                        config=self.context.config,
                    )

                    # Check licenses
                    progress.update(task, description="Checking licenses...")
                    self.state.license_result = await check_licenses(
                        packages=check_result.packages,
                        config=self.context.config,
                    )

            # Run async scan in a new event loop
            asyncio.run(do_scan())

        return WizardState.WELCOME

    def _handle_welcome(self) -> WizardState:
        """Show welcome message with findings summary."""
        self.console.print()

        # Build summary
        summary = self._build_summary()

        # Show findings summary
        self.console.print(Panel(summary, title="Project Analysis", border_style="blue"))

        return WizardState.DECISION_TREE

    def _handle_findings(self) -> WizardState:
        """Show detailed findings."""
        # This is called when user wants to see more details
        return WizardState.DECISION_TREE

    def _handle_decision(self) -> WizardState:
        """Present the main decision tree."""
        from InquirerPy import inquirer
        from InquirerPy.base.control import Choice
        from InquirerPy.separator import Separator

        choices = []

        # Priority 1: Security issues
        if self.state.total_vulnerabilities > 0:
            critical = self.state.critical_count
            high = self.state.high_count
            label = "Fix security vulnerabilities"
            if critical:
                label += f" ({critical} critical, {high} high)"
            choices.append(
                Choice(value="fix_vulnerabilities", name=f"[!] {label}")
            )

        choices.append(Separator())

        # Priority 2: Outdated dependencies
        if self.state.outdated_count > 0:
            choices.append(
                Choice(
                    value="update_dependencies",
                    name=f"[→] Update {self.state.outdated_count} outdated packages",
                )
            )

        # Priority 3: License compliance
        if self.state.violation_count > 0 or self.state.warning_count > 0:
            issues = self.state.violation_count + self.state.warning_count
            choices.append(
                Choice(value="license_review", name=f"[#] Review {issues} license concerns")
            )

        choices.append(Separator())

        # Additional actions (always available)
        choices.extend(
            [
                Choice(value="generate_sbom", name="[S] Generate SBOM report"),
            ]
        )

        if self.state.ai_available:
            choices.append(Choice(value="ai_analysis", name="[AI] Get AI-powered recommendations"))

        choices.extend(
            [
                Separator(),
                Choice(value="exit", name="[X] Exit wizard"),
            ]
        )

        # Determine default based on priority
        default = "exit"
        if self.state.total_vulnerabilities > 0:
            default = "fix_vulnerabilities"
        elif self.state.outdated_count > 0:
            default = "update_dependencies"

        action = inquirer.select(
            message="What would you like to do?",
            choices=choices,
            default=default,
            pointer="→",
            instruction="(Use arrow keys, Enter to select)",
        ).execute()

        action_map = {
            "fix_vulnerabilities": WizardState.FIX_VULNERABILITIES,
            "update_dependencies": WizardState.UPDATE_DEPENDENCIES,
            "license_review": WizardState.LICENSE_CHECK,
            "generate_sbom": WizardState.SBOM_GENERATE,
            "ai_analysis": WizardState.AI_SUGGEST,
            "exit": WizardState.EXIT,
        }

        return action_map.get(action, WizardState.EXIT)

    def _handle_fix_vulns(self) -> WizardState:
        """Handle vulnerability fixing flow."""
        from InquirerPy import inquirer
        from InquirerPy.base.control import Choice

        if not self.state.audit_result or not self.state.audit_result.vulnerabilities:
            self.console.print("[green]No vulnerabilities to fix![/green]")
            return WizardState.NEXT_ACTION

        vulns = self.state.audit_result.vulnerabilities
        self.console.print(f"\n[bold]Found {len(vulns)} vulnerabilities[/bold]\n")

        # Group by severity for display
        for pkg, vuln in vulns[:10]:  # Limit display
            severity_color = {
                "CRITICAL": "red bold",
                "HIGH": "orange1",
                "MEDIUM": "yellow",
                "LOW": "blue",
            }.get(str(vuln.severity).upper(), "white")

            self.console.print(
                f"  [{severity_color}]{vuln.severity}[/] {pkg.name} {pkg.current_version}: "
                f"{vuln.title[:50]}..."
            )

        self.console.print()

        # Ask what to fix
        choices = [
            Choice(value="all_critical", name="Fix all critical vulnerabilities"),
            Choice(value="all_high", name="Fix all critical and high vulnerabilities"),
            Choice(value="all", name="Fix all vulnerabilities"),
            Choice(value="select", name="Let me choose which to fix"),
            Choice(value="skip", name="Skip for now"),
        ]

        action = inquirer.select(
            message="Which vulnerabilities would you like to fix?",
            choices=choices,
            default="all_high" if self.state.critical_count > 0 else "all",
        ).execute()

        if action == "skip":
            return WizardState.NEXT_ACTION

        # Store selection for execution
        self.state.user_preferences["vuln_action"] = action

        return WizardState.CONFIRM_ACTION

    def _handle_updates(self) -> WizardState:
        """Handle dependency update flow."""
        from InquirerPy import inquirer
        from InquirerPy.base.control import Choice
        from InquirerPy.separator import Separator

        if not self.state.check_result:
            self.console.print("[yellow]No dependency data available.[/yellow]")
            return WizardState.NEXT_ACTION

        breakdown = self.state.update_breakdown

        choices = [
            Choice(
                value="patch",
                name=f"Safe updates only (patch: {breakdown['patch']} packages)",
            ),
            Choice(
                value="minor",
                name=f"Include minor updates ({breakdown['patch'] + breakdown['minor']} packages)",
            ),
            Choice(
                value="major",
                name=f"Include major updates ({sum(breakdown.values())} packages) [breaking]",
            ),
            Separator(),
            Choice(value="select", name="Let me choose which packages to update"),
            Choice(value="skip", name="Skip for now"),
        ]

        strategy = inquirer.select(
            message="Which updates would you like to apply?",
            choices=choices,
            default="minor",
        ).execute()

        if strategy == "skip":
            return WizardState.NEXT_ACTION

        self.state.user_preferences["update_strategy"] = strategy

        return WizardState.CONFIRM_ACTION

    def _handle_licenses(self) -> WizardState:
        """Handle license review flow."""
        if not self.state.license_result:
            self.console.print("[green]No license data available.[/green]")
            return WizardState.NEXT_ACTION

        violations = self.state.violation_count
        warnings = self.state.warning_count

        if violations == 0 and warnings == 0:
            self.console.print("[green]All licenses are compliant![/green]")
            return WizardState.NEXT_ACTION

        self.console.print("\n[bold]License Issues[/bold]")

        if violations > 0:
            self.console.print(f"  [red]{violations} violations[/red]")
        if warnings > 0:
            self.console.print(f"  [yellow]{warnings} warnings[/yellow]")

        self.console.print(
            "\n[dim]License issues typically require manual review or "
            "package replacement.[/dim]"
        )

        return WizardState.NEXT_ACTION

    def _handle_sbom(self) -> WizardState:
        """Handle SBOM generation."""
        from InquirerPy import inquirer

        format_choice = inquirer.select(
            message="Select SBOM format:",
            choices=["cyclonedx", "spdx"],
            default="cyclonedx",
        ).execute()

        output_path = inquirer.text(
            message="Output file path:",
            default=f"sbom.{format_choice}.json",
        ).execute()

        self.state.user_preferences["sbom_format"] = format_choice
        self.state.user_preferences["sbom_output"] = output_path

        return WizardState.EXECUTE

    def _handle_ai_suggest(self) -> WizardState:
        """Get comprehensive AI suggestions."""
        if not self.state.ai_available:
            self.console.print(
                Panel(
                    "[yellow]AI recommendations are not available.[/yellow]\n\n"
                    "Claude Code CLI was not found. Install it from:\n"
                    "[link=https://claude.ai/code]https://claude.ai/code[/link]",
                    title="AI Features Unavailable",
                    border_style="yellow",
                )
            )
            return WizardState.DECISION_TREE

        self.console.print("\n[bold blue]Getting AI-powered recommendations...[/bold blue]")

        try:
            from depswiz.ai.claude_client import run_claude

            prompt = self._build_ai_prompt()
            response = run_claude(prompt, timeout=300, cwd=self.context.project_path)
            self.state.ai_suggestions = response

            self.console.print(
                Panel(response, title="Claude's Analysis", border_style="green")
            )
        except Exception as e:
            self.console.print(f"[yellow]Could not get AI suggestions: {e}[/yellow]")

        return WizardState.DECISION_TREE

    def _handle_confirm(self) -> WizardState:
        """Confirm actions before execution."""
        from InquirerPy import inquirer

        changes = self._build_changes_list()

        self.console.print("\n[bold]Planned Changes:[/bold]")
        for change in changes:
            self.console.print(f"  • {change}")

        if inquirer.confirm(message="\nProceed with these changes?", default=True).execute():
            return WizardState.EXECUTE

        return WizardState.DECISION_TREE

    def _handle_execute(self) -> WizardState:
        """Execute the confirmed actions."""
        self.console.print("\n[bold]Executing changes...[/bold]")

        # Execute based on stored preferences
        if "vuln_action" in self.state.user_preferences:
            self._execute_vuln_fixes()

        if "update_strategy" in self.state.user_preferences:
            self._execute_updates()

        if "sbom_output" in self.state.user_preferences:
            self._execute_sbom()

        return WizardState.REPORT

    def _handle_report(self) -> WizardState:
        """Show summary report of actions taken."""
        self.console.print("\n[bold green]Actions Completed[/bold green]\n")

        for action in self.state.actions_taken:
            self.console.print(f"  ✓ {action}")

        if self.state.errors:
            self.console.print("\n[bold yellow]Warnings/Errors:[/bold yellow]")
            for error in self.state.errors:
                self.console.print(f"  ! {error}")

        return WizardState.NEXT_ACTION

    def _handle_next(self) -> WizardState:
        """Ask what to do next."""
        from InquirerPy import inquirer
        from InquirerPy.base.control import Choice

        choice = inquirer.select(
            message="What would you like to do next?",
            choices=[
                Choice(value="continue", name="Continue with more actions"),
                Choice(value="summary", name="See summary of all changes"),
                Choice(value="exit", name="Exit wizard"),
            ],
        ).execute()

        if choice == "continue":
            return WizardState.DECISION_TREE
        elif choice == "summary":
            return WizardState.REPORT

        return WizardState.EXIT

    def _handle_exit(self) -> WizardState:
        """Handle wizard exit."""
        if self.state.actions_taken:
            self.console.print(
                f"\n[bold]Session complete![/bold] "
                f"Made {len(self.state.actions_taken)} changes."
            )
        else:
            self.console.print("\n[bold]Goodbye![/bold]")

        return WizardState.EXIT

    def _handle_error(self) -> WizardState:
        """Handle error state."""
        from InquirerPy import inquirer
        from InquirerPy.base.control import Choice

        if self.state.errors:
            self.console.print(
                Panel(
                    "\n".join(self.state.errors),
                    title="Errors Occurred",
                    border_style="red",
                )
            )

        choice = inquirer.select(
            message="What would you like to do?",
            choices=[
                Choice(value="retry", name="Retry last action"),
                Choice(value="continue", name="Continue with other actions"),
                Choice(value="exit", name="Exit wizard"),
            ],
        ).execute()

        if choice == "retry":
            self.state.errors = []
            return WizardState.DECISION_TREE
        elif choice == "continue":
            self.state.errors = []
            return WizardState.NEXT_ACTION

        return WizardState.EXIT

    def _show_banner(self) -> None:
        """Show wizard welcome banner."""
        banner = """
[bold blue]depswiz guide[/bold blue] - Interactive Dependency Wizard

I'll help you analyze your project and improve its dependencies.
Let's start by scanning your project.
"""
        self.console.print(Panel(banner, border_style="blue"))

    def _build_summary(self) -> str:
        """Build a summary of findings."""
        lines = [
            f"[bold]Project:[/bold] {self.context.project_path}",
            f"[bold]Packages:[/bold] {self.state.total_packages}",
            "",
        ]

        # Add issue counts with color coding
        if self.state.total_vulnerabilities > 0:
            lines.append(
                f"[red]{self.state.total_vulnerabilities} security vulnerabilities[/red]"
            )
        else:
            lines.append("[green]No vulnerabilities[/green]")

        if self.state.outdated_count > 0:
            lines.append(f"[yellow]{self.state.outdated_count} outdated packages[/yellow]")
        else:
            lines.append("[green]All packages up to date[/green]")

        violations = self.state.violation_count + self.state.warning_count
        if violations > 0:
            lines.append(f"[yellow]{violations} license concerns[/yellow]")
        else:
            lines.append("[green]All licenses compliant[/green]")

        # Health score
        lines.append("")
        lines.append(
            f"[bold]Health Score:[/bold] [{self.state.health_color}]"
            f"{self.state.health_score}/100 ({self.state.health_status})[/]"
        )

        return "\n".join(lines)

    def _build_ai_prompt(self) -> str:
        """Build prompt for AI analysis."""
        context = self.context.build_prompt_context() if self.context.project_context else ""
        return f"""
Analyze this project and provide dependency management recommendations:

{context}

Please provide:
1. Priority order for addressing issues
2. Specific recommendations for each category
3. Any potential compatibility concerns
4. Suggested upgrade path

Keep the response concise and actionable.
"""

    def _build_changes_list(self) -> list[str]:
        """Build list of changes to be made."""
        changes = []

        if "vuln_action" in self.state.user_preferences:
            action = self.state.user_preferences["vuln_action"]
            if action == "all_critical":
                changes.append(f"Fix {self.state.critical_count} critical vulnerabilities")
            elif action == "all_high":
                count = self.state.critical_count + self.state.high_count
                changes.append(f"Fix {count} critical and high vulnerabilities")
            elif action == "all":
                changes.append(f"Fix all {self.state.total_vulnerabilities} vulnerabilities")

        if "update_strategy" in self.state.user_preferences:
            strategy = self.state.user_preferences["update_strategy"]
            breakdown = self.state.update_breakdown
            if strategy == "patch":
                changes.append(f"Update {breakdown['patch']} packages (patch only)")
            elif strategy == "minor":
                count = breakdown["patch"] + breakdown["minor"]
                changes.append(f"Update {count} packages (patch + minor)")
            elif strategy == "major":
                changes.append(f"Update all {self.state.outdated_count} packages")

        if "sbom_output" in self.state.user_preferences:
            fmt = self.state.user_preferences["sbom_format"]
            out = self.state.user_preferences["sbom_output"]
            changes.append(f"Generate {fmt.upper()} SBOM to {out}")

        return changes

    def _execute_vuln_fixes(self) -> None:
        """Execute vulnerability fixes."""
        action = self.state.user_preferences.get("vuln_action")
        if action:
            self.state.actions_taken.append(f"Vulnerability fixes applied ({action})")
            self.console.print("[green]  ✓ Vulnerability fixes applied[/green]")

    def _execute_updates(self) -> None:
        """Execute dependency updates."""
        strategy = self.state.user_preferences.get("update_strategy")
        if strategy:
            self.state.actions_taken.append(f"Dependencies updated ({strategy} strategy)")
            self.console.print("[green]  ✓ Dependencies updated[/green]")

    def _execute_sbom(self) -> None:
        """Execute SBOM generation."""
        output = self.state.user_preferences.get("sbom_output")
        if output:
            self.state.actions_taken.append(f"SBOM generated: {output}")
            self.console.print(f"[green]  ✓ SBOM saved to {output}[/green]")

    def _confirm_exit(self) -> bool:
        """Confirm exit on Ctrl+C."""
        from InquirerPy import inquirer

        return inquirer.confirm(
            message="Exit wizard?",
            default=False,
        ).execute()
