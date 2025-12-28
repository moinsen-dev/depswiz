"""CLI context utilities for depswiz."""

import os


def is_ci_environment() -> bool:
    """Detect if running in a CI environment.

    Checks for common CI environment variables to determine if we're
    running in an automated pipeline.

    Returns:
        True if CI environment detected, False otherwise.
    """
    ci_vars = [
        "CI",  # Generic CI indicator (GitHub Actions, GitLab CI, etc.)
        "GITHUB_ACTIONS",  # GitHub Actions
        "GITLAB_CI",  # GitLab CI
        "CIRCLECI",  # CircleCI
        "TRAVIS",  # Travis CI
        "JENKINS_URL",  # Jenkins
        "BUILDKITE",  # Buildkite
        "DRONE",  # Drone CI
        "TEAMCITY_VERSION",  # TeamCity
        "AZURE_PIPELINES",  # Azure Pipelines
        "TF_BUILD",  # Azure DevOps
        "BITBUCKET_BUILD_NUMBER",  # Bitbucket Pipelines
        "CODEBUILD_BUILD_ID",  # AWS CodeBuild
    ]
    return any(os.environ.get(var) for var in ci_vars)


def parse_language_filter(only: str | None) -> list[str] | None:
    """Parse comma-separated language filter.

    Args:
        only: Comma-separated list of languages (e.g., "python,docker")

    Returns:
        List of language strings, or None if no filter.
    """
    if not only:
        return None
    return [lang.strip().lower() for lang in only.split(",") if lang.strip()]


def determine_format(
    json_flag: bool,
    md_flag: bool,
    html_flag: bool,
    sarif_flag: bool = False,
    default: str = "cli",
) -> str:
    """Determine output format from shorthand flags.

    Args:
        json_flag: --json was specified
        md_flag: --md was specified
        html_flag: --html was specified
        sarif_flag: --sarif was specified
        default: Default format if no flags

    Returns:
        Format string: "cli", "json", "markdown", "html", or "sarif"
    """
    if json_flag:
        return "json"
    if md_flag:
        return "markdown"
    if html_flag:
        return "html"
    if sarif_flag:
        return "sarif"
    return default
