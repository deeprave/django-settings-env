import contextlib
import io

import envex
import pytest
from django.core.exceptions import ImproperlyConfigured

from django_settings_env import Env, dot_env

try:
    import class_settings
except ImportError:
    class_settings = None

TEST_ENV = [
    "# This is an example .env file",
    "DATABASE_URL=postgresql://username:password@localhost/database_name",
    "CACHE_URL=memcache://localhost:11211",
    "REDIS_URL=redis://localhost:6379/5",
    'QUOTED_VALUE="some double quoted value"',
    "INT_VALUE=225",
    "FLOAT_VALUE=54.92",
    "BOOL_VALUE_TRUE=True",
    "BOOL_VALUE_FALSE=off",
    "LIST_OF_QUOTED_VALUES=1,\"two\",3,'four'",
    "A_LIST_OF_IPS=::1,127.0.0.1,mydomain.com",
]


@contextlib.contextmanager
def dotenv(ignored):
    _ = ignored
    #   yield io.BytesIO("\n".join(TEST_ENV).encode("utf-8"))
    yield io.StringIO("\n".join(TEST_ENV))


def test_env_db(monkeypatch):
    monkeypatch.setattr(dot_env, "open_env", dotenv)
    env = Env()

    database = env.database_url()
    assert database["NAME"] == "database_name"
    assert database["USER"] == "username"
    assert database["PASSWORD"] == "password"
    assert database["HOST"] == "localhost"
    assert database["ENGINE"] == "django.db.backends.postgresql"


def test_env_memcached(monkeypatch):
    monkeypatch.setattr(dot_env, "open_env", dotenv)
    env = Env()

    django_cache = env.cache_url()
    assert django_cache["LOCATION"] == "localhost:11211/"
    assert (
        django_cache["BACKEND"] == "django.core.cache.backends.memcached.MemcachedCache"
    )


def test_env_redis(monkeypatch):
    monkeypatch.setattr(dot_env, "open_env", dotenv)
    env = Env()

    django_cache = env.cache_url("REDIS_URL")
    assert django_cache["LOCATION"] == "redis://localhost:6379/5"
    assert django_cache["BACKEND"] == "django.core.cache.backends.redis.RedisCache"


def test_env_email(monkeypatch):
    monkeypatch.setattr(dot_env, "open_env", dotenv)
    with pytest.raises(ImproperlyConfigured):
        env = Env()
        env.email_url()

    env["EMAIL_URL"] = "smtps://user@example.com:secret@smtp.example.com:587"
    email = env.email_url()
    assert email["EMAIL_HOST_USER"] == "user@example.com"
    assert email["EMAIL_HOST_PASSWORD"] == "secret"
    assert email["EMAIL_HOST"] == "smtp.example.com"
    assert email["EMAIL_PORT"] == 587

    env["EMAIL_URL"] = "amazonses://user@example.com"
    email = env.email_url()
    assert email["EMAIL_BACKEND"] == "django_ses.SESBackend"
    assert email["EMAIL_HOST_USER"] == "user"
    assert email["EMAIL_HOST"] == "example.com"


@pytest.mark.parametrize(
    "search_url, expected_backend, expected_url, expected_hosts, expected_index_name",
    [
        (
            "elasticsearch2://127.0.0.1:9200/index?SCHEME=http",
            "haystack.backends.elasticsearch2_backend.Elasticsearch2SearchEngine",
            "http://127.0.0.1:9200",
            None,
            "index",
        ),
        (
            "elasticsearch://127.0.0.1:9200/index?SCHEME=http",
            "haystack.backends.elasticsearch_backend.ElasticsearchSearchEngine",
            "http://127.0.0.1:9200",
            None,
            "index",
        ),
        (
            "elasticsearch+dsl://127.0.0.1:9200?SCHEME=http",
            None,
            None,
            "http://127.0.0.1:9200/",
            None,
        ),
        (
            "elasticsearch-dsl://127.0.0.1:9200",
            None,
            None,
            "https://127.0.0.1:9200/",
            None,
        ),
    ],
)
def test_search_url(
    monkeypatch,
    search_url,
    expected_backend,
    expected_url,
    expected_hosts,
    expected_index_name,
):
    monkeypatch.setattr(dot_env, "open_env", dotenv)
    env = Env()

    env["SEARCH_URL"] = search_url
    result = env.search_url()

    # sourcery skip: no-conditionals-in-tests
    if expected_backend:
        assert result["BACKEND"] == expected_backend
    if expected_url:
        assert result["URL"] == expected_url
    if expected_hosts:
        assert result["hosts"] == expected_hosts
    if expected_index_name:
        assert result["INDEX_NAME"] == expected_index_name


@pytest.mark.skipif(class_settings is None, reason="class_settings not installed")
def test_class_settings_env(monkeypatch):
    monkeypatch.setattr(dot_env, "open_env", dotenv)
    env = Env()

    # noinspection PyUnresolvedReferences
    class MySettings(class_settings.Settings):
        DATABASE_URL = env()
        CACHES = {"default": env.cache_url()}

    assert MySettings.DATABASE_URL == env["DATABASE_URL"]
    assert isinstance(MySettings.CACHES["default"], dict)
    assert MySettings.CACHES["default"]["LOCATION"] == "localhost:11211"


@pytest.mark.skipif(class_settings is not None, reason="class_settings is installed")
def test_module_settings_env(monkeypatch):
    monkeypatch.setattr(dot_env, "open_env", dotenv)
    env = Env()

    # noinspection PyGlobalUndefined
    DATABASE_URL = env()

    assert str(DATABASE_URL) == env["DATABASE_URL"]

    class TestClass:
        DATABASE_URL = env()

    assert str(TestClass.DATABASE_URL) == env["DATABASE_URL"]


