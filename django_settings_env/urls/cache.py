from typing import AnyStr, Optional, Dict
from urllib.parse import parse_qs

from .url import parse_url, dict_to_url, ConfigDict, remove_items
from django.utils.version import get_complete_version

DJANGO_VERSION = get_complete_version()

REDIS_CACHE = "django_redis.cache.RedisCache"
DJANGO_REDIS_CACHE = "django.core.cache.backends.redis.RedisCache"
CACHE_SCHEMES = {
    "dbcache": "django.core.cache.backends.db.DatabaseCache",
    "dummycache": "django.core.cache.backends.dummy.DummyCache",
    "filecache": "django.core.cache.backends.filebased.FileBasedCache",
    "locmemcache": "django.core.cache.backends.locmem.LocMemCache",
    "memcache": "django.core.cache.backends.memcached.MemcachedCache",
    "pymemcache": "django.core.cache.backends.memcached.PyLibMCCache",
    "rediscache": REDIS_CACHE if DJANGO_VERSION[0] < 4 else DJANGO_REDIS_CACHE,
    "redis": REDIS_CACHE if DJANGO_VERSION[0] < 4 else DJANGO_REDIS_CACHE,
    "rediss": REDIS_CACHE if DJANGO_VERSION[0] < 4 else DJANGO_REDIS_CACHE,
}


def cache_scheme_handler(config: Dict, scheme: str, backend: Optional[AnyStr] = None):
    if backend:
        config["BACKEND"] = backend
    elif scheme in CACHE_SCHEMES:
        config["BACKEND"] = CACHE_SCHEMES[scheme]
    else:
        raise ValueError(f"Unknown cache scheme: {scheme}")

    config = ConfigDict(config, scheme=scheme)

    match scheme:
        case "filecache":
            host, name = config.pop("HOST", ""), config.pop("NAME", "")
            location = (
                f"{host}/{name}"
                if host and name
                else host or name
                if name.startswith("/")
                else f"/{name}"
            )
            config["LOCATION"] = config.get("LOCATION", location)
        case "redis" | "rediscache" | "pymemcache":
            # note: SSL is not supported for unix domain sockets, so "rediss" is missing here
            if config.get("HOST") == "unix":
                config["LOCATION"] = (
                    f"{config.pop('HOST')}://{config.get('LOCATION', '/tmp/redis.sock')}"
                )
            else:
                config["LOCATION"] = dict_to_url(config)
        case "dummycache":
            config = remove_items(config, "LOCATION")
        case "dbcache":
            config["LOCATION"] = config["NAME"]  # will raise error here without name
        case "memcache":
            config["LOCATION"] = dict_to_url(dict(config))
        case _:
            config["LOCATION"] = dict_to_url(config)

    return remove_items(config, "HOST", "PORT", "NAME")


def cache_options_handler(config: Dict, qs: str) -> Dict:
    opts = dict(parse_qs(qs).items()) if qs else {}
    opts = {k: v[0] for k, v in opts.items()}
    if "db" in opts:
        config["LOCATION"] += f"?db={opts.pop('db')}"
    config["OPTIONS"] = config.get("OPTIONS", {}) | opts
    if not config["OPTIONS"]:
        del config["OPTIONS"]
    return config


def parse_cache_url(raw_url: AnyStr, backend: Optional[AnyStr] = None) -> Dict:
    return parse_url(raw_url, backend, cache_scheme_handler, cache_options_handler)
