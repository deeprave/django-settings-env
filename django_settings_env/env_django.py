# -*- coding: utf-8 -*-
"""
Wrapper around os.environ with django config value parsers
"""

import contextlib
import inspect

from django.core.exceptions import ImproperlyConfigured
from envex import Env

DEFAULT_DATABASE_ENV = "DATABASE_URL"
DEFAULT_CACHE_ENV = "CACHE_URL"
DEFAULT_EMAIL_ENV = "EMAIL_URL"
DEFAULT_SEARCH_ENV = "SEARCH_URL"
DEFAULT_QUEUE_ENV = "QUEUE_URL"

_DEFAULT_PREFIX = "DJANGO_"
_USE_DEFAULT_PREFIX = object()


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
        @param readenv: bool If True, values will be read from .env files (default=**True**)
        - if True: the following additional args may be used
        @param env_file: str name of the environment file (.env or $ENV default)
        @param search_path: Union[List[str], List[Path]], str] path(s) to search for env_file
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
        @param timeout: (optional) int timeout for connecting to vault (default=5)
        @param working_dirs: (optional) bool whether to include PWD/CWD (default=True)
        -
        @param kwargs: (optional) environment variables to add/override
        """
        self.prefix = kwargs.pop("prefix", _DEFAULT_PREFIX)
        # by default, use Django config exception in preference to KeyError
        kwargs.setdefault("exception", ImproperlyConfigured)
        # change default to read .env files and search parents as well
        kwargs.setdefault("readenv", True)
        kwargs.setdefault("parents", True)
        super().__init__(*args, **kwargs)

    def _with_prefix(self, var, prefix):
        if prefix is _USE_DEFAULT_PREFIX:
            prefix = self.prefix
        if var and prefix and not var.startswith(prefix) and not self.is_set(var):
            var = f"{prefix}{var}"
        return var

    def get(self, var, default=None, prefix=_USE_DEFAULT_PREFIX):
        return super().get(self._with_prefix(var, prefix=prefix), default)

    def int(self, var, default=None, prefix=_USE_DEFAULT_PREFIX) -> int:
        val = self.get(var, default, prefix=prefix)
        return self._int(val)

    def float(self, var, default=None, prefix=_USE_DEFAULT_PREFIX) -> float:
        val = self.get(var, default, prefix=prefix)
        return self._float(val)

    def bool(self, var, default=None, prefix=_USE_DEFAULT_PREFIX) -> bool:
        val = self.get(var, default, prefix=prefix)
        return val if isinstance(val, (bool, int)) else self.is_true(val)

    def list(self, var, default=None, prefix=_USE_DEFAULT_PREFIX) -> list:
        val = self.get(var, default, prefix=prefix)
        return val if isinstance(val, (list, tuple)) else self._list(val)

    def check_var(self, var, default=None, prefix=_USE_DEFAULT_PREFIX, raise_error=True):
        """
        Override variable name to insert prefix unless the raw var is set
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
        prefix = kwargs.pop("prefix", _USE_DEFAULT_PREFIX)
        # This is tied to django-class-settings (optional dependency), which allows
        # omitting the 'name' parameter and using the setting name instead
        if var is None:
            _kwargs = {
                "name": var,
                "prefix": prefix if prefix is _USE_DEFAULT_PREFIX else self.prefix,
                "default": default,
            }
            # try using class_settings version if installed
            with contextlib.suppress(ImportError):
                # noinspection PyUnresolvedReferences
                from class_settings.env import DeferredEnv

                return DeferredEnv(
                    self, kwargs=_kwargs, optional=kwargs.get("optional", False)
                )
            # otherwise, use our own implementation (handles module level vars)
            from .deferred import DeferredSetting
            scope = inspect.currentframe().f_back

            # class settings not installed
            return DeferredSetting(env=self, scope=scope, kwargs=_kwargs)

        # set to the provided default if not already set
        if (
            default is not None
            and not self.is_set(var)
            and not self.is_set(self._with_prefix(var, prefix=prefix))
        ):
            self.set(var, default)
        # resolve entry point by the type
        with contextlib.suppress(KeyError):
            _type = kwargs.pop("type", "str")
            _type = _type if isinstance(_type, str) else _type.__name__
            return self.django_env_typemap[_type](
                self, var, default=default, prefix=prefix
            )
        return self.get(var, default=default, prefix=prefix)

    # Django-specific additions

    def database_url(
        self,
        var=DEFAULT_DATABASE_ENV,
        *,
        default=None,
        backend=None,
        prefix=_USE_DEFAULT_PREFIX,
    ):
        """
        Parse a database URL from the environment

        :param var: Variable to use
        :param default: str default value if var is unset
        :param backend: str|None override parsed email backend
        :param prefix: override the prefix to add to variable
        :return: dictionary of database options
        """
        from .urls import database

        raw_url = self.check_var(var, prefix=prefix, default=default)
        return database.parse_db_url(raw_url, backend=backend)

    def cache_url(
        self,
        var=DEFAULT_CACHE_ENV,
        *,
        default=None,
        backend=None,
        prefix=_USE_DEFAULT_PREFIX,
    ):
        """
        Parse a queue URL from the environment

        :param var: Variable to use
        :param default: str default value if var is unset
        :param backend: str|None override parsed email backend
        :param prefix: override the prefix to add to variable
        :return: dictionary of cache parameters
        """
        from .urls import cache

        raw_url = self.check_var(var, prefix=prefix, default=default)
        return cache.parse_cache_url(raw_url, backend=backend)

    def email_url(
        self,
        var=DEFAULT_EMAIL_ENV,
        *,
        default=None,
        backend=None,
        prefix=_USE_DEFAULT_PREFIX,
    ):
        """
        Parse an email URL from the environment

        :param var: Environment variable to use
        :param default: str default value if var is unset
        :param backend: str|None override parsed email backend
        :param prefix: override the prefix to add to variable
        :return: dictionary of email variables
        """
        from .urls import email

        raw_url = self.check_var(var, prefix=prefix, default=default)
        return email.parse_email_url(raw_url, backend=backend)

    def search_url(
        self,
        var=DEFAULT_SEARCH_ENV,
        *,
        default=None,
        backend=None,
        prefix=_USE_DEFAULT_PREFIX,
    ):
        """
        Parse a search URL from environment

        :param var: Environment variable to use
        :param default: str default value if var is unset
        :param backend: str|None override parsed email backend
        :param prefix: override the prefix to add to variable
        :return: dictionary of storage variables
        """
        from .urls import search

        raw_url = self.check_var(var, prefix=prefix, default=default)
        return search.parse_search_url(raw_url, backend=backend)
