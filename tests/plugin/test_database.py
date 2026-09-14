import pytest
from django_settings_env.plugin.plugin_database import DB_ENGINES, DatabasePlugin


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
        "NAME": "",
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


@pytest.mark.parametrize(
    ("scheme", "engine"),
    [(scheme, engine) for scheme, engine in DB_ENGINES.items() if scheme != "sqlite"],
)
def test_database_plugin_supports_each_declared_network_scheme(
    database_plugin, scheme, engine
):
    config = database_plugin.get_backend(f"{scheme}://localhost/example")

    assert config["ENGINE"] == engine
    assert config["NAME"] == "example"
    assert config["HOST"] == "localhost"


def test_database_plugin_falls_back_to_the_base_scheme_for_unknown_qualifiers(
    database_plugin,
):
    config = database_plugin.get_backend("postgresql+psycopg://localhost/application")

    assert config["ENGINE"] == DB_ENGINES["postgresql"]
    assert config["NAME"] == "application"


def test_promotes_conn_health_checks_and_keeps_sslmode_in_options(database_plugin):
    url = "postgresql://u:p@localhost/db?CONN_HEALTH_CHECKS=True&sslmode=prefer"
    config = database_plugin.get_backend(url)

    assert config["CONN_HEALTH_CHECKS"] is True
    assert config["OPTIONS"] == {"sslmode": "prefer"}
    assert "CONN_HEALTH_CHECKS" not in config["OPTIONS"]
    assert "conn_health_checks" not in config["OPTIONS"]


def test_lowercase_query_key_promotes_to_canonical_django_name(database_plugin):
    url = "postgresql://u:p@localhost/db?conn_health_checks=true"
    config = database_plugin.get_backend(url)

    assert config["CONN_HEALTH_CHECKS"] is True
    assert "conn_health_checks" not in config


def test_conn_max_age_integer_including_zero_is_kept(database_plugin):
    url = "postgresql://u:p@localhost/db?CONN_MAX_AGE=0"
    config = database_plugin.get_backend(url)

    assert config["CONN_MAX_AGE"] == 0


def test_conn_max_age_none_means_unlimited(database_plugin):
    url = "postgresql://u:p@localhost/db?CONN_MAX_AGE=none"
    config = database_plugin.get_backend(url)

    assert config["CONN_MAX_AGE"] is None


def test_false_boolean_is_kept_not_dropped_by_configdict(database_plugin):
    url = "postgresql://u:p@localhost/db?CONN_HEALTH_CHECKS=false"
    config = database_plugin.get_backend(url)

    assert config["CONN_HEALTH_CHECKS"] is False


def test_mixed_case_unknown_option_stays_in_options_unchanged(database_plugin):
    url = "postgresql://u:p@localhost/db?application_name=rjf"
    config = database_plugin.get_backend(url)

    assert config["OPTIONS"] == {"application_name": "rjf"}
    assert "application_name" not in config


@pytest.mark.parametrize(
    ("query", "key", "expected"),
    [
        ("ATOMIC_REQUESTS=true", "ATOMIC_REQUESTS", True),
        ("AUTOCOMMIT=false", "AUTOCOMMIT", False),
        ("DISABLE_SERVER_SIDE_CURSORS=1", "DISABLE_SERVER_SIDE_CURSORS", True),
        ("TIME_ZONE=UTC", "TIME_ZONE", "UTC"),
    ],
)
def test_promotes_other_django_alias_settings(database_plugin, query, key, expected):
    config = database_plugin.get_backend(f"postgresql://u:p@localhost/db?{query}")

    assert config[key] == expected
    assert key not in config.get("OPTIONS", {})
