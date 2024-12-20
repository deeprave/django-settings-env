from . import EnvPlugin, ConfigDict, register_plugin

EMAIL_AMAZON_SES = "django_ses.SESBackend"
EMAIL_SMTP = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_SCHEMES = {
    "smtp": EMAIL_SMTP,
    "smtps": EMAIL_SMTP,
    "smtp+tls": EMAIL_SMTP,
    "smtp+ssl": EMAIL_SMTP,
    "consolemail": "django.core.mail.backends.console.EmailBackend",
    "filemail": "django.core.mail.backends.filebased.EmailBackend",
    "memorymail": "django.core.mail.backends.locmem.EmailBackend",
    "dummymail": "django.core.mail.backends.dummy.EmailBackend",
    "amazonses": EMAIL_AMAZON_SES,
    "amazon-ses": EMAIL_AMAZON_SES,
}


@register_plugin("email_url")
class EmailPlugin(EnvPlugin):
    """
    Plugin for handling email configuration
    """

    VAR = "EMAIL_URL"
    CONTEXTS = ["email"]

    def get_backend(self, url: str, **kwargs) -> object:
        parsed = self.parse_url(url, context=self.CONTEXTS)
        backend = kwargs.get("backend", None)
        options = kwargs.get("options", {})
        config = ConfigDict()

        if not parsed.scheme:
            raise ValueError("Missing email scheme or url parse error")
        try:
            config["EMAIL_BACKEND"] = backend or EMAIL_SCHEMES[parsed.scheme]
        except KeyError as e:
            raise ValueError(f"Unknown email scheme: {parsed.scheme}") from e

        config.update(options)
        default_port = 25
        if parsed.scheme in {"smtps", "smtp+tls"}:
            config["EMAIL_USE_TLS"] = True
            default_port = 587
        elif parsed.scheme == "smtp+ssl":
            config["EMAIL_USE_SSL"] = True
            default_port = 465

        config.update(
            {
                "EMAIL_FILE_PATH": parsed.path[1:] if parsed.path else None,
                "EMAIL_HOST_USER": parsed.username,
                "EMAIL_HOST_PASSWORD": parsed.password,
                "EMAIL_HOST": parsed.hostname or "localhost",
                "EMAIL_PORT": int(parsed.port) if parsed.port else default_port,
            }
        )
        if parsed.qs:
            config.update(parsed.qs)

        # if update=globals() can update settings module directly
        # if update=settings_class.__dict__ if using class-based settings
        if (update := kwargs.get("update", None)) is not None:
            if isinstance(update, dict):
                update.update(config)

        return config
