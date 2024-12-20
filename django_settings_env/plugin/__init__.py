import contextlib
from abc import ABC, abstractmethod
from typing import Dict, Type, Any
import threading

__all__ = ("EnvPlugin", "ConfigDict", "register_plugin")

from ..parser import ParsedUrl, default_parser


class ConfigDict(dict):
    def __setitem__(self, key, value):
        if value:
            super().__setitem__(key, value)
        elif key in self:
            super().__delitem__(key)

    def update(self, *args, **kwargs):
        for key, value in dict(*args, **kwargs).items():
            self[key] = value
        return self


def is_int(value: Any) -> bool:
    if value:
        if not isinstance(value, str):
            value = str(value)
        with contextlib.suppress(ValueError):
            int(value)
            return True
    return False


def is_float(value: Any) -> bool:
    if value:
        if not isinstance(value, str):
            value = str(value)
        with contextlib.suppress(ValueError):
            float(value)
            return True
    return False


def is_true(value: Any) -> bool:
    if not value:
        return False
    if isinstance(value, str):
        value = value.lower()
        return any(value.startswith(x) for x in ("tr", "ye", "1", "en"))
    return bool(value)


def convert_values(options: dict):
    # convert numerical values to numbers or booleans
    for k, v in options.items():
        if is_int(v):
            options[k] = int(v)
        elif is_float(v):
            options[k] = float(v)


class EnvPlugin(ABC):
    DEFAULT_SCHEME = "https"

    @property
    def parser(self):
        return default_parser

    def parse_url(self, url: str, **kwargs) -> ParsedUrl:
        return self.parser(url, **kwargs)

    @abstractmethod
    def get_backend(self, url: str, **kwargs) -> object:
        # Return a Django object or dictionary
        pass


_initialized = False
_registered_plugins: Dict = {}
_registered_plugins_lock = threading.Lock()


def _register_plugin(plugin_cls: type[EnvPlugin], name: str):
    if not issubclass(plugin_cls, EnvPlugin):
        raise TypeError(f"{plugin_cls.__name__} must implement EnvPlugin")
    with _registered_plugins_lock:
        global _initialized
        _registered_plugins[name] = plugin_cls()
        _initialized = True


def register_plugin(name: str):
    """
    Class decorator to automatically register a plugin subclass in the plugin registry.

    Args:
        name: DjangoEnv method name to handle

    Raises:
        TypeError: If the decorated class doesn't implement the EnvPlugin protocol.
    """

    def decorator(plugin_cls: Type[EnvPlugin] | str):
        _register_plugin(plugin_cls, name)
        return plugin_cls

    return decorator  # Return the parser class itself


def get_plugin_from_name(name: str) -> EnvPlugin:
    with _registered_plugins_lock:
        return _registered_plugins.get(name)
