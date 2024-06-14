from typing import Dict, Optional, AnyStr
from urllib.parse import parse_qs

from .url import parse_url, ConfigDict

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


def email_scheme_handler(config: Dict, scheme: str, backend: Optional[AnyStr] = None):
    if not backend:
        if scheme in EMAIL_SCHEMES:
            backend = EMAIL_SCHEMES[scheme]
        else:
            raise ValueError(f"Unknown email scheme: {scheme}")

    config = ConfigDict(
        scheme=scheme,
        **{
            "EMAIL_BACKEND": backend,
            "EMAIL_FILE_PATH": config.get("NAME"),
            "EMAIL_HOST_USER": config.get("USER"),
            "EMAIL_HOST_PASSWORD": config.get("PASSWORD"),
            "EMAIL_HOST": config.get("HOST", "localhost"),
            "EMAIL_PORT": int(config["PORT"]) if "PORT" in config else 25,
        },
    )

    if scheme in {"smtps", "smtp+tls"}:
        config["EMAIL_USE_TLS"] = True
    elif scheme == "smtp+ssl":
        config["EMAIL_USE_SSL"] = True

    return config


def email_options_handler(config: Dict, qs: str) -> Dict:
    opts = dict(parse_qs(qs).items()) if qs else {}
    email_opts = {key: values[0] for key, values in opts.items()}
    config |= email_opts
    return config


def parse_email_url(raw_url: AnyStr, backend: Optional[AnyStr] = None):
    return parse_url(raw_url, backend, email_scheme_handler, email_options_handler)
