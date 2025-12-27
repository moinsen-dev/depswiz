"""Monorepo/workspace detection."""

import json
import tomllib
from dataclasses import dataclass
from pathlib import Path

import yaml

from depswiz.core.logging import get_logger
from depswiz.plugins import get_all_plugins

logger = get_logger("monorepo.detector")


@dataclass
class WorkspaceMember:
    """Represents a workspace member."""

    path: Path
    language: str
    name: str | None = None


class WorkspaceDetector:
    """Detects and enumerates workspace members across all ecosystems."""

    def detect(self, path: Path) -> list[WorkspaceMember]:
        """Detect all workspace members at the given path.

        Args:
            path: Root path to search from

        Returns:
            List of WorkspaceMember objects
        """
        members = []

        for plugin in get_all_plugins():
            if plugin.supports_workspaces():
                workspace_paths = plugin.detect_workspaces(path)
                for workspace_path in workspace_paths:
                    name = self._get_workspace_name(workspace_path, plugin.name)
                    members.append(
                        WorkspaceMember(
                            path=workspace_path,
                            language=plugin.name,
                            name=name,
                        )
                    )

        return members

    def _get_workspace_name(self, path: Path, language: str) -> str:
        """Get the name of a workspace member."""
        # Try to extract name from manifest
        if language == "rust":
            return self._get_cargo_name(path)
        elif language == "javascript":
            return self._get_npm_name(path)
        elif language == "dart":
            return self._get_pub_name(path)

        return path.name

    def _get_cargo_name(self, path: Path) -> str:
        """Get package name from Cargo.toml."""
        try:
            with open(path / "Cargo.toml", "rb") as f:
                data = tomllib.load(f)
            return data.get("package", {}).get("name", path.name)
        except tomllib.TOMLDecodeError as e:
            logger.debug("Failed to parse Cargo.toml at %s: %s", path, e)
        except OSError as e:
            logger.debug("Failed to read Cargo.toml at %s: %s", path, e)
        except Exception as e:
            logger.debug("Unexpected error reading Cargo.toml at %s: %s", path, e)
        return path.name

    def _get_npm_name(self, path: Path) -> str:
        """Get package name from package.json."""
        try:
            with open(path / "package.json") as f:
                data = json.load(f)
            return data.get("name", path.name)
        except json.JSONDecodeError as e:
            logger.debug("Failed to parse package.json at %s: %s", path, e)
        except OSError as e:
            logger.debug("Failed to read package.json at %s: %s", path, e)
        except Exception as e:
            logger.debug("Unexpected error reading package.json at %s: %s", path, e)
        return path.name

    def _get_pub_name(self, path: Path) -> str:
        """Get package name from pubspec.yaml."""
        try:
            with open(path / "pubspec.yaml") as f:
                data = yaml.safe_load(f)
            return data.get("name", path.name)
        except yaml.YAMLError as e:
            logger.debug("Failed to parse pubspec.yaml at %s: %s", path, e)
        except OSError as e:
            logger.debug("Failed to read pubspec.yaml at %s: %s", path, e)
        except Exception as e:
            logger.debug("Unexpected error reading pubspec.yaml at %s: %s", path, e)
        return path.name

    def is_workspace_root(self, path: Path) -> bool:
        """Check if the given path is a workspace root.

        Args:
            path: Path to check

        Returns:
            True if any plugin detects workspace configuration
        """
        for plugin in get_all_plugins():
            if plugin.supports_workspaces():
                if plugin.detect_workspaces(path):
                    return True
        return False

    def get_workspace_info(self, path: Path) -> dict:
        """Get detailed workspace information.

        Args:
            path: Root path

        Returns:
            Dictionary with workspace info
        """
        members = self.detect(path)

        # Group by language
        by_language: dict[str, list[WorkspaceMember]] = {}
        for member in members:
            if member.language not in by_language:
                by_language[member.language] = []
            by_language[member.language].append(member)

        return {
            "is_workspace": len(members) > 0,
            "total_members": len(members),
            "members": members,
            "by_language": by_language,
            "languages": list(by_language.keys()),
        }
