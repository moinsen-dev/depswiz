"""SBOM command for depswiz."""

import asyncio
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from depswiz.cli.context import parse_language_filter
from depswiz.core.config import load_config
from depswiz.core.scanner import scan_dependencies
from depswiz.sbom import CycloneDxGenerator, SpdxGenerator

app = typer.Typer(invoke_without_command=True)
console = Console()


@app.callback(invoke_without_command=True)
def sbom(
    ctx: typer.Context,
    path: Path = typer.Argument(
        Path(),
        help="Project path to scan",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    # Simplified language filter
    only: str | None = typer.Option(
        None,
        "--only",
        help="Only scan specific languages (comma-separated, e.g., python,docker)",
    ),
    # Recursive is now TRUE by default, --shallow to opt-out
    shallow: bool = typer.Option(
        False,
        "--shallow",
        help="Only scan current directory (don't recurse)",
    ),
    # SBOM format
    sbom_format: str = typer.Option(
        "cyclonedx",
        "--format",
        "-f",
        help="SBOM format: cyclonedx, spdx",
    ),
    spec_version: str | None = typer.Option(
        None,
        "--spec-version",
        help="Spec version (cyclonedx: 1.6, spdx: 3.0)",
    ),
    # Dev dependencies: --dev to include
    dev: bool = typer.Option(
        False,
        "--dev",
        help="Include development dependencies",
    ),
    # Transitive dependencies
    transitive: bool = typer.Option(
        True,
        "--transitive/--no-transitive",
        help="Include transitive dependencies from lockfiles",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file (defaults to stdout)",
    ),
    # Component metadata
    name: str | None = typer.Option(
        None,
        "--name",
        help="Component name for SBOM (defaults to directory name)",
    ),
    version: str | None = typer.Option(
        None,
        "--version",
        help="Component version for SBOM",
    ),
) -> None:
    """Generate Software Bill of Materials.

    By default, scans the entire project recursively and generates
    a CycloneDX 1.6 SBOM.

    Examples:
        depswiz sbom                      # Generate SBOM to stdout
        depswiz sbom -o sbom.json         # Save to file
        depswiz sbom --format spdx        # SPDX format
        depswiz sbom --dev                # Include dev deps
        depswiz sbom --only python
    """
    # Load configuration
    config_path = ctx.obj.get("config_path") if ctx.obj else None
    config = load_config(config_path, path)

    # Recursive is TRUE by default now
    recursive = not shallow

    # Parse language filter
    languages = parse_language_filter(only)

    # Override config with CLI options
    if dev:
        config.sbom.include_dev = True
    if not transitive:
        config.sbom.include_transitive = False

    quiet = ctx.obj.get("quiet", False) if ctx.obj else False

    # Determine spec version
    if spec_version is None:
        spec_version = "1.6" if sbom_format == "cyclonedx" else "3.0"

    # Run the scan
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        disable=quiet,
    ) as progress:
        task = progress.add_task("Scanning dependencies...", total=None)

        check_result = asyncio.run(
            scan_dependencies(
                path=path,
                languages=languages,
                recursive=recursive,
                workspace=True,  # Always detect workspaces
                include_dev=config.sbom.include_dev,
                config=config,
                progress_callback=lambda msg: progress.update(task, description=msg),
            )
        )

        progress.update(task, description="Generating SBOM...")

        # Generate SBOM
        generator: CycloneDxGenerator | SpdxGenerator
        if sbom_format == "cyclonedx":
            generator = CycloneDxGenerator(spec_version=spec_version)
        else:
            generator = SpdxGenerator(spec_version=spec_version)

        sbom_content = generator.generate(
            packages=check_result.packages,
            component_name=name or path.name,
            component_version=version or "0.0.0",
        )

        progress.update(task, description="Done!")

    # Output
    if output:
        output.write_text(sbom_content)
        if not quiet:
            console.print(f"[green]SBOM written to {output}[/green]")
    else:
        console.print(sbom_content)
