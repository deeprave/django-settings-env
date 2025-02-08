import re

from . import EnvPlugin, ConfigDict, register_plugin

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

# DB_OPTIONS = [
#     "CONN_MAX_AGE",
#     "ATOMIC_REQUESTS",
#     "AUTOCOMMIT",
#     "SSLMODE",
#     "SSLROOTCERT",
#     "TEST",
#     # extensions
#     "READ_ONLY",
#     "READONLY",
#     "HTTP_METHODS",
#     "HTTP_WRITE_PATHS",
#     "HTTP_WRITE_STICKY",
# ]


def is_postgres(engine):
    return engine in (
        POSTGRES_ENGINE,
        "django.db.backends.postgresql_psycopg2",
        "django.contrib.gis.db.backends.postgis",
        "django_redshift_backend",
    )


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
        if parsed.scheme == "sqlite":
            config["NAME"] = (
                ":memory:"
                if not parsed.path or re.match(r"/:?memory:?", parsed.path)
                else parsed.path
            )
            config["ENGINE"] = backend or SQLITE_ENGINE
        else:
            try:
                config["ENGINE"] = backend or DB_ENGINES[parsed.scheme]
            except KeyError as e:
                raise ValueError(f"Unsupported database scheme: {parsed.scheme}") from e
            config["NAME"] = parsed.path[1:] if parsed.path else parsed.path
            config["HOST"] = parsed.hostname
            config["PORT"] = parsed.port or None
            config["USER"] = parsed.username
            config["PASSWORD"] = parsed.password
        if parsed.qs:
            options |= parsed.qs
        if options:
            if schema := options.pop("currentSchema", None):
                if is_postgres(config["ENGINE"]):
                    options["options"] = f"-c search_path={schema}"
            config["OPTIONS"] = options
        return config
