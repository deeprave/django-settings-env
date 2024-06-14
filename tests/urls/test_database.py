import pytest

from django_settings_env.urls.database import (
    is_postgres,
    db_scheme_handler,
    db_options_handler,
    parse_db_url,
    DJANGO_POSTGRES,
)


@pytest.mark.parametrize(
    "engine, expected",
    [
        (DJANGO_POSTGRES, True),
        ("django.db.backends.postgresql_psycopg2", True),
        ("django.contrib.gis.db.backends.postgis", True),
        ("django_redshift_backend", True),
        ("django.db.backends.mysql", False),
    ],
    ids="postgres postgres_psycopg2 postgis redshift mysql".split(),
)
def test_is_postgres(engine, expected):
    # Act
    result = is_postgres(engine)

    # Assert
    assert result == expected


@pytest.mark.parametrize(
    "config, scheme, engine, expected",
    [
        (
            {},
            "sqlite",
            None,
            {"NAME": ":memory:", "ENGINE": "django.db.backends.sqlite3"},
        ),
        (
            {"NAME": "test.db"},
            "sqlite",
            None,
            {"NAME": "test.db", "ENGINE": "django.db.backends.sqlite3"},
        ),
        ({}, "postgres", None, {"ENGINE": DJANGO_POSTGRES}),
        ({}, "mysql", "custom_engine", {"ENGINE": "custom_engine"}),
        ({}, "unsupported", None, ValueError),
    ],
    ids="sqlite_default sqlite_named postgres_default custom_engine unsupported_scheme".split(),
)
def test_db_scheme_handler(config, scheme, engine, expected):
    # Act and Assert
    # sourcery skip: no-conditionals-in-tests
    if expected is ValueError:
        with pytest.raises(ValueError):
            db_scheme_handler(config, scheme, engine)
    else:
        result = db_scheme_handler(config, scheme, engine)
        assert result == expected


@pytest.mark.parametrize(
    "qs, config, expected",
    [
        ("", {}, {"OPTIONS": {}}),
        (
            "CONN_MAX_AGE=600",
            {},
            {"CONN_MAX_AGE": "600", "OPTIONS": {}},
        ),
        (
            "customOption=value",
            {},
            {"OPTIONS": {"customOption": "value"}},
        ),
        (
            "currentSchema=myschema",
            {"ENGINE": DJANGO_POSTGRES},
            {
                "ENGINE": DJANGO_POSTGRES,
                "OPTIONS": {"options": "-c search_path=myschema"},
            },
        ),
        (
            "currentSchema=myschema",
            {"ENGINE": "django.db.backends.mysql"},
            {"ENGINE": "django.db.backends.mysql", "OPTIONS": {}},
        ),
    ],
    ids="empty_qs conn_max_age custom_option current_schema_postgres current_schema_non_postgres".split(),
)
def test_db_options_handler(qs, config, expected):
    # Act
    result = db_options_handler(config, qs)

    # Assert
    assert result == expected


@pytest.mark.parametrize(
    "raw_url, engine, expected",
    [
        (
            "postgres://user:pass@localhost/dbname",
            None,
            {
                "ENGINE": DJANGO_POSTGRES,
                "NAME": "dbname",
                "USER": "user",
                "PASSWORD": "pass",
                "HOST": "localhost",
                "OPTIONS": {},
            },
        ),
        (
            "sqlite:///mydb.sqlite3",
            None,
            {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": "mydb.sqlite3",
                "OPTIONS": {},
            },
        ),
        (
            "mysql://user:pass@localhost/dbname",
            None,
            {
                "ENGINE": "django.db.backends.mysql",
                "NAME": "dbname",
                "USER": "user",
                "PASSWORD": "pass",
                "HOST": "localhost",
                "OPTIONS": {},
            },
        ),
        (
            "unsupported://user:pass@localhost/dbname",
            None,
            ValueError,
        ),
    ],
    ids="postgres sqlite mysql unsupported".split(),
)
def test_parse_db_url(raw_url, engine, expected):
    # Act and Assert
    # sourcery skip: no-conditionals-in-tests
    if expected is ValueError:
        with pytest.raises(ValueError):
            parse_db_url(raw_url, engine)
    else:
        result = parse_db_url(raw_url, engine)
        assert result == expected
