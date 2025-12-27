"""SBOM command for depswiz."""

import asyncio
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

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
    language: list[str] | None = typer.Option(
        None,
        "--language",
        "-l",
        help="Filter by language (can be repeated)",
    ),
    recursive: bool = typer.Option(
        False,
        "--recursive",
        "-r",
        help="Scan subdirectories",
    ),
    workspace: bool = typer.Option(
        False,
        "--workspace",
        "-w",
        help="Detect and scan workspaces",
    ),
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
    include_dev: bool = typer.Option(
        False,
        "--include-dev",
        help="Include development dependencies",
    ),
    include_transitive: bool = typer.Option(
        True,
        "--include-transitive/--no-transitive",
        help="Include transitive dependencies from lockfiles",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file (defaults to stdout)",
    ),
    component_name: str | None = typer.Option(
        None,
        "--name",
        help="Component name for SBOM",
    ),
    component_version: str | None = typer.Option(
        None,
        "--version",
        help="Component version for SBOM",
    ),
) -> None:
    """Generate Software Bill of Materials."""
    # Load configuration
    config_path = ctx.obj.get("config_path") if ctx.obj else None
    config = load_config(config_path, path)

    # Override config with CLI options
    if include_dev:
        config.sbom.include_dev = include_dev
    if not include_transitive:
        config.sbom.include_transitive = False

    ctx.obj.get("verbose", False) if ctx.obj else False
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
                languages=language,
                recursive=recursive or config.check.recursive,
                workspace=workspace or config.check.workspace,
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
            component_name=component_name or path.name,
            component_version=component_version or "0.0.0",
        )

        progress.update(task, description="Done!")

    # Output
    if output:
        output.write_text(sbom_content)
        if not quiet:
            console.print(f"[green]SBOM written to {output}[/green]")
    else:
        console.print(sbom_content)
