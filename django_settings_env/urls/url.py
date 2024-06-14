from typing import Dict, AnyStr, Optional, Callable, Any
from urllib.parse import ParseResult, urlparse

__all__ = (
    "ConfigDict",
    "url_to_dict",
    "dict_to_url",
    "parse_url",
    "parse_url_as_url",
    "is_true",
)

_BOOLEAN_TRUE_STRINGS = ("T", "t", "1", "on", "ok", "Y", "y", "en")
_BOOLEAN_TRUE_BYTES = (b"T", b"t", b"1", b"on", b"ok", b"Y", b"y", b"en")


def remove_items(d: dict, *keys):
    for key in keys:
        d.pop(key, None)
    return d


def true_values(val: AnyStr) -> tuple:
    return _BOOLEAN_TRUE_BYTES if isinstance(val, bytes) else _BOOLEAN_TRUE_STRINGS


def is_true(val: Any | None):
    if val in [None, False, "", b"", 0, "0", b"0"]:
        return False
    if not isinstance(val, (str, bytes)):
        return bool(val)
    true_vals = true_values(val)
    return bool(val and any(val.startswith(v) for v in true_vals))


class ConfigDict(dict):
    def __filter_none(self, d: Dict) -> Dict:
        return {k: v for k, v in d.items() if v is not None}

    def __init__(self, *args, scheme=None, **kwargs):
        if args:
            if isinstance(args[0], ConfigDict) and scheme is None:
                scheme = args[0].scheme
            elif isinstance(args[0], dict):
                args = (self.__filter_none(args[0]),)
        filtered_kwargs = {k: v for k, v in kwargs.items() if v is not None}
        super().__init__(*args, **filtered_kwargs)
        self._scheme = scheme

    @property
    def scheme(self):
        return self._scheme

    @scheme.setter
    def scheme(self, value):
        self._scheme = value


def url_to_dict(parsed_url: ParseResult, leadingSlash: bool = False) -> ConfigDict:
    """
    Convert a parsed URL into a dictionary with the keys renamed according to the given attribute map.
    :param parsed_url: This is a parsed URL (from urlparse)
    :return: a mapping of the parsed URL as a dict
    """

    def port():
        try:
            return str(parsed_url.port) if parsed_url.port else None
        except ValueError:
            return None

    def path():
        return (
            parsed_url.path[1:]
            if not leadingSlash and parsed_url.path.startswith("/")
            else parsed_url.path or None
        )

    def host():
        if parsed_url.netloc.startswith(":"):
            return parsed_url.netloc
        return parsed_url.hostname or None

    scheme = parsed_url.scheme or "unknown"
    d = {
        "USER": parsed_url.username,
        "PASSWORD": parsed_url.password,
        "HOST": host(),
        "PORT": port(),
        "NAME": path(),
    }
    return ConfigDict(**d, scheme=scheme)


_DEFAULT_SCHEME = "unknown"


def dict_to_url(config: Dict, scheme: str = _DEFAULT_SCHEME) -> str:
    """
    Convert a dictionary into a URL string.
    :param config: This is a dictionary of the URL
    :param scheme: Override the scheme of the URL
    :return: a URL string
    """

    def get_scheme() -> Optional[str]:
        """Extract the scheme from the given config."""
        if scheme and scheme != _DEFAULT_SCHEME:
            return scheme
        return config.scheme if isinstance(config, ConfigDict) else None

    def get_user_password() -> str:
        """Construct user-password part of url."""
        user, password = config.get("USER"), config.get("PASSWORD")
        if user and password:
            return f"{user}:{password}@"
        elif user:
            return f"{user}@"
        else:
            return ""

    scheme = get_scheme()
    prefix = f"{scheme}://" if scheme else ""

    user_password = get_user_password()
    host, port, name = config.get("HOST", ""), config.get("PORT"), config.get("NAME")

    port = f":{port}" if port else ""
    name = f"/{name}" if name else ""

    return f"{prefix}{user_password}{host}{port}{name}"


def parse_url(
    raw_url: AnyStr,
    backend: Optional[AnyStr] = None,
    scheme_handler: Optional[Callable[[Dict, str], Dict]] = None,
    options_handler: Optional[Callable[[Dict, str], Dict]] = None,
) -> ConfigDict:
    if "," in raw_url:
        configs = [
            parse_url(v, backend, scheme_handler, options_handler)
            for v in raw_url.split(",")
        ]
        scheme = None
        backend_key = "BACKEND"
        # ENGINE or BACKEND is common and applies to all URLs
        urls = []
        # when handling multple URLs, we need to ensure that the backend and scheme apply at the top level only
        # remove BACKEND or ENGINE from config and place it at the global level
        for config in configs:
            if not scheme:
                scheme = config.scheme
            if "ENGINE" in config:
                backend_key = "ENGINE"
            if config.get(backend_key):
                if not backend:
                    backend = config.get(backend_key)
                del config[backend_key]
            urls.append(dict_to_url(config))
        return ConfigDict(scheme=scheme, backend_key=backend, LOCATION=urls)

    parsed_url: ParseResult = urlparse(raw_url)

    config = url_to_dict(parsed_url)
    config = scheme_handler(config, config.scheme) if scheme_handler else config
    config = options_handler(config, parsed_url.query) if options_handler else config

    return config


def parse_url_as_url(
    raw_url: AnyStr,
    backend: Optional[AnyStr] = None,
    scheme_handler: Optional[Callable[[Dict, str], Dict]] = None,
    options_handler: Optional[Callable[[Dict, str], Dict]] = None,
) -> str:
    config = parse_url(raw_url, backend, scheme_handler, options_handler)
    return dict_to_url(config)
