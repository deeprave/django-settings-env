# -*- coding: utf-8 -*-


deferred_handler_enabled = False


def enable_deferred_handler():
    # at least one DeferredSetting is being used, so override the
    # __getattr__ handler for the setting module and catch any
    # DeferredSetting use and return an appropriate value from the environment
    global deferred_handler_enabled
    if not deferred_handler_enabled:  # only do this once
        from django.conf import LazySettings
        LazySettings.__getattr__ = deferred_settings_handler(LazySettings.__getattr__)
        deferred_handler_enabled = True


class DeferredSetting:
    # similar to django-class-settings DeferredEnv but simpler
    # and handles settings at module level not in a Settings class

    def __init__(self, env, *, kwargs):
        self._env, self._kwargs = env, kwargs
        enable_deferred_handler()

    def setting(self, name):
        kwargs = self._kwargs.copy()
        name_kwarg = kwargs.pop("name")
        name = name_kwarg if name_kwarg is not None else name
        return self._env.get(name, **kwargs)


def deferred_settings_handler(func):
        
    def wrapper(self, name):
        obj = func(self, name)
        return obj.setting(name) if isinstance(obj, DeferredSetting) else obj
    
    return wrapper
