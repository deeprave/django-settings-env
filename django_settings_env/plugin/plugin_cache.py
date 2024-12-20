from django.utils.version import get_complete_version

from . import EnvPlugin, ConfigDict, register_plugin, convert_values

DJANGO_VERSION = get_complete_version()

REDIS_CACHE_BACKEND = "django_redis.cache.RedisCache"
DJANGO_REDIS_CACHE_BACKEND = "django.core.cache.backends.redis.RedisCache"
DJANGO_LOCMEM_CACHE_BACKEND = "django.core.cache.backends.locmem.LocMemCache"
CACHE_SCHEMES = {
    "dbcache": "django.core.cache.backends.db.DatabaseCache",
    "dummycache": "django.core.cache.backends.dummy.DummyCache",
    "filecache": "django.core.cache.backends.filebased.FileBasedCache",
    "locmem": DJANGO_LOCMEM_CACHE_BACKEND,
    "locmemcache": DJANGO_LOCMEM_CACHE_BACKEND,
    "memcache": "django.core.cache.backends.memcached.MemcachedCache",
    "pymemcache": "django.core.cache.backends.memcached.PyLibMCCache",
    "rediscache": REDIS_CACHE_BACKEND
    if DJANGO_VERSION[0] < 4
    else DJANGO_REDIS_CACHE_BACKEND,
    "redis": REDIS_CACHE_BACKEND if DJANGO_VERSION[0] < 4 else DJANGO_REDIS_CACHE_BACKEND,
    "rediss": REDIS_CACHE_BACKEND
    if DJANGO_VERSION[0] < 4
    else DJANGO_REDIS_CACHE_BACKEND,
}


@register_plugin("cache_url")
class CachePlugin(EnvPlugin):
    """
    Plugin for handling database configuration
    """

    VAR = "CACHE_URL"
    CONTEXTS = ["caches"]

    def get_backend(self, url: str, **kwargs) -> object:  # noqa: C901
        parsed = self.parse_url(url, context=self.CONTEXTS)
        backend = kwargs.get("backend", None)
        options = kwargs.get("options", {})
        config = ConfigDict()

        if not parsed.scheme:
            raise ValueError("Missing cache scheme or url parse error")
        try:
            config["BACKEND"] = backend or CACHE_SCHEMES[parsed.scheme]
        except KeyError as e:
            raise ValueError(f"Unknown cache scheme: {parsed.scheme}") from e

        host = parsed.hostname
        name = parsed.path
        match parsed.scheme:
            case "filecache":
                config["LOCATION"] = f"{host}{name}"
            case "redis" | "rediscache" | "pymemcache":
                # note: SSL is not supported for unix domain sockets, so "rediss" is not here
                if parsed.hostname == "unix":
                    path = name or "/tmp/redis.sock"
                    config["LOCATION"] = f"unix://{path}"
                else:
                    config["LOCATION"] = parsed.to_url()
            case "dummycache":
                config["LOCATION"] = config["NAME"] = None
            case "dbcache":
                config["LOCATION"] = parsed.path[1:] if parsed.path else ""
            case "memcache":
                config["LOCATION"] = parsed.to_url(scheme=None)
            case _:
                config["LOCATION"] = parsed.to_url()
        if parsed.qs:
            options.update(parsed.qs)
        convert_values(options)
        if options:
            config["OPTIONS"] = options
        # special handling of these
        config["TIMEOUT"] = options.pop("timeout", None)
        config["KEY_PREFIX"] = options.pop("key_prefix", None)
        return config
