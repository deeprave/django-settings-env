import pytest
from django_settings_env.plugin.plugin_cache import CachePlugin


@pytest.fixture
def cache_plugin():
    return CachePlugin()


def test_cache_plugin_get_backend_valid_filecache(cache_plugin):
    url = "filecache://localhost/tmp/cache"
    result = cache_plugin.get_backend(url)
    assert result["BACKEND"] == "django.core.cache.backends.filebased.FileBasedCache"
    assert result["LOCATION"] == "localhost/tmp/cache"


def test_cache_plugin_get_backend_valid_redis(cache_plugin):
    url = "redis://localhost:6379/0"
    result = cache_plugin.get_backend(url)
    assert result["BACKEND"] == "django.core.cache.backends.redis.RedisCache"
    assert result["LOCATION"] == "redis://localhost:6379/0"


def test_cache_plugin_get_backend_valid_dummycache(cache_plugin):
    url = "dummycache://"
    result = cache_plugin.get_backend(url)
    assert result["BACKEND"] == "django.core.cache.backends.dummy.DummyCache"
    assert "LOCATION" not in result or not result["LOCATION"]
    assert "NAME" not in result or not result["NAME"]


def test_cache_plugin_get_backend_valid_memcache(cache_plugin):
    url = "memcache://localhost:11211"
    result = cache_plugin.get_backend(url)
    assert result["BACKEND"] == "django.core.cache.backends.memcached.MemcachedCache"
    assert result["LOCATION"] == "localhost:11211/"


def test_cache_plugin_get_backend_unknown_scheme(cache_plugin):
    url = "unknownscheme://example.com"
    with pytest.raises(ValueError, match="Unknown cache scheme: unknownscheme"):
        cache_plugin.get_backend(url)


def test_cache_plugin_get_backend_options_handling(cache_plugin):
    url = "redis://localhost:6379/0?timeout=300&key_prefix=my_prefix"
    result = cache_plugin.get_backend(url, options={"extra_option": "value"})
    assert result["BACKEND"] == "django.core.cache.backends.redis.RedisCache"
    assert result["LOCATION"] == "redis://localhost:6379/0"
    assert result["OPTIONS"]["extra_option"] == "value"
    assert result["TIMEOUT"] == 300
    assert result["KEY_PREFIX"] == "my_prefix"


def test_cache_plugin_get_backend_special_case_unix(cache_plugin):
    url = "redis://unix/tmp/redis.sock"
    result = cache_plugin.get_backend(url)
    assert result["BACKEND"] == "django.core.cache.backends.redis.RedisCache"
    assert result["LOCATION"] == "unix:///tmp/redis.sock"


def test_cache_plugin_get_backend_invalid_scheme(cache_plugin):
    url = "cache_unknown_scheme:///"
    with pytest.raises(ValueError, match="Missing cache scheme or url parse error"):
        cache_plugin.get_backend(url)
