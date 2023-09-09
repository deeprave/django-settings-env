# -*- coding: utf-8 -*-
"""
Wrapper around os.environ with django config value parsers
"""
from urllib.parse import parse_qs, unquote_plus, urlparse, urlunparse

from django.core.exceptions import ImproperlyConfigured
from django.utils.encoding import smart_str
from envex import Env

DEFAULT_DATABASE_ENV = "DATABASE_URL"
DJANGO_POSTGRES = "django.db.backends.postgresql"
MYSQL_DRIVER = "django.db.backends.mysql"
DB_SCHEMES = {
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
_DB_BASE_OPTIONS = [
    "CONN_MAX_AGE",
    "ATOMIC_REQUESTS",
    "AUTOCOMMIT",
    "SSLMODE",
    "TEST",
    # extensions
    "READ_ONLY",
    "READONLY",
    "HTTP_METHODS",
    "HTTP_WRITE_PATHS",
    "HTTP_WRITE_STICKY",
]

DEFAULT_CACHE_ENV = "CACHE_URL"
REDIS_CACHE = "django_redis.cache.RedisCache"
CACHE_SCHEMES = {
    "dbcache": "django.core.cache.backends.db.DatabaseCache",
    "dummycache": "django.core.cache.backends.dummy.DummyCache",
    "filecache": "django.core.cache.backends.filebased.FileBasedCache",
    "locmemcache": "django.core.cache.backends.locmem.LocMemCache",
    "memcache": "django.core.cache.backends.memcached.MemcachedCache",
    "pymemcache": "django.core.cache.backends.memcached.PyLibMCCache",
    "rediscache": REDIS_CACHE,
    "redis": REDIS_CACHE,
}
_CACHE_BASE_OPTIONS = ["TIMEOUT", "KEY_PREFIX", "VERSION", "KEY_FUNCTION", "BINARY"]

DEFAULT_EMAIL_ENV = "EMAIL_URL"
EMAIL_AMAZON_SES = "django_ses.SESBackend"
EMAIL_SMTP = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_SCHEMES = {
    "smtp": EMAIL_SMTP,
    "smtps": EMAIL_SMTP,
    "smtp+tls": EMAIL_SMTP,
    "smtp+ssl": EMAIL_SMTP,
    "consolemail": "django.core.mail.backends.console.EmailBackend",
    "filemail": "django.core.mail.backends.filebased.EmailBackend",
    "memorymail": "django.core.mail.backends.locmem.EmailBackend",
    "dummymail": "django.core.mail.backends.dummy.EmailBackend",
    "amazonses": EMAIL_AMAZON_SES,
    "amazon-ses": EMAIL_AMAZON_SES,
}
_EMAIL_BASE_OPTIONS = ["EMAIL_USE_TLS", "EMAIL_USE_SSL"]

DEFAULT_SEARCH_ENV = "SEARCH_URL"
SEARCH_SCHEMES = {
    "elasticsearch": "haystack.backends.elasticsearch_backend.ElasticsearchSearchEngine",
    "elasticsearch2": "haystack.backends.elasticsearch2_backend.Elasticsearch2SearchEngine",
    "solr": "haystack.backends.solr_backend.SolrEngine",
    "whoosh": "haystack.backends.whoosh_backend.WhooshEngine",
    "xapian": "haystack.backends.xapian_backend.XapianEngine",
    "simple": "haystack.backends.simple_backend.SimpleEngine",
}

DEFAULT_QUEUE_ENV = "QUEUE_URL"
QUEUE_SCHEMES = {
    "rabbitmq": {
        "backend": "mq.backends.rabbitmq_backend.create_backend",
        "default-port": 5672,
    },
    "redis": {"backend": REDIS_CACHE, "default-port": 6379},
    "amazonsqs": {
        "backend": "mq.backends.sqs_backend.create_backend",
    },
    "amazon-sqs": {
        "backend": "mq.backends.sqs_backend.create_backend",
    },
}
_QUEUE_BASE_OPTIONS = []
_DEFAULT_ENV_PREFIX = "DJANGO_"
_DEFAULT_PREFIX = object()


class DjangoEnv(Env):
    """
    Wrapper around os.environ with .env enhancement django, and Hashicorp vault support
    """

    def __init__(self, *args, **kwargs):
        """
        @param args: dict (optional) environment variables
        @param prefix: (optional) str prefix to add to all variables (default=DJANGO_)
        @param exception: (optional) Exception class to raise on error (default=KeyError)
        @param environ: dict | None default base environment (os.environ is default)
        @param readenv: read values from .env files (default=**True**)
        - if readenv=True, the following additional args may be used
        @param env_file: str name of the environment file (.env or $ENV default)
        @param search_path: None | Union[List[str], List[Path]], str] path(s) to search for env_file
        @param overwrite: bool whether to overwrite existing environment variables (default=False)
        @param parents: bool whether to search parent directories for env_file (default=**True**)
        @param update: bool whether to update os.environ with values from env_file (default=False)
        @param errors: bool whether to raise error on missing env_file (default=False)
        - kwargs for vault/secrets manager:
        @param url: (optional) vault url, default is $VAULT_ADDR
        @param token: (optional) vault token, default is $VAULT_TOKEN or ~/.vault-token
        @param cert: (optional) tuple (cert, key) or str path to client cert/key files
        @param verify: (optional) bool | str whether to verify server cert or set ca cert path (default=True)
        @param cache_enabled: (optional) bool whether to cache secrets (default=True)
        @param base_path: (optional) str base path for secrets (default=None)
        @param engine: (optional) str vault secrets engine (default=None)
        @param mount_point: (optional) str vault secrets mount point (default=None, determined by engine)
        @param working_dirs: (optional) bool whether to include PWD/CWD (default=True)
        -
        @param kwargs: (optional) environment variables to add/override
        """
        self.prefix = kwargs.pop("prefix", _DEFAULT_ENV_PREFIX)
        # by default, use Django config exception in preference to KeyError
        kwargs.setdefault("exception", ImproperlyConfigured)
        # change default to read .env files and search parents as well
        kwargs.setdefault("readenv", True)
        kwargs.setdefault("parents", True)
        super().__init__(*args, **kwargs)

    def _with_prefix(self, var, prefix):
        if prefix is _DEFAULT_PREFIX:
            prefix = self.prefix
        if var and prefix and not var.startswith(prefix) and not self.is_set(var):
            var = f"{prefix}{var}"
        return var

    def get(self, var, default=None, prefix=_DEFAULT_PREFIX):
        return super().get(self._with_prefix(var, prefix=prefix), default)

    def int(self, var, default=None, prefix=_DEFAULT_PREFIX) -> int:
        val = self.get(var, default, prefix=prefix)
        return self._int(val)

    def float(self, var, default=None, prefix=_DEFAULT_PREFIX) -> float:
        val = self.get(var, default, prefix=prefix)
        return self._float(val)

    def bool(self, var, default=None, prefix=_DEFAULT_PREFIX) -> bool:
        val = self.get(var, default, prefix=prefix)
        return val if isinstance(val, (bool, int)) else self.is_true(val)

    def list(self, var, default=None, prefix=_DEFAULT_PREFIX) -> list:
        val = self.get(var, default, prefix=prefix)
        return val if isinstance(val, (list, tuple)) else self._list(val)

    def check_var(self, var, default=None, prefix=_DEFAULT_PREFIX, raise_error=True):
        """
        override to insert prefix unless the raw var is set
        """
        var = self._with_prefix(var, prefix=prefix)
        return super().check_var(var, default=default, raise_error=raise_error)

    django_env_typemap = {
        "int": int,
        "bool": bool,
        "float": float,
        "list": list,
    }

    # noinspection PyShadowingBuiltins
    def __call__(self, var=None, default=None, **kwargs):
        prefix = kwargs.pop("prefix", _DEFAULT_PREFIX)
        # This is tied to django-class-settings (optional dependency), which allows
        # omitting the 'name' parameter and using the setting name instead
        if var is None:
            kwds = {
                "name": var,
                "prefix": prefix if prefix is None else self.prefix,
                "default": default,
            }
            # try using class_settings version if installed
            try:
                # noinspection PyUnresolvedReferences
                from class_settings.env import DeferredEnv

                return DeferredEnv(self, kwargs=kwds, optional=kwargs.get("optional", False))
            except ImportError:
                pass
            # otherwise, use our own implementation (handles module level vars)
            from .deferred import DeferredSetting

            # class settings not installed
            return DeferredSetting(env=self, kwargs=kwds)

        # set to the provided default if not already set
        if default is not None and not self.is_set(var):
            self.set(var, default)
        # resolve entry point by the type
        try:
            _type = kwargs.pop("type", "str")
            _type = _type if isinstance(_type, str) else _type.__name__
            return self.django_env_typemap[_type](self, var, default=default, prefix=prefix)
        except KeyError:
            pass
        return self.get(var, default=default, prefix=prefix)

    # Django-specific additions

    def database_url(self, var=DEFAULT_DATABASE_ENV, *, default=None, engine=None, options=None):
        """
        Parse the url, mostly based on dj-database-url

        :param var: Variable to use
        :param default: default value if var is unset
        :param engine: override database engine
        :param options: additional database options
        :return: dictionary of database options
        """
        url = self.check_var(var, default=default)
        # shortcut to avoid urlparse
        if url == "sqlite://:memory":
            return {"ENGINE": DB_SCHEMES["sqlite"], "NAME": ":memory:"}

        # otherwise, parse the url as normal
        config = {}
        url = urlparse(url)

        path = smart_str(url.path[1:])
        path = unquote_plus(path.split("?", 2)[0])

        if url.scheme == "sqlite" and path == "":
            path = ":memory:"
        elif url.scheme == "ldap":
            path = f"{url.scheme}://{url.hostname}"
            if url.port:
                path += f":{url.port}"

        # Handle postgres percent-encoded paths.
        hostname = url.hostname or ""
        if "%2f" in hostname.lower():
            # Switch to url.netloc to avoid lower cased paths
            hostname = url.netloc
            if "@" in hostname:
                hostname = hostname.rsplit("@", 1)[1]
            if ":" in hostname:
                hostname = hostname.split(":", 1)[0]
            hostname = hostname.replace("%2f", "/").replace("%2F", "/")

        engine = DB_SCHEMES[url.scheme] if engine is None else engine
        port = str(url.port) if url.port and engine == DB_SCHEMES["oracle"] else url.port

        # Update with configuration.
        config.update(
            {
                "NAME": path or "",
                "USER": url.username or "",
                "PASSWORD": url.password or "",
                "HOST": hostname,
                "PORT": port or "",
            }
        )

        if url.scheme == "postgres" and path.startswith("/"):
            config["HOST"], config["NAME"] = path.rsplit("/", 1)

        elif url.scheme == "oracle":
            if path == "":
                config["NAME"], config["HOST"] = config["HOST"], ""
            if not config["PORT"]:  # Django oracle/base.py strips port and fails on non-string value
                del config["PORT"]
            else:
                config["PORT"] = str(config["PORT"])

        db_options = {}
        # Pass the query string into OPTIONS.
        if url.query:
            for key, values in parse_qs(url.query).items():
                if key.upper() in _DB_BASE_OPTIONS:
                    config.update({key.upper(): values[0]})
                else:
                    db_options.update({key: self._int(values[0])})

            # Support for Postgres Schema URLs
            if "currentSchema" in db_options and engine in (
                "django.contrib.gis.db.backends.postgis",
                "django.db.backends.postgresql_psycopg2",
                "django_redshift_backend",
            ):
                db_options["options"] = "-c search_path={0}".format(db_options.pop("currentSchema"))

        if options:
            for key, value in options.items():
                if key.upper() in _DB_BASE_OPTIONS:
                    config.update({key.upper(): value})
                else:
                    db_options.update({key: value})
        if db_options:
            config["OPTIONS"] = {k.upper(): v for k, v in db_options.items()}
        if engine:
            config["ENGINE"] = engine
        return config

    def cache_url(self, var=DEFAULT_CACHE_ENV, *, default=None, backend=None, options=None):
        """based on dj-cache-url

        :param var: variable to use
        :param default: default variable
        :param backend: override parsed backend
        :param options: additional options
        :return: dictionary of cache parameters
        """
        url = urlparse(self.check_var(var, default=default))

        location = url.netloc.split(",")
        if len(location) == 1:
            location = location[0]

        config = {
            "BACKEND": backend if backend else CACHE_SCHEMES[url.scheme],
            "LOCATION": location,
        }

        # Add the drive to LOCATION
        if url.scheme == "filecache":
            config.update(
                {
                    "LOCATION": url.netloc + url.path,
                }
            )

        if url.path and url.scheme in ["unix", "memcache", "pymemcache"]:
            config.update(
                {
                    "LOCATION": f"unix:{url.path}",
                }
            )
        elif url.scheme.startswith("redis"):
            scheme = url.scheme.replace("cache", "") if url.hostname else "unix"
            locations = [f"{scheme}://{smart_str(loc)}{url.path}" for loc in url.netloc.split(",")]
            config["LOCATION"] = locations[0] if len(locations) == 1 else locations

        cache_options = {}
        if url.query:
            for key, values in parse_qs(url.query).items():
                opt = {smart_str(key).upper(): smart_str(values[0], strings_only=True)}
                if key.upper() in _CACHE_BASE_OPTIONS:
                    config.update(opt)
                else:
                    cache_options.update(opt)

        if options:
            cache_options.update({k.upper(): v for k, v in options.items()})
        config["OPTIONS"] = cache_options
        return config

    def email_url(self, var=DEFAULT_EMAIL_ENV, *, default=None, backend=None, options=None):
        """parse an email URL, based on django-environ
        :param var: environment variable to use
        :param default: default value if var is unset
        :param backend: override parsed email backend
        :param options: specify email options (as dict)
        :return: dictionary of email variables
        """
        url = urlparse(self.check_var(var, default=default))

        path = smart_str(url.path[1:])
        path = unquote_plus(path.split("?", 2)[0])

        # Update with environment configuration
        config = {
            "EMAIL_FILE_PATH": path,
            "EMAIL_HOST_USER": url.username,
            "EMAIL_HOST_PASSWORD": url.password,
            "EMAIL_HOST": url.hostname,
            "EMAIL_PORT": self._int(url.port),
        }

        if backend:
            config["EMAIL_BACKEND"] = backend
        elif url.scheme in EMAIL_SCHEMES:
            config["EMAIL_BACKEND"] = EMAIL_SCHEMES[url.scheme]
        else:
            raise self.exception("Invalid email schema %s" % url.scheme)

        if url.scheme in ("smtps", "smtp+tls"):
            config["EMAIL_USE_TLS"] = True
        elif url.scheme == "smtp+ssl":
            config["EMAIL_USE_SSL"] = True

        email_options = {}
        if url.query:
            for key, values in parse_qs(url.query).items():
                opt = {smart_str(key).upper(): self._int(values[0])}
                if key.upper() in _EMAIL_BASE_OPTIONS:
                    config.update(opt)
                else:
                    email_options.update(opt)

        if options:
            email_options.update(options)
        if email_options:
            config["OPTIONS"] = {k.upper(): v for k, v in email_options.items()}

        return config

    def search_url(self, var=DEFAULT_SEARCH_ENV, *, default=None, engine=None, options=None):
        """parse a search URL from environment, based on django-environ
        :param var: environment variable to use
        :param default: default value if var is unset
        :param engine: override parsed storage engine
        :param options: specify storage options (as dict)
        :return: dictionary of storage variables
        """
        url = urlparse(self.check_var(var, default=default))

        path = smart_str(url.path[1:])
        path = unquote_plus(path.split("?", 2)[0])

        if url.scheme not in SEARCH_SCHEMES:
            raise self.exception("Invalid search schema %s" % url.scheme)

        config = {"ENGINE": engine if engine else SEARCH_SCHEMES[url.scheme]}

        # check common params
        params = {}
        if url.query:
            params = {smart_str(k): smart_str(v, strings_only=True) for k, v in parse_qs(url.query)}
            if "EXCLUDED_INDEXES" in params.keys():
                config["EXCLUDED_INDEXES"] = params["EXCLUDED_INDEXES"][0].split(",")
            if "INCLUDE_SPELLING" in params.keys():
                config["INCLUDE_SPELLING"] = self.is_true(params["INCLUDE_SPELLING"][0])
            if "BATCH_SIZE" in params.keys():
                config["BATCH_SIZE"] = self._int(params["BATCH_SIZE"][0])

        if url.scheme == "simple":
            return config
        elif url.scheme in ["solr", "elasticsearch", "elasticsearch2"]:
            if "KWARGS" in params.keys():
                config["KWARGS"] = params["KWARGS"][0]

        # remove trailing slash
        if path.endswith("/"):
            path = path[:-1]

        if url.scheme == "solr":
            config["URL"] = urlunparse(("http",) + url[1:2] + (path,) + ("", "", ""))
            if "TIMEOUT" in params.keys():
                config["TIMEOUT"] = self._int(params["TIMEOUT"][0])
            return config

        if url.scheme.startswith("elasticsearch"):
            split = path.rsplit("/", 1)

            if len(split) > 1:
                path = "/".join(split[:-1])
                index = split[-1]
            else:
                path = ""
                index = split[0]

            config["URL"] = urlunparse(("http",) + url[1:2] + (path,) + ("", "", ""))
            if "TIMEOUT" in params.keys():
                config["TIMEOUT"] = self._int(params["TIMEOUT"][0])
            config["INDEX_NAME"] = index
        else:
            config["PATH"] = "/" + path

            if url.scheme == "whoosh":
                if "STORAGE" in params.keys():
                    config["STORAGE"] = params["STORAGE"][0]
                if "POST_LIMIT" in params.keys():
                    config["POST_LIMIT"] = self._int(params["POST_LIMIT"][0])
            elif url.scheme == "xapian":
                if "FLAGS" in params.keys():
                    config["FLAGS"] = params["FLAGS"][0]

        if options:
            config.update({k.upper(): v for k, v in options.items()})

        return config

    def queue_url(self, var=DEFAULT_QUEUE_ENV, *, default=None, backend=None, options=None):
        """
        Parse a url, mostly based on dj-database-url
        :param var: environment variable to use
        :param default: default value if var is unset
        :param backend: override parsed backend
        :param options: specify queue options (as dict)
        :return: dictionary of queue variables
        """
        url = self.check_var(var, default=default)

        # otherwise, parse the url as normal
        url = urlparse(url)

        path = smart_str(url.path[1:])
        path = unquote_plus(path.split("?", 2)[0])

        conf = QUEUE_SCHEMES.get(url.scheme, {})
        port = int(url.port) if url.port else conf.get("default-port", None)

        config = {"QUEUE_BACKEND": backend if backend is None else conf["backend"]}

        if url.scheme.startswith("amazon"):
            path = f"https://{url.hostname}"
            if port:
                path += f":{port}"
            config.update({"AWS_SQS_ENDPOINT": path})

        elif url.scheme.startswith("rabbit"):
            config = {
                "QUEUE_BACKEND": backend or config["QUEUE_BACKEND"],
                "RABBITMQ_HOST": url.hostname or "",
                "RABBITMQ_PORT": port,
            }
            if not url.hostname:
                config.update(
                    {
                        "QUEUE_LOCATION": f"unix://{url.netloc}{url.path}",
                        "RABBITMQ_LOCATION": f"unix://{url.netloc}{url.path}",
                        "RABBITMQ_PORT": "",
                    }
                )

        elif url.scheme == "redis":
            scheme = url.scheme if url.hostname else "unix"
            locations = [f"{scheme}://{loc}{url.path}" for loc in url.netloc.split(",")]
            if not backend:
                config.update({"QUEUE_LOCATION": locations[0] if len(locations) == 1 else locations})

        else:
            config.update({"PATH": path or "", "HOST": url.hostname, "PORT": port or ""})

        if url.username:
            config.update(
                {
                    "USER": url.username or "",
                    "PASSWORD": url.password or "",
                }
            )

        queue_options = {}
        if url.query:
            for key, values in parse_qs(url.query).items():
                opt = {smart_str(key).upper(): smart_str(values[0], strings_only=True)}
                if key.upper() in _QUEUE_BASE_OPTIONS:
                    config.update(opt)
                else:
                    queue_options.update(opt)

        if options:
            queue_options.update(options)
        if queue_options:
            config["OPTIONS"] = {k.upper(): v for k, v in queue_options.items()}

        # return configuration.
        return config
