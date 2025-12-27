"""Caching utilities for depswiz."""

from pathlib import Path
from typing import Optional, Any
import hashlib
import json

from diskcache import Cache

from depswiz.core.config import CacheConfig


class DepsWizCache:
    """Cache manager for depswiz."""

    def __init__(self, config: Optional[CacheConfig] = None):
        if config is None:
            config = CacheConfig()

        self.config = config
        self.enabled = config.enabled
        self._cache: Optional[Cache] = None

        if self.enabled:
            cache_dir = Path(config.directory).expanduser()
            cache_dir.mkdir(parents=True, exist_ok=True)
            self._cache = Cache(str(cache_dir))

    def _make_key(self, prefix: str, *args: Any) -> str:
        """Create a cache key from prefix and arguments."""
        key_data = json.dumps([prefix, *[str(a) for a in args]], sort_keys=True)
        return hashlib.sha256(key_data.encode()).hexdigest()[:32]

    def get(self, prefix: str, *args: Any) -> Optional[Any]:
        """Get a value from cache."""
        if not self.enabled or self._cache is None:
            return None

        key = self._make_key(prefix, *args)
        return self._cache.get(key)

    def set(self, prefix: str, *args: Any, value: Any) -> None:
        """Set a value in cache."""
        if not self.enabled or self._cache is None:
            return

        key = self._make_key(prefix, *args)
        self._cache.set(key, value, expire=self.config.ttl_seconds)

    def get_package_info(self, language: str, package_name: str) -> Optional[dict]:
        """Get cached package information."""
        return self.get("pkg", language, package_name)

    def set_package_info(self, language: str, package_name: str, info: dict) -> None:
        """Cache package information."""
        self.set("pkg", language, package_name, value=info)

    def get_vulnerabilities(self, language: str, package_name: str, version: str) -> Optional[list]:
        """Get cached vulnerabilities."""
        return self.get("vuln", language, package_name, version)

    def set_vulnerabilities(self, language: str, package_name: str, version: str, vulns: list) -> None:
        """Cache vulnerabilities."""
        self.set("vuln", language, package_name, version, value=vulns)

    def clear(self) -> None:
        """Clear the cache."""
        if self._cache is not None:
            self._cache.clear()

    def close(self) -> None:
        """Close the cache."""
        if self._cache is not None:
            self._cache.close()
