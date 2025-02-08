import pytest
from django_settings_env.plugin.plugin_database import DatabasePlugin


@pytest.fixture
def database_plugin():
    return DatabasePlugin()


def test_database_plugin_sqlite(database_plugin):
    url = "sqlite:///memory"
    config = database_plugin.get_backend(url)
    assert config["NAME"] == ":memory:"
    assert config["ENGINE"] == "django.db.backends.sqlite3"
    assert "OPTIONS" not in config


def test_database_plugin_postgres(database_plugin):
    from django.db.backends.postgresql.psycopg_any import IsolationLevel

    url = f"postgres://user:password@localhost/dbname?isolation_level={IsolationLevel.SERIALIZABLE}"
    config = database_plugin.get_backend(url)

    assert config["NAME"] == "dbname"
    assert config["ENGINE"] == "django.db.backends.postgresql"
    assert config["HOST"] == "localhost"
    assert config["USER"] == "user"
    assert config["PASSWORD"] == "password"
    assert config["OPTIONS"] == {"isolation_level": f"{IsolationLevel.SERIALIZABLE}"}


def test_database_plugin_options(database_plugin):
    url = "postgres://user:password@localhost/dbname?currentSchema=myschema"
    config = database_plugin.get_backend(url)
    assert config["OPTIONS"]["options"] == "-c search_path=myschema"


def test_database_plugin_options_service(database_plugin):
    url = "postgres:///?service=my_service&passfile=.my_pgpass"
    config = database_plugin.get_backend(url)
    assert config == {
        "ENGINE": "django.db.backends.postgresql",
        "OPTIONS": {"service": "my_service", "passfile": ".my_pgpass"},
    }


def test_database_plugin_unsupported_scheme(database_plugin):
    url = "unsupported://user:password@localhost/dbname"
    with pytest.raises(ValueError, match="Unsupported database scheme: unsupported"):
        database_plugin.get_backend(url)


def test_database_plugin_missing_engine(database_plugin):
    url = "blahdb://host:6555/path"
    with pytest.raises(ValueError, match="Unsupported database scheme: blahdb"):
        database_plugin.get_backend(url)


def test_database_plugin_get_backend_without_userpass(database_plugin):
    url = "postgres://localhost:5432/mydb"
    config = database_plugin.get_backend(url)
    assert config == {
        "ENGINE": "django.db.backends.postgresql",
        "HOST": "localhost",
        "NAME": "mydb",
        "PORT": 5432,
    }


def test_database_plugin_get_backend_withuserpass(database_plugin):
    url = "postgres://user:password@localhost:5432/mydb"
    config = database_plugin.get_backend(url)
    assert config == {
        "ENGINE": "django.db.backends.postgresql",
        "HOST": "localhost",
        "NAME": "mydb",
        "USER": "user",
        "PORT": 5432,
        "PASSWORD": "password",
    }
