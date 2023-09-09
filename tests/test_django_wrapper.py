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
    "INTVALUE=225",
    "FLOATVALUE=54.92",
    "BOOLVALUETRUE=True",
    "BOOLVALUEFALSE=off",
    "LISTOFQUOTEDVALUES=1,\"two\",3,'four'",
    "ALISTOFIPS=::1,127.0.0.1,mydomain.com",
]


@contextlib.contextmanager
def dotenv(ignored):
    _ = ignored
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

    cache = env.cache_url()
    assert cache["LOCATION"] == "localhost:11211"
    assert cache["BACKEND"] == "django.core.cache.backends.memcached.MemcachedCache"


def test_env_redis(monkeypatch):
    monkeypatch.setattr(dot_env, "open_env", dotenv)
    env = Env()

    cache = env.cache_url("REDIS_URL")
    assert cache["LOCATION"] == "redis://localhost:6379/5"
    assert cache["BACKEND"] == "django_redis.cache.RedisCache"


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


def test_env_search(monkeypatch):
    monkeypatch.setattr(dot_env, "open_env", dotenv)
    with pytest.raises(ImproperlyConfigured):
        env = Env()
        env.search_url()

    env["SEARCH_URL"] = "elasticsearch2://127.0.0.1:9200/index"
    search = env.search_url()
    assert search["ENGINE"] == "haystack.backends.elasticsearch2_backend.Elasticsearch2SearchEngine"
    assert search["URL"] == "http://127.0.0.1:9200"
    assert search["INDEX_NAME"] == "index"


def test_env_queue(monkeypatch):
    monkeypatch.setattr(dot_env, "open_env", dotenv)
    with pytest.raises(ImproperlyConfigured):
        env = Env()
        env.queue_url()
    env["QUEUE_URL"] = "rabbitmq://localhost"
    queue = env.queue_url(backend="mq.backends.RabbitMQ.create_queue")
    assert queue["QUEUE_BACKEND"] == "mq.backends.RabbitMQ.create_queue"
    assert queue["RABBITMQ_HOST"] == "localhost"
    assert queue["RABBITMQ_PORT"] == 5672

    env["QUEUE_URL"] = "rabbitmq://localhost:5555"
    queue = env.queue_url(backend="mq.backends.rabbitmq_backend.create_queue")
    assert queue["RABBITMQ_PORT"] == 5555

    env["QUEUE_URL"] = "rabbitmq:/var/run/rabbitmq.sock"
    queue = env.queue_url(backend="mq.backends.rabbitmq_backend.create_queue")
    assert not queue["RABBITMQ_HOST"]
    assert not queue["RABBITMQ_PORT"]
    assert queue["RABBITMQ_LOCATION"] == "unix:///var/run/rabbitmq.sock"

    env["AWS_SQS_URL"] = "amazon-sqs://2138954170.sqs.amazon.com/"
    queue = env.queue_url("AWS_SQS_URL", backend="mq.backends.sqs_backend.create_queue")
    assert queue["QUEUE_BACKEND"] == "mq.backends.sqs_backend.create_backend"
    assert queue["AWS_SQS_ENDPOINT"] == "https://2138954170.sqs.amazon.com"


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

    global DATABASE_URL
    DATABASE_URL = env()

    DATABASE_URL = DATABASE_URL.setting("DATABASE_URL")
    assert DATABASE_URL == env["DATABASE_URL"]


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
    assert env.int("INTVALUE", default=99) == 225
    assert env("INTVALUE", default=99, type=int) == 225
    assert env.int("DEFAULTINTVALUE", default=981) == 981
    assert env("DEFAULTINTVALUE", default=981, type=int) == 981
    assert env("DEFAULTINTVALUE", type=int) == 981


def test_env_float(monkeypatch):
    monkeypatch.setattr(envex.dot_env, "open_env", dotenv)
    env = Env()
    assert env.float("FLOATVALUE", default=99.9999) == 54.92
    assert env("FLOATVALUE", default=99.9999, type=float) == 54.92
    assert env.float("DEFAULTFLOATVALUE", default=83.6) == 83.6
    assert env("DEFAULTFLOATVALUE", default=83.6, type=float) == 83.6
    assert env("DEFAULTFLOATVALUE", type=float) == 83.6


def test_is_true():
    env = Env()
    assert env.is_true(1)
    assert env.is_true("1")
    assert not env.is_true(0)
    assert not env.is_true("0")
    assert not env.is_true(b"0")
    assert not env.is_true(False)
    assert not env.is_true("False")
    assert not env.is_true(None)


def test_env_bool(monkeypatch):
    monkeypatch.setattr(envex.dot_env, "open_env", dotenv)
    env = Env()
    assert env.bool("BOOLVALUETRUE", default=False)
    assert env.bool("DEFAULTBOOLVALUETRUE", default=True)
    assert env("DEFAULTBOOLVALUETRUE", default=True, type=bool)
    assert not env.bool("BOOLVALUEFALSE", default=True)
    assert not env.bool("DEFAULTBOOLVALUEFALSE", default=False)
    assert not env("DEFAULTBOOLVALUEFALSE", type=bool)


def test_env_list(monkeypatch):
    monkeypatch.setattr(envex.dot_env, "open_env", dotenv)
    env = Env()

    result = env.list("ALISTOFIPS")
    assert isinstance(result, list)
    assert len(result) == 3
    assert result == ["::1", "127.0.0.1", "mydomain.com"]

    result = env("ALISTOFIPS", type=list)
    assert isinstance(result, list)
    assert len(result) == 3
    assert result == ["::1", "127.0.0.1", "mydomain.com"]

    result = env.list("LISTOFQUOTEDVALUES")
    assert isinstance(result, list)
    assert len(result) == 4
    assert result == ["1", "two", "3", "four"]

    result = env("LISTOFQUOTEDVALUES", type=list)
    assert isinstance(result, list)
    assert len(result) == 4
    assert result == ["1", "two", "3", "four"]
