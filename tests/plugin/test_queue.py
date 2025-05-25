import pytest
from django_settings_env.plugin.plugin_queue import QueuePlugin


@pytest.fixture
def queue_plugin():
    return QueuePlugin()


def test_queue_plugin_get_backend_valid_redis(queue_plugin):
    url = "redis://localhost:6379/0"
    result = queue_plugin.get_backend(url)
    assert result["BACKEND"] == "django_redis.cache.RedisCache"
    assert result["URL"] == "redis://localhost:6379/0"


def test_queue_plugin_get_backend_valid_rediss(queue_plugin):
    url = "rediss://localhost:6379/0"
    result = queue_plugin.get_backend(url)
    assert result["BACKEND"] == "django_redis.cache.RedisCache"
    assert result["URL"] == "rediss://localhost:6379/0"


def test_queue_plugin_get_backend_unknown_scheme(queue_plugin):
    url = "unknownscheme://example.com"
    with pytest.raises(ValueError, match="Unknown queue scheme: unknownscheme"):
        queue_plugin.get_backend(url)


def test_queue_plugin_get_backend_options_handling(queue_plugin):
    url = "redis://localhost:6379/0?timeout=300&key_prefix=my_prefix"
    result = queue_plugin.get_backend(url, options={"extra_option": "value"})
    assert result["BACKEND"] == "django_redis.cache.RedisCache"
    assert result["URL"] == "redis://localhost:6379/0"
    assert result["OPTIONS"]["extra_option"] == "value"
    assert result["TIMEOUT"] == 300
    assert result["KEY_PREFIX"] == "my_prefix"


def test_queue_plugin_get_backend_special_case_unix(queue_plugin):
    url = "redis://unix/tmp/redis.sock"
    result = queue_plugin.get_backend(url)
    assert result["BACKEND"] == "django_redis.cache.RedisCache"
    assert result["URL"] == "unix:///tmp/redis.sock"


def test_queue_plugin_get_backend_special_case_socket(queue_plugin):
    url = "redis+socket:///var/run/redis/redis.sock"
    result = queue_plugin.get_backend(url)
    assert result["BACKEND"] == "django_redis.cache.RedisCache"
    assert result["URL"] == "unix:///var/run/redis/redis.sock"


def test_queue_plugin_get_backend_invalid_scheme(queue_plugin):
    url = "queue_unknown_scheme:///"
    with pytest.raises(ValueError, match="Missing queue scheme or url parse error"):
        queue_plugin.get_backend(url)
