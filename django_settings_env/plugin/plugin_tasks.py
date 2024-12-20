from django.utils.version import get_complete_version

from . import EnvPlugin, ConfigDict, register_plugin, convert_values

DJANGO_VERSION = get_complete_version()

MODULE_PREFIX = (
    "django_tasks"
    if (DJANGO_VERSION[0] < 5 > DJANGO_VERSION[0]) or DJANGO_VERSION[1] < 2
    else "django.core.tasks"
)
REDIS_QUEUE_BACKEND = f"{MODULE_PREFIX}.backends.RedisQueue"
REDIS_BACKEND = f"{MODULE_PREFIX}.backends.RedisBackend"
DATABASE_BACKEND = f"{MODULE_PREFIX}.backends.database.DatabaseBackend"

TASKS_SCHEMES = {
    "redis": REDIS_BACKEND,
    "redis-queue": REDIS_QUEUE_BACKEND,
    "postgres": DATABASE_BACKEND,
    "postgresql": DATABASE_BACKEND,
    "mysql": DATABASE_BACKEND,
    "sqlite": DATABASE_BACKEND,
    "dummy": f"{MODULE_PREFIX}.backends.dummy.DummyBackend",
    "immediate": f"{MODULE_PREFIX}.backends.immediate.ImmediateBackend",
}


@register_plugin("tasks_url")
class TasksPlugin(EnvPlugin):
    """
    Plugin for handling database configuration
    """

    VAR = "CACHE_URL"
    CONTEXTS = ["caches"]

    def get_backend(self, url: str, **kwargs) -> object:
        parsed = self.parse_url(url, context=self.CONTEXTS)
        backend = kwargs.get("backend", None)
        options = ConfigDict(kwargs.get("options", {}))
        config = ConfigDict()

        if not parsed.scheme:
            raise ValueError("Missing tasks scheme or url parse error")
        try:
            config["BACKEND"] = backend or TASKS_SCHEMES[parsed.scheme]
        except KeyError as e:
            raise ValueError(f"Unknown tasks scheme: {parsed.scheme}") from e

        url_scheme = parsed.scheme
        name = parsed.path[1:] if parsed.path else None
        match parsed.scheme:
            case "redis" | "redis-queue":
                if parsed.hostname == "unix":
                    path = name or "tmp/redis.sock"
                    config["URL"] = f"unix:///{path}"
                else:
                    url_scheme = "redis"
            case "postgres" | "postgresql" | "mysql" | "sqlite":
                # which db to use
                config["DATABASE"] = parsed.path[1:] if parsed.path else "default"
                config["URL"] = parsed.to_url()
            case "dummy" | "immediate":
                pass  # no additional options

        config["URL"] = parsed.to_url(scheme=url_scheme)
        if parsed.qs:
            options.update(parsed.qs)
        convert_values(options)
        config["ENQUEUE_ON_COMMIT"] = options.pop("ENQUEUE_ON_COMMIT", None)
        config["QUEUES"] = options.pop("QUEUES", None)
        if options:
            config["BACKEND_OPTIONS"] = options
        return config
