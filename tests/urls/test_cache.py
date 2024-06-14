import pytest
from django.utils.version import get_complete_version
from django_settings_env.urls.cache import (
    cache_scheme_handler,
    cache_options_handler,
    parse_cache_url,
)

DJANGO_VERSION = get_complete_version()


@pytest.mark.parametrize(
    "config, scheme, backend, expected",
    [
        (
            {"HOST": "/var/tmp", "NAME": "cache"},
            "filecache",
            None,
            {
                "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
                "LOCATION": "/var/tmp/cache",
            },
        ),
        (
            {"NAME": "/var/tmp/cache"},
            "filecache",
            None,
            {
                "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
                "LOCATION": "/var/tmp/cache",
            },
        ),
        (
            {"HOST": "unix"},
            "redis",
            None,
            {
                "BACKEND": "django.core.cache.backends.redis.RedisCache",
                "LOCATION": "unix:///tmp/redis.sock",
            },
        ),
        (
            {"HOST": "localhost"},
            "dummycache",
            None,
            {"BACKEND": "django.core.cache.backends.dummy.DummyCache"},
        ),
        (
            {"HOST": "", "NAME": "my_cache_table"},
            "dbcache",
            None,
            {
                "BACKEND": "django.core.cache.backends.db.DatabaseCache",
                "LOCATION": "my_cache_table",
            },
        ),
        ({"HOST": "localhost"}, "unknown", None, ValueError),
    ],
    ids=[
        "filecache_with_host_and_name",
        "filecache_with_name_only",
        "redis_with_unix_host",
        "dummycache_with_localhost",
        "dbcache",
        "unknown_scheme",
    ],
)
def test_cache_scheme_handler(config, scheme, backend, expected):
    # Act
    # sourcery skip: no-conditionals-in-tests
    if isinstance(expected, type) and issubclass(expected, Exception):
        with pytest.raises(expected):
            cache_scheme_handler(config, scheme, backend)
    else:
        result = cache_scheme_handler(config, scheme, backend)

        # Assert
        assert result == expected


@pytest.mark.parametrize(
    "config, qs, expected",
    [
        (
            {"LOCATION": "localhost"},
            "db=1",
            {"LOCATION": "localhost?db=1"},
        ),
        (
            {"LOCATION": "localhost"},
            "timeout=10&key_prefix=test",
            {
                "LOCATION": "localhost",
                "OPTIONS": {"timeout": "10", "key_prefix": "test"},
            },
        ),
        ({"LOCATION": "localhost"}, "", {"LOCATION": "localhost"}),
    ],
    ids=["single_db_option", "multiple_options", "empty_query_string"],
)
def test_cache_options_handler(config, qs, expected):
    # Act
    result = cache_options_handler(config, qs)

    # Assert
    assert result == expected


@pytest.mark.parametrize(
    "raw_url, backend, expected",
    [
        (
            "redis://localhost:6379/1",
            None,
            {
                "BACKEND": "django.core.cache.backends.redis.RedisCache",
                "LOCATION": "redis://localhost:6379/1",
            },
        ),
        (
            "filecache:///var/tmp/cache",
            None,
            {
                "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
                "LOCATION": "/var/tmp/cache",
            },
        ),
        (
            "dummycache://localhost",
            None,
            {"BACKEND": "django.core.cache.backends.dummy.DummyCache"},
        ),
    ],
    ids=["redis_url", "filecache_url", "dummycache_url"],
)
def test_parse_cache_url(raw_url, backend, expected):
    # Act
    result = parse_cache_url(raw_url, backend)

    # Assert
    assert result == expected
