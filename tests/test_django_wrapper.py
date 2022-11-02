import contextlib
import io
import pytest

from django.core.exceptions import ImproperlyConfigured

from django_settings_env import Env, dot_env

try:
    import class_settings
except ImportError:
    class_settings = None



TEST_ENV = [
    '# This is an example .env file',
    'DATABASE_URL=postgresql://username:password@localhost/database_name',
    'CACHE_URL=memcache://localhost:11211',
    'REDIS_URL=redis://localhost:6379/5',
    'QUOTED_VALUE="some double quoted value"',
    'INTVALUE=225',
    'FLOATVALUE=54.92',
    'BOOLVALUETRUE=True',
    'BOOLVALUEFALSE=off',
    'LISTOFQUOTEDVALUES=1,"two",3,\'four\'',
    'ALISTOFIPS=::1,127.0.0.1,mydomain.com',
]


@contextlib.contextmanager
def dotenv(ignored):
    _ = ignored
    yield io.StringIO("\n".join(TEST_ENV))


def test_env_db(monkeypatch):
    monkeypatch.setattr(dot_env, 'open_env', dotenv)
    env = Env()
    env.read_env()

    database = env.database_url()
    assert database['NAME'] == 'database_name'
    assert database['USER'] == 'username'
    assert database['PASSWORD'] == 'password'
    assert database['HOST'] == 'localhost'
    assert database['ENGINE'] == 'django.db.backends.postgresql'


def test_env_memcached(monkeypatch):
    monkeypatch.setattr(dot_env, 'open_env', dotenv)
    env = Env()
    env.read_env()

    cache = env.cache_url()
    assert cache['LOCATION'] == 'localhost:11211'
    assert cache['BACKEND'] == 'django.core.cache.backends.memcached.MemcachedCache'


def test_env_redis(monkeypatch):
    monkeypatch.setattr(dot_env, 'open_env', dotenv)
    env = Env()
    env.read_env()

    cache = env.cache_url('REDIS_URL')
    assert cache['LOCATION'] == 'redis://localhost:6379/5'
    assert cache['BACKEND'] == 'django_redis.cache.RedisCache'


def test_env_email(monkeypatch):
    monkeypatch.setattr(dot_env, 'open_env', dotenv)
    with pytest.raises(ImproperlyConfigured):
        env = Env()
        env.read_env()
        env.email_url()

    env['EMAIL_URL'] = 'smtps://user@example.com:secret@smtp.example.com:587'
    email = env.email_url()
    assert email['EMAIL_HOST_USER'] == 'user@example.com'
    assert email['EMAIL_HOST_PASSWORD'] == 'secret'
    assert email['EMAIL_HOST'] == 'smtp.example.com'
    assert email['EMAIL_PORT'] == 587

    env['EMAIL_URL'] = 'amazonses://user@example.com'
    email = env.email_url()
    assert email['EMAIL_BACKEND'] == 'django_ses.SESBackend'
    assert email['EMAIL_HOST_USER'] == 'user'
    assert email['EMAIL_HOST'] == 'example.com'


def test_env_search(monkeypatch):
    monkeypatch.setattr(dot_env, 'open_env', dotenv)
    with pytest.raises(ImproperlyConfigured):
        env = Env()
        env.read_env()
        env.search_url()

    env['SEARCH_URL'] = 'elasticsearch2://127.0.0.1:9200/index'
    search = env.search_url()
    assert search['ENGINE'] == 'haystack.backends.elasticsearch2_backend.Elasticsearch2SearchEngine'
    assert search['URL'] == 'http://127.0.0.1:9200'
    assert search['INDEX_NAME'] == 'index'


def test_env_queue(monkeypatch):
    monkeypatch.setattr(dot_env, 'open_env', dotenv)
    with pytest.raises(ImproperlyConfigured):
        env = Env()
        env.read_env()
        env.queue_url()
    env['QUEUE_URL'] = 'rabbitmq://localhost'
    queue = env.queue_url(backend='mq.backends.RabbitMQ.create_queue')
    assert queue['QUEUE_BACKEND'] == 'mq.backends.RabbitMQ.create_queue'
    assert queue['RABBITMQ_HOST'] == 'localhost'
    assert queue['RABBITMQ_PORT'] == 5672

    env['QUEUE_URL'] = 'rabbitmq://localhost:5555'
    queue = env.queue_url(backend='mq.backends.rabbitmq_backend.create_queue')
    assert queue['RABBITMQ_PORT'] == 5555

    env['QUEUE_URL'] = 'rabbitmq:/var/run/rabbitmq.sock'
    queue = env.queue_url(backend='mq.backends.rabbitmq_backend.create_queue')
    assert not queue['RABBITMQ_HOST']
    assert not queue['RABBITMQ_PORT']
    assert queue['RABBITMQ_LOCATION'] == 'unix:///var/run/rabbitmq.sock'

    env['AWS_SQS_URL'] = 'amazon-sqs://2138954170.sqs.amazon.com/'
    queue = env.queue_url('AWS_SQS_URL', backend='mq.backends.sqs_backend.create_queue')


@pytest.mark.skipif(class_settings is None, reason="class_settings not installed")
def test_class_settings_env(monkeypatch):
    monkeypatch.setattr(dot_env, 'open_env', dotenv)
    env = Env(readenv=True)

    class MySettings(class_settings.Settings):
        DATABASE_URL = env()
        CACHES = {'default': env.cache_url()}

    assert MySettings.DATABASE_URL == env['DATABASE_URL']
    assert isinstance(MySettings.CACHES['default'], dict)
    assert MySettings.CACHES['default']['LOCATION'] == 'localhost:11211'


@pytest.mark.skipif(class_settings is not None, reason="class_settings is installed")
def test_module_settings_env(monkeypatch):
    monkeypatch.setattr(dot_env, 'open_env', dotenv)
    env = Env(readenv=True)

    global DATABASE_URL
    DATABASE_URL = env()

    DATABASE_URL = DATABASE_URL.setting('DATABASE_URL')
    assert DATABASE_URL == env['DATABASE_URL']

