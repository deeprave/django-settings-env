# -*- coding: utf-8 -*-
from functools import wraps

from django.conf import LazySettings


class MyLazySettings(LazySettings):
    def __getattribute__(self, name):
        return LazySettings.__getattribute__(self, name)


def deferred_handler():
    # at least one DeferredSetting is being used, so override the __getattr__ handler for the setting module
    # to catch any DeferredSetting use and return an appropriate value from the environment
    if not getattr(deferred_handler, "enabled", False):
        # need to overrite both because __getattr__ is not called if the setting is defined (no longer lazy)
        LazySettings.__getattr__ = deferred_getattr(LazySettings.__getattr__)
        LazySettings.__getattribute__ = deferred_getattribute(LazySettings.__getattribute__)
        deferred_handler.enabled = True


class DeferredSetting:
    # similar to django-class-settings DeferredEnv but simpler
    # and handles settings at module level not in a Settings class

    def __init__(self, env, *, kwargs):
        self._env, self._kwargs = env, kwargs
        deferred_handler()

    def setting(self, name):
        kwargs = self._kwargs.copy()
        name_kwarg = kwargs.pop("name")
        name = name_kwarg if name_kwarg is not None else name
        return self._env.get(name, **kwargs)


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
    @wraps(deferred_getattr)
    def wrapper(self, name):
        return cache_setting(self, name, func(self, name))

    return wrapper


def deferred_getattribute(func):
    @wraps(deferred_getattribute)
    def wrapper(self, name):
        return cache_setting(self, name, func(self, name))

    return wrapper
