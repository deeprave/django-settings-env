from . import EnvPlugin, ConfigDict, register_plugin, convert_values

REDIS_QUEUE_BACKEND = "django_redis.cache.RedisCache"
QUEUE_SCHEMES = {
    "pymemqueue": "django.core.cache.backends.memcached.PyLibMCCache",
    "redisqueue": REDIS_QUEUE_BACKEND,
    "redis+socket": REDIS_QUEUE_BACKEND,
    "redis": REDIS_QUEUE_BACKEND,
    "rediss": REDIS_QUEUE_BACKEND,
}


@register_plugin("queue_url")
class QueuePlugin(EnvPlugin):
    """
    Plugin for handling queue configuration
    """

    VAR = "QUEUE_URL"
    CONTEXTS = ["queues"]

    def get_backend(self, url: str, **kwargs) -> object:  # noqa: C901
        parsed = self.parse_url(url, context=self.CONTEXTS)
        backend = kwargs.get("backend", None)
        options = kwargs.get("options", {})
        config = ConfigDict()

        if not parsed.scheme:
            raise ValueError("Missing queue scheme or url parse error")
        try:
            config["BACKEND"] = backend or QUEUE_SCHEMES[parsed.scheme]
        except KeyError as e:
            valid_schemes = ", ".join(sorted(QUEUE_SCHEMES.keys()))
            raise ValueError(
                f"Unknown queue scheme: {parsed.scheme}. Supported schemes are: {valid_schemes}"
            ) from e

        name = parsed.path
        match parsed.scheme:
            case "redis" | "redisqueue" | "pymemqueue" | "redis+socket" | "rediss":
                # note: SSL is not supported for unix domain sockets
                if parsed.hostname == "unix" or not parsed.hostname:
                    path = name or "/tmp/redis.sock"
                    config["URL"] = f"unix://{path}"
                else:
                    config["URL"] = parsed.to_url()
            case _:
                config["URL"] = parsed.to_url()
        if parsed.qs:
            options.update(parsed.qs)
        convert_values(options)
        if options:
            config["OPTIONS"] = options
        # special handling of these
        config["TIMEOUT"] = options.pop("timeout", None)
        config["KEY_PREFIX"] = options.pop("key_prefix", None)
        return config