def test_env_get():
    env = Env(environ={})
    var, val = "MY_VARIABLE", "MY_VARIABLE_VALUE"
    assert var not in env
    value = env(var)
    assert value is None
    value = env(var, default=val)
    assert value == val
    assert var in env
    del env[var]
    assert var not in env
    with pytest.raises(ImproperlyConfigured):
        _ = env[var]
    env[var] = val
    val = env.pop(var)
    assert value == val
    assert var not in env


def test_env_int(monkeypatch):
    monkeypatch.setattr(envex.dot_env, "open_env", dotenv)
    env = Env()
    assert env.int("INT_VALUE", default=99) == 225
    assert env("INT_VALUE", default=99, type=int) == 225
    assert env.int("DEFAULT_INT_VALUE", default=981) == 981
    assert env("DEFAULT_INT_VALUE", default=981, type=int) == 981
    assert env("DEFAULT_INT_VALUE", type=int) == 981


def test_env_float(monkeypatch):
    monkeypatch.setattr(envex.dot_env, "open_env", dotenv)
    env = Env()
    assert env.float("FLOAT_VALUE", default=99.9999) == 54.92
    assert env("FLOAT_VALUE", default=99.9999, type=float) == 54.92
    assert env.float("DEFAULT_FLOAT_VALUE", default=83.6) == 83.6
    assert env("DEFAULT_FLOAT_VALUE", default=83.6, type=float) == 83.6
    assert env("DEFAULT_FLOAT_VALUE", type=float) == 83.6


def test_env_bool(monkeypatch):
    monkeypatch.setattr(envex.dot_env, "open_env", dotenv)
    env = Env()
    assert env.bool("BOOL_VALUE_TRUE", default=False)
    assert env.bool("DEFAULT_BOOL_VALUE_TRUE", default=True)
    assert env("DEFAULT_BOOL_VALUE_TRUE", default=True, type=bool)
    assert not env.bool("BOOL_VALUE_FALSE", default=True)
    assert not env.bool("DEFAULT_BOOL_VALUE_FALSE", default=False)
    assert not env("DEFAULT_BOOL_VALUE_FALSE", type=bool)


@pytest.mark.parametrize(
    "env_key, expected_length, expected_values",
    [
        ("A_LIST_OF_IPS", 3, ["::1", "127.0.0.1", "mydomain.com"]),
        ("LIST_OF_QUOTED_VALUES", 4, ["1", "two", "3", "four"]),
    ],
)
def test_env_list(monkeypatch, env_key, expected_length, expected_values):
    monkeypatch.setattr(envex.dot_env, "open_env", dotenv)
    env = Env()

    def list_test_common(result, expected_length, expected_values):
        assert isinstance(result, list)
        assert len(result) == expected_length
        assert result == expected_values
        return result

    def list_test(env, env_key, expected_length, expected_values):
        result = env.list(env_key)
        return list_test_common(result, expected_length, expected_values)

    list_test(env, env_key, expected_length, expected_values)


def test_is_all_set():
    env = Env(environ={})

    # Test with single variables
    env["TEST_VAR1"] = "value1"
    assert env.is_all_set("TEST_VAR1")
    assert not env.is_all_set("TEST_VAR2")

    # Test with multiple variables
    env["TEST_VAR2"] = "value2"
    assert env.is_all_set("TEST_VAR1", "TEST_VAR2")
    assert not env.is_all_set("TEST_VAR1", "TEST_VAR3")

    # Test with nested lists/tuples
    env["TEST_VAR3"] = "value3"
    assert env.is_all_set(["TEST_VAR1", "TEST_VAR2"])
    assert env.is_all_set(("TEST_VAR1", "TEST_VAR2"))
    assert env.is_all_set("TEST_VAR1", ["TEST_VAR2", "TEST_VAR3"])
    assert not env.is_all_set("TEST_VAR1", ["TEST_VAR2", "TEST_VAR4"])

    # Test with prefix
    env["DJANGO_PREFIX_VAR"] = "value"
    assert env.is_all_set("PREFIX_VAR", prefix="DJANGO_")

    # Test with a complex nested structure
    assert env.is_all_set("TEST_VAR1", ["TEST_VAR2", ("TEST_VAR3",)])
    assert not env.is_all_set("TEST_VAR1", ["TEST_VAR2", ("TEST_VAR4",)])


def test_is_any_set():
    env = Env(environ={}, readenv=False)

    # Test with single variables
    env["TEST_VAR1"] = "value1"
    assert env.is_any_set("TEST_VAR1")
    assert not env.is_any_set("TEST_VAR2")

    # Test with multiple variables
    assert env.is_any_set("TEST_VAR1", "TEST_VAR2")
    assert env.is_any_set("TEST_VAR2", "TEST_VAR1")
    assert not env.is_any_set("TEST_VAR2", "TEST_VAR3")

    # Test with nested lists/tuples
    env["TEST_VAR3"] = "value3"
    assert env.is_any_set(["TEST_VAR1", "TEST_VAR4"])
    assert env.is_any_set(("TEST_VAR4", "TEST_VAR1"))
    assert env.is_any_set("TEST_VAR4", ["TEST_VAR2", "TEST_VAR3"])
    assert not env.is_any_set("TEST_VAR4", ["TEST_VAR5", "TEST_VAR6"])

    # Test with prefix
    env["DJANGO_PREFIX_VAR"] = "value"
    assert env.is_any_set("PREFIX_VAR", prefix="DJANGO_")

    # Test with complex nested structure
    assert env.is_any_set("TEST_VAR4", ["TEST_VAR5", ("TEST_VAR1",)])
    assert not env.is_any_set("TEST_VAR4", ["TEST_VAR5", ("TEST_VAR6",)])
