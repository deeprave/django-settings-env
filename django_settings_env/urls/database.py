from typing import Dict, Optional, AnyStr
from urllib.parse import parse_qs

from .url import parse_url

DJANGO_POSTGRES = "django.db.backends.postgresql"
MYSQL_DRIVER = "django.db.backends.mysql"

DB_ENGINES = {
    "postgres": DJANGO_POSTGRES,
    "postgresql": DJANGO_POSTGRES,
    "psql": DJANGO_POSTGRES,
    "pgsql": DJANGO_POSTGRES,
    "postgis": "django.contrib.gis.db.backends.postgis",
    "mysql": MYSQL_DRIVER,
    "mysql2": MYSQL_DRIVER,
    "mysql-connector": "mysql.connector.django",
    "mysqlgis": "django.contrib.gis.db.backends.mysql",
    "mssql": "sql_server.pyodbc",
    "oracle": "django.db.backends.oracle",
    "pyodbc": "sql_server.pyodbc",
    "redshift": "django_redshift_backend",
    "spatialite": "django.contrib.gis.db.backends.spatialite",
    "sqlite": "django.db.backends.sqlite3",
    "ldap": "ldapdb.backends.ldap",
}

DB_OPTIONS = [
    "CONN_MAX_AGE",
    "ATOMIC_REQUESTS",
    "AUTOCOMMIT",
    "SSLMODE",
    "SSLROOTCERT",
    "TEST",
    # extensions
    "READ_ONLY",
    "READONLY",
    "HTTP_METHODS",
    "HTTP_WRITE_PATHS",
    "HTTP_WRITE_STICKY",
]


def is_postgres(engine):
    return engine in (
        DJANGO_POSTGRES,
        "django.db.backends.postgresql_psycopg2",
        "django.contrib.gis.db.backends.postgis",
        "django_redshift_backend",
    )


def db_scheme_handler(config: Dict, scheme: str, backend: Optional[AnyStr] = None):
    if scheme == "sqlite":
        config["NAME"] = config.pop("HOST", None) or config.get("NAME") or ":memory:"
    if backend:
        config["ENGINE"] = backend
    elif scheme in DB_ENGINES:
        config["ENGINE"] = DB_ENGINES[scheme]
    else:
        raise ValueError(f"Unsupported database scheme: {scheme}")
    return config


def db_options_handler(config: Dict, qs: str) -> Dict:
    opts = dict(parse_qs(qs).items()) if qs else {}
    db_opts = {
        key: values[0] for key, values in opts.items() if key.upper() not in DB_OPTIONS
    }
    config |= {k: values[0] for k, values in opts.items() if k.upper() in DB_OPTIONS}
    if "currentSchema" in db_opts:
        schema = db_opts.pop("currentSchema")
        if is_postgres(config["ENGINE"]):
            db_opts["options"] = f"-c search_path={schema}"
    config["OPTIONS"] = db_opts
    return config


def parse_db_url(raw_url: AnyStr, backend: Optional[AnyStr] = None):
    return parse_url(raw_url, backend, db_scheme_handler, db_options_handler)
