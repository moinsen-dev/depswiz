"""Docker Compose file parsing utilities."""

from pathlib import Path

import yaml

from depswiz.core.logging import get_logger
from depswiz.plugins.docker.dockerfile import DockerImage, _parse_image_reference

logger = get_logger("plugins.docker.compose")


def parse_compose_file(path: Path) -> list[DockerImage]:
    """Parse a Docker Compose file and extract all service images.

    Supports both docker-compose.yml (v2/v3) and compose.yml formats.

    Args:
        path: Path to the compose file

    Returns:
        List of DockerImage objects representing service images
    """
    images: list[DockerImage] = []

    try:
        content = path.read_text()
        data = yaml.safe_load(content)

        if not data or not isinstance(data, dict):
            return images

        services = data.get("services", {})
        if not isinstance(services, dict):
            return images

        for service_name, service_config in services.items():
            if not isinstance(service_config, dict):
                continue

            # Get image directly specified
            image_ref = service_config.get("image")
            if image_ref and isinstance(image_ref, str):
                name, tag, digest = _parse_image_reference(image_ref)
                images.append(
                    DockerImage(
                        name=name,
                        tag=tag,
                        digest=digest,
                        stage_name=service_name,  # Use service name as stage_name
                    )
                )

            # Note: Services with 'build' instead of 'image' are skipped
            # as they build from a Dockerfile which will be parsed separately

    except yaml.YAMLError as e:
        logger.warning("Failed to parse compose file at %s: %s", path, e)
    except OSError as e:
        logger.warning("Failed to read compose file at %s: %s", path, e)
    except Exception as e:
        logger.debug("Unexpected error parsing compose file at %s: %s", path, e)

    return images
