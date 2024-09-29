# -*- coding: utf-8 -*-
from functools import wraps

from django.conf import LazySettings


def cache_setting(self, name, value):
    if isinstance(value, DeferredSetting):
        if not hasattr(cache_setting, "cache"):
            cache_setting.cache = {}
        cache = cache_setting.cache
        if name not in cache:
            cache[name] = value.setting(name)
        value = cache[name]
    return value


def deferred_getattr(func):
    # The @wraps decorator is used to preserve the original function's metadata
    @wraps(func)
    def wrapper(self, name):
        return cache_setting(self, name, func(self, name))

    return wrapper


def deferred_getattribute(func):
    @wraps(func)
    def wrapper(self, name):
        return cache_setting(self, name, func(self, name))

    return wrapper


def deferred_handler():
    # at least one DeferredSetting is being used, so override the __getattr__ handler for the setting module
    # to catch any DeferredSetting use and return an appropriate value from the environment
    if not getattr(deferred_handler, "__enabled__", False):
        # need to overwrite both because __getattr__ is not called if the setting is defined (no longer lazy)
        setattr(LazySettings, "__getattr__", deferred_getattr(LazySettings.__getattr__))
        setattr(
            LazySettings,
            "__getattribute__",
            deferred_getattribute(LazySettings.__getattribute__),
        )
        deferred_handler.__enabled__ = True


class DeferredSetting:
    # similar to django-class-settings DeferredEnv but simpler
    # and handles settings at module level not in a Settings class

    def __init__(self, env, *, scope, kwargs):
        self._name = kwargs.pop("name", None) or None
        self._env, self._scope, self._kwargs = env, scope, kwargs
        deferred_handler()

    def __get_variable_name(self, name):
        name = self._name or name
        if name is None:
            names = [n for n, v in self._scope.f_locals.items() if v is self]
            name = names[0] if names else None
        return name

    def setting(self, name):
        name = self.__get_variable_name(name)
        return self._env.get(name, **self._kwargs) if name else ""

    def __repr__(self):
        return self.setting(self._name) or ""
