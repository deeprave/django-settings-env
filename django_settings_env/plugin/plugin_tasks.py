from django import VERSION as DJANGO_VERSION

from . import EnvPlugin, ConfigDict, register_plugin, convert_values

TASKS_SCHEMES = {
    "dummy": "django.tasks.backends.dummy.DummyBackend",
    "immediate": "django.tasks.backends.immediate.ImmediateBackend",
}


@register_plugin("tasks_url")
class TasksPlugin(EnvPlugin):
    """Plugin for handling task backend configuration."""

    VAR = "TASKS_URL"
    CONTEXTS = ["tasks"]

    def get_backend(self, url: str, **kwargs) -> object:
        if DJANGO_VERSION < (6, 0):
            raise ValueError("tasks_url requires Django 6.0 or later")

        parsed = self.parse_url(url, context=self.CONTEXTS)
        backend = kwargs.get("backend", None)
        options = ConfigDict(kwargs.get("options", {}))
        config = ConfigDict()

        if not parsed.scheme:
            raise ValueError("Missing tasks scheme or url parse error")
        try:
            scheme = self.resolve_scheme(parsed, TASKS_SCHEMES)
            config["BACKEND"] = backend or TASKS_SCHEMES[scheme]
        except KeyError as e:
            raise ValueError(f"Unknown tasks scheme: {parsed.scheme}") from e

        config["URL"] = parsed.to_url()
        if parsed.qs:
            options.update(parsed.qs)
        convert_values(options)
        config["ENQUEUE_ON_COMMIT"] = options.pop("ENQUEUE_ON_COMMIT", None)
        config["QUEUES"] = options.pop("QUEUES", None)
        if options:
            config["BACKEND_OPTIONS"] = options
        return config
