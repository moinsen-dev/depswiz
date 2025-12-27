"""Tests for caching utilities."""

from pathlib import Path

import pytest

from depswiz.core.cache import DepsWizCache
from depswiz.core.config import CacheConfig


class TestDepsWizCache:
    """Tests for DepsWizCache class."""

    @pytest.fixture
    def cache_dir(self, tmp_path: Path) -> Path:
        """Create a temporary cache directory."""
        return tmp_path / "cache"

    @pytest.fixture
    def enabled_cache(self, cache_dir: Path) -> DepsWizCache:
        """Create an enabled cache instance."""
        config = CacheConfig(enabled=True, directory=str(cache_dir), ttl_seconds=3600)
        return DepsWizCache(config)

    @pytest.fixture
    def disabled_cache(self) -> DepsWizCache:
        """Create a disabled cache instance."""
        config = CacheConfig(enabled=False)
        return DepsWizCache(config)

    def test_cache_default_config(self, tmp_path: Path) -> None:
        """Test cache with default configuration."""
        cache = DepsWizCache()
        assert cache.enabled is True
        cache.close()

    def test_cache_enabled(self, enabled_cache: DepsWizCache) -> None:
        """Test that cache is enabled when configured."""
        assert enabled_cache.enabled is True
        enabled_cache.close()

    def test_cache_disabled(self, disabled_cache: DepsWizCache) -> None:
        """Test that cache is disabled when configured."""
        assert disabled_cache.enabled is False

    def test_set_and_get(self, enabled_cache: DepsWizCache) -> None:
        """Test basic set and get operations."""
        enabled_cache.set("test", "key1", "key2", value="test_value")
        result = enabled_cache.get("test", "key1", "key2")
        assert result == "test_value"
        enabled_cache.close()

    def test_get_nonexistent_key(self, enabled_cache: DepsWizCache) -> None:
        """Test getting a non-existent key returns None."""
        result = enabled_cache.get("test", "nonexistent")
        assert result is None
        enabled_cache.close()

    def test_get_disabled_cache(self, disabled_cache: DepsWizCache) -> None:
        """Test getting from disabled cache returns None."""
        result = disabled_cache.get("test", "key")
        assert result is None

    def test_set_disabled_cache(self, disabled_cache: DepsWizCache) -> None:
        """Test setting on disabled cache does nothing."""
        # Should not raise any errors
        disabled_cache.set("test", "key", value="value")
        assert disabled_cache.get("test", "key") is None

    def test_package_info_cache(self, enabled_cache: DepsWizCache) -> None:
        """Test package info caching convenience methods."""
        pkg_info = {"name": "test-pkg", "version": "1.0.0"}
        enabled_cache.set_package_info("python", "test-pkg", pkg_info)
        result = enabled_cache.get_package_info("python", "test-pkg")
        assert result == pkg_info
        enabled_cache.close()

    def test_vulnerabilities_cache(self, enabled_cache: DepsWizCache) -> None:
        """Test vulnerabilities caching convenience methods."""
        vulns = [{"id": "CVE-2024-1234", "severity": "high"}]
        enabled_cache.set_vulnerabilities("python", "test-pkg", "1.0.0", vulns)
        result = enabled_cache.get_vulnerabilities("python", "test-pkg", "1.0.0")
        assert result == vulns
        enabled_cache.close()

    def test_clear_cache(self, enabled_cache: DepsWizCache) -> None:
        """Test clearing the cache."""
        enabled_cache.set("test", "key", value="value")
        enabled_cache.clear()
        result = enabled_cache.get("test", "key")
        assert result is None
        enabled_cache.close()

    def test_close_cache(self, enabled_cache: DepsWizCache) -> None:
        """Test closing the cache."""
        enabled_cache.set("test", "key", value="value")
        enabled_cache.close()
        # Should not raise any errors when closing

    def test_close_disabled_cache(self, disabled_cache: DepsWizCache) -> None:
        """Test closing a disabled cache."""
        disabled_cache.close()
        # Should not raise any errors

    def test_clear_disabled_cache(self, disabled_cache: DepsWizCache) -> None:
        """Test clearing a disabled cache."""
        disabled_cache.clear()
        # Should not raise any errors


class TestCacheKeyGeneration:
    """Tests for cache key generation."""

    @pytest.fixture
    def cache(self, tmp_path: Path) -> DepsWizCache:
        """Create a cache for testing."""
        config = CacheConfig(enabled=True, directory=str(tmp_path / "cache"))
        return DepsWizCache(config)

    def test_different_prefixes_different_keys(self, cache: DepsWizCache) -> None:
        """Test that different prefixes create different keys."""
        cache.set("prefix1", "arg1", value="value1")
        cache.set("prefix2", "arg1", value="value2")
        assert cache.get("prefix1", "arg1") == "value1"
        assert cache.get("prefix2", "arg1") == "value2"
        cache.close()

    def test_different_args_different_keys(self, cache: DepsWizCache) -> None:
        """Test that different arguments create different keys."""
        cache.set("prefix", "arg1", value="value1")
        cache.set("prefix", "arg2", value="value2")
        assert cache.get("prefix", "arg1") == "value1"
        assert cache.get("prefix", "arg2") == "value2"
        cache.close()

    def test_key_is_deterministic(self, cache: DepsWizCache) -> None:
        """Test that the same inputs always produce the same key."""
        cache.set("prefix", "arg1", "arg2", value="value")
        result = cache.get("prefix", "arg1", "arg2")
        assert result == "value"
        cache.close()
