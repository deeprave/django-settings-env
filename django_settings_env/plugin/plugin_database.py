import re

from . import EnvPlugin, ConfigDict, register_plugin, is_true

POSTGRES_ENGINE = "django.db.backends.postgresql"
MYSQL_ENGINE = "django.db.backends.mysql"
SQLITE_ENGINE = "django.db.backends.sqlite3"

DB_ENGINES = {
    "postgres": POSTGRES_ENGINE,
    "postgresql": POSTGRES_ENGINE,
    "psql": POSTGRES_ENGINE,
    "pgsql": POSTGRES_ENGINE,
    "postgis": "django.contrib.gis.db.backends.postgis",
    "mysql": MYSQL_ENGINE,
    "mysql2": MYSQL_ENGINE,
    "mysql-connector": "mysql.connector.django",
    "mysqlgis": "django.contrib.gis.db.backends.mysql",
    "mssql": "sql_server.pyodbc",
    "oracle": "django.db.backends.oracle",
    "pyodbc": "sql_server.pyodbc",
    "redshift": "django_redshift_backend",
    "spatialite": "django.contrib.gis.db.backends.spatialite",
    "sqlite": SQLITE_ENGINE,
    "ldap": "ldapdb.backends.ldap",
}

# Django alias keys that must not be passed through as libpq/driver OPTIONS.
# Match query keys case-insensitively, then store these canonical names.
DJANGO_DATABASE_SETTINGS = {
    "CONN_HEALTH_CHECKS": "bool",
    "CONN_MAX_AGE": "max_age",
    "ATOMIC_REQUESTS": "bool",
    "AUTOCOMMIT": "bool",
    "DISABLE_SERVER_SIDE_CURSORS": "bool",
    "TIME_ZONE": "raw",
    "TEST": "raw",
}

_UNLIMITED_CONN_MAX_AGE = frozenset({"", "none", "null"})
_DJANGO_DATABASE_SETTINGS_LOOKUP = {
    name.lower(): (name, kind) for name, kind in DJANGO_DATABASE_SETTINGS.items()
}


def is_postgres(engine):
    return engine in (
        POSTGRES_ENGINE,
        "django.db.backends.postgresql_psycopg2",
        "django.contrib.gis.db.backends.postgis",
        "django_redshift_backend",
    )


def _set_alias_setting(config: ConfigDict, key: str, value) -> None:
    if value is None:
        config.set_none(key)
    else:
        config[key] = value


def _coerce_conn_max_age(value):
    if value is None:
        return None
    if isinstance(value, str) and value.strip().lower() in _UNLIMITED_CONN_MAX_AGE:
        return None
    return int(value)


def _coerce_alias_setting(kind: str, value):
    if kind == "bool":
        return is_true(value)
    if kind == "max_age":
        return _coerce_conn_max_age(value)
    return value


def _promote_django_database_settings(config: dict, options: dict) -> None:
    for key in list(options):
        match = _DJANGO_DATABASE_SETTINGS_LOOKUP.get(key.lower())
        if match is None:
            continue
        name, kind = match
        _set_alias_setting(config, name, _coerce_alias_setting(kind, options.pop(key)))


@register_plugin("database_url")
class DatabasePlugin(EnvPlugin):
    """
    Plugin for handling database configuration
    """

    VAR = "DATABASE_URL"
    CONTEXTS = ["database"]

    def get_backend(self, url: str, **kwargs) -> object:
        # sourcery skip: extract-method
        parsed = self.parse_url(url, context=self.CONTEXTS)
        backend = kwargs.get("backend", None)
        options = kwargs.get("options", {})
        config = ConfigDict()
        try:
            scheme = self.resolve_scheme(parsed, DB_ENGINES)
        except KeyError as e:
            raise ValueError(f"Unsupported database scheme: {parsed.scheme}") from e
        if scheme == "sqlite":
            config["NAME"] = (
                ":memory:"
                if not parsed.path or re.match(r"/:?memory:?", parsed.path)
                else parsed.path
            )
            config["ENGINE"] = backend or SQLITE_ENGINE
        else:
            config["ENGINE"] = backend or DB_ENGINES[scheme]
            config["NAME"] = parsed.path[1:] if parsed.path else parsed.path
            config["HOST"] = parsed.hostname
            config["PORT"] = parsed.port or None
            config["USER"] = parsed.username
            config["PASSWORD"] = parsed.password
        if parsed.qs:
            options |= parsed.qs
        _promote_django_database_settings(config, options)
        if options:
            if schema := options.pop("currentSchema", None):
                if is_postgres(config["ENGINE"]):
                    options["options"] = f"-c search_path={schema}"
            config["OPTIONS"] = options
        return config
