"""Tool definitions for development tools version checking."""

from depswiz.tools.models import ToolDefinition

# Registry of all supported development tools
TOOL_DEFINITIONS: dict[str, ToolDefinition] = {
    "node": ToolDefinition(
        name="node",
        display_name="Node.js",
        version_command=["node", "--version"],
        version_regex=r"v?(\d+\.\d+\.\d+)",
        official_api_url="https://nodejs.org/dist/index.json",
        project_indicators=["package.json"],
        update_instructions={
            "macos": "brew upgrade node",
            "linux": "nvm install --lts  # or: sudo apt update && sudo apt upgrade nodejs",
            "windows": "winget upgrade OpenJS.NodeJS",
        },
        related_tools=["npm", "pnpm", "yarn"],
    ),
    "npm": ToolDefinition(
        name="npm",
        display_name="npm",
        version_command=["npm", "--version"],
        version_regex=r"(\d+\.\d+\.\d+)",
        github_repo="npm/cli",
        project_indicators=["package-lock.json"],
        update_instructions={
            "macos": "npm install -g npm@latest",
            "linux": "npm install -g npm@latest",
            "windows": "npm install -g npm@latest",
        },
    ),
    "pnpm": ToolDefinition(
        name="pnpm",
        display_name="pnpm",
        version_command=["pnpm", "--version"],
        version_regex=r"(\d+\.\d+\.\d+)",
        github_repo="pnpm/pnpm",
        project_indicators=["pnpm-lock.yaml"],
        update_instructions={
            "macos": "brew upgrade pnpm  # or: npm install -g pnpm@latest",
            "linux": "npm install -g pnpm@latest",
            "windows": "npm install -g pnpm@latest",
        },
    ),
    "yarn": ToolDefinition(
        name="yarn",
        display_name="Yarn",
        version_command=["yarn", "--version"],
        version_regex=r"(\d+\.\d+\.\d+)",
        github_repo="yarnpkg/berry",
        project_indicators=["yarn.lock"],
        update_instructions={
            "macos": "brew upgrade yarn  # or: npm install -g yarn@latest",
            "linux": "npm install -g yarn@latest",
            "windows": "npm install -g yarn@latest",
        },
    ),
    "bun": ToolDefinition(
        name="bun",
        display_name="Bun",
        version_command=["bun", "--version"],
        version_regex=r"(\d+\.\d+\.\d+)",
        github_repo="oven-sh/bun",
        project_indicators=["bun.lockb"],
        update_instructions={
            "macos": "brew upgrade bun  # or: bun upgrade",
            "linux": "bun upgrade",
            "windows": "bun upgrade",
        },
    ),
    "deno": ToolDefinition(
        name="deno",
        display_name="Deno",
        version_command=["deno", "--version"],
        version_regex=r"deno\s+(\d+\.\d+\.\d+)",
        github_repo="denoland/deno",
        project_indicators=["deno.json", "deno.jsonc"],
        update_instructions={
            "macos": "brew upgrade deno  # or: deno upgrade",
            "linux": "deno upgrade",
            "windows": "deno upgrade",
        },
    ),
    "python": ToolDefinition(
        name="python",
        display_name="Python",
        version_command=["python3", "--version"],
        version_regex=r"Python\s+(\d+\.\d+\.\d+)",
        github_repo="python/cpython",
        project_indicators=["pyproject.toml", "requirements.txt", "setup.py"],
        update_instructions={
            "macos": "brew upgrade python",
            "linux": "sudo apt update && sudo apt upgrade python3",
            "windows": "winget upgrade Python.Python.3.13",
        },
        related_tools=["uv", "pip"],
    ),
    "uv": ToolDefinition(
        name="uv",
        display_name="uv",
        version_command=["uv", "--version"],
        version_regex=r"uv\s+(\d+\.\d+\.\d+)",
        github_repo="astral-sh/uv",
        project_indicators=["uv.lock", "pyproject.toml"],
        update_instructions={
            "macos": "brew upgrade uv  # or: uv self update",
            "linux": "uv self update",
            "windows": "uv self update",
        },
    ),
    "pip": ToolDefinition(
        name="pip",
        display_name="pip",
        version_command=["pip3", "--version"],
        version_regex=r"pip\s+(\d+\.\d+(?:\.\d+)?)",
        github_repo="pypa/pip",
        project_indicators=["requirements.txt"],
        update_instructions={
            "macos": "pip3 install --upgrade pip",
            "linux": "pip3 install --upgrade pip",
            "windows": "pip install --upgrade pip",
        },
    ),
    "rust": ToolDefinition(
        name="rust",
        display_name="Rust",
        version_command=["rustc", "--version"],
        version_regex=r"rustc\s+(\d+\.\d+\.\d+)",
        github_repo="rust-lang/rust",
        project_indicators=["Cargo.toml"],
        update_instructions={
            "macos": "rustup update stable",
            "linux": "rustup update stable",
            "windows": "rustup update stable",
        },
        related_tools=["cargo"],
    ),
    "cargo": ToolDefinition(
        name="cargo",
        display_name="Cargo",
        version_command=["cargo", "--version"],
        version_regex=r"cargo\s+(\d+\.\d+\.\d+)",
        github_repo="rust-lang/cargo",
        project_indicators=["Cargo.toml"],
        update_instructions={
            "macos": "rustup update stable",
            "linux": "rustup update stable",
            "windows": "rustup update stable",
        },
    ),
    "dart": ToolDefinition(
        name="dart",
        display_name="Dart",
        version_command=["dart", "--version"],
        version_regex=r"Dart SDK version:\s*(\d+\.\d+\.\d+)",
        github_repo="dart-lang/sdk",
        project_indicators=["pubspec.yaml"],
        update_instructions={
            "macos": "brew upgrade dart",
            "linux": "sudo apt update && sudo apt upgrade dart",
            "windows": "choco upgrade dart-sdk",
        },
        related_tools=["flutter"],
    ),
    "flutter": ToolDefinition(
        name="flutter",
        display_name="Flutter",
        version_command=["flutter", "--version"],
        version_regex=r"Flutter\s+(\d+\.\d+\.\d+)",
        github_repo="flutter/flutter",
        project_indicators=["pubspec.yaml"],
        update_instructions={
            "macos": "flutter upgrade",
            "linux": "flutter upgrade",
            "windows": "flutter upgrade",
        },
    ),
    "go": ToolDefinition(
        name="go",
        display_name="Go",
        version_command=["go", "version"],
        version_regex=r"go(\d+\.\d+\.\d+)",
        official_api_url="https://go.dev/dl/?mode=json",
        project_indicators=["go.mod", "go.sum"],
        update_instructions={
            "macos": "brew upgrade go",
            "linux": "sudo apt update && sudo apt upgrade golang",
            "windows": "winget upgrade GoLang.Go",
        },
    ),
    "docker": ToolDefinition(
        name="docker",
        display_name="Docker",
        version_command=["docker", "--version"],
        version_regex=r"Docker version\s+(\d+\.\d+\.\d+)",
        github_repo="docker/cli",
        project_indicators=["Dockerfile", "docker-compose.yml", "docker-compose.yaml"],
        update_instructions={
            "macos": "brew upgrade --cask docker  # or update Docker Desktop",
            "linux": "sudo apt update && sudo apt upgrade docker-ce",
            "windows": "Update Docker Desktop from the app",
        },
    ),
    # Java ecosystem
    "java": ToolDefinition(
        name="java",
        display_name="Java",
        version_command=["java", "--version"],
        version_regex=r"openjdk\s+(\d+\.\d+\.\d+)|java\s+(\d+\.\d+\.\d+)",
        github_repo="adoptium/temurin-build",
        project_indicators=["pom.xml", "build.gradle", "build.gradle.kts"],
        update_instructions={
            "macos": "brew upgrade openjdk  # or: sdk upgrade java",
            "linux": "sudo apt update && sudo apt upgrade openjdk-21-jdk",
            "windows": "winget upgrade EclipseAdoptium.Temurin.21.JDK",
        },
        related_tools=["maven", "gradle"],
    ),
    "maven": ToolDefinition(
        name="maven",
        display_name="Maven",
        version_command=["mvn", "--version"],
        version_regex=r"Apache Maven\s+(\d+\.\d+\.\d+)",
        github_repo="apache/maven",
        project_indicators=["pom.xml"],
        update_instructions={
            "macos": "brew upgrade maven",
            "linux": "sudo apt update && sudo apt upgrade maven",
            "windows": "choco upgrade maven",
        },
    ),
    "gradle": ToolDefinition(
        name="gradle",
        display_name="Gradle",
        version_command=["gradle", "--version"],
        version_regex=r"Gradle\s+(\d+\.\d+(?:\.\d+)?)",
        github_repo="gradle/gradle",
        project_indicators=["build.gradle", "build.gradle.kts", "settings.gradle"],
        update_instructions={
            "macos": "brew upgrade gradle  # or: ./gradlew wrapper --gradle-version=latest",
            "linux": "sdk upgrade gradle",
            "windows": "choco upgrade gradle",
        },
    ),
    # Ruby ecosystem
    "ruby": ToolDefinition(
        name="ruby",
        display_name="Ruby",
        version_command=["ruby", "--version"],
        version_regex=r"ruby\s+(\d+\.\d+\.\d+)",
        github_repo="ruby/ruby",
        project_indicators=["Gemfile", "*.gemspec"],
        update_instructions={
            "macos": "brew upgrade ruby  # or: rbenv install <version>",
            "linux": "rbenv install <version>  # or: rvm install <version>",
            "windows": "choco upgrade ruby",
        },
        related_tools=["bundler"],
    ),
    "bundler": ToolDefinition(
        name="bundler",
        display_name="Bundler",
        version_command=["bundle", "--version"],
        version_regex=r"Bundler version\s+(\d+\.\d+\.\d+)",
        github_repo="rubygems/rubygems",
        project_indicators=["Gemfile", "Gemfile.lock"],
        update_instructions={
            "macos": "gem update bundler",
            "linux": "gem update bundler",
            "windows": "gem update bundler",
        },
    ),
    # PHP ecosystem
    "php": ToolDefinition(
        name="php",
        display_name="PHP",
        version_command=["php", "--version"],
        version_regex=r"PHP\s+(\d+\.\d+\.\d+)",
        github_repo="php/php-src",
        project_indicators=["composer.json", "composer.lock"],
        update_instructions={
            "macos": "brew upgrade php",
            "linux": "sudo apt update && sudo apt upgrade php",
            "windows": "choco upgrade php",
        },
        related_tools=["composer"],
    ),
    "composer": ToolDefinition(
        name="composer",
        display_name="Composer",
        version_command=["composer", "--version"],
        version_regex=r"Composer version\s+(\d+\.\d+\.\d+)",
        github_repo="composer/composer",
        project_indicators=["composer.json", "composer.lock"],
        update_instructions={
            "macos": "brew upgrade composer  # or: composer self-update",
            "linux": "composer self-update",
            "windows": "choco upgrade composer",
        },
    ),
}


def get_tool_definition(name: str) -> ToolDefinition | None:
    """Get a tool definition by name."""
    return TOOL_DEFINITIONS.get(name.lower())


def get_all_tool_names() -> list[str]:
    """Get list of all supported tool names."""
    return list(TOOL_DEFINITIONS.keys())


def get_tools_for_project_files(files: list[str]) -> list[str]:
    """Get relevant tools based on project files present.

    Args:
        files: List of filenames in the project root

    Returns:
        List of tool names relevant to this project
    """
    relevant_tools: set[str] = set()

    for tool_name, definition in TOOL_DEFINITIONS.items():
        for indicator in definition.project_indicators:
            if indicator in files:
                relevant_tools.add(tool_name)
                # Also add related tools
                for related in definition.related_tools:
                    relevant_tools.add(related)
                break

    return sorted(relevant_tools)
