import pytest
from django_settings_env.urls.email import (
    email_scheme_handler,
    email_options_handler,
    parse_email_url,
    EMAIL_SCHEMES,
)
from django_settings_env.urls.url import ConfigDict


@pytest.mark.parametrize(
    "config, scheme, backend, expected",
    [
        (
            {
                "NAME": "test",
                "USER": "user",
                "PASSWORD": "pass",
                "HOST": "host",
                "PORT": 587,
            },
            "smtp",
            None,
            ConfigDict(
                {
                    "EMAIL_BACKEND": EMAIL_SCHEMES["smtp"],
                    "EMAIL_FILE_PATH": "test",
                    "EMAIL_HOST_USER": "user",
                    "EMAIL_HOST_PASSWORD": "pass",
                    "EMAIL_HOST": "host",
                    "EMAIL_PORT": 587,
                }
            ),
        ),
        (
            {
                "NAME": "test",
                "USER": "user",
                "PASSWORD": "pass",
                "HOST": "host",
                "PORT": 465,
            },
            "smtp+ssl",
            None,
            ConfigDict(
                {
                    "EMAIL_BACKEND": EMAIL_SCHEMES["smtp+ssl"],
                    "EMAIL_FILE_PATH": "test",
                    "EMAIL_HOST_USER": "user",
                    "EMAIL_HOST_PASSWORD": "pass",
                    "EMAIL_HOST": "host",
                    "EMAIL_PORT": 465,
                    "EMAIL_USE_SSL": True,
                }
            ),
        ),
        (
            {
                "NAME": "test",
                "USER": "user",
                "PASSWORD": "pass",
                "HOST": "host",
                "PORT": 587,
            },
            "smtp+tls",
            None,
            ConfigDict(
                {
                    "EMAIL_BACKEND": EMAIL_SCHEMES["smtp+tls"],
                    "EMAIL_FILE_PATH": "test",
                    "EMAIL_HOST_USER": "user",
                    "EMAIL_HOST_PASSWORD": "pass",
                    "EMAIL_HOST": "host",
                    "EMAIL_PORT": 587,
                    "EMAIL_USE_TLS": True,
                }
            ),
        ),
    ],
    ids=["smtp_scheme", "smtp_ssl_scheme", "smtp_tls_scheme"],
)
def test_email_scheme_handler(config, scheme, backend, expected):
    # Act
    result = email_scheme_handler(config, scheme, backend)

    # Assert
    assert result == expected


@pytest.mark.parametrize(
    "config, qs, expected",
    [
        (
            {"EMAIL_BACKEND": "smtp"},
            "EMAIL_USE_TLS=True&EMAIL_PORT=587",
            {"EMAIL_BACKEND": "smtp", "EMAIL_USE_TLS": "True", "EMAIL_PORT": "587"},
        ),
        ({"EMAIL_BACKEND": "smtp"}, "", {"EMAIL_BACKEND": "smtp"}),
    ],
)
def test_email_options_handler(config, qs, expected):
    # Act
    result = email_options_handler(config, qs)

    # Assert
    assert result == expected


@pytest.mark.parametrize(
    "raw_url, backend, expected",
    [
        (
            "smtp://user:pass@host:587",
            None,
            ConfigDict(
                {
                    "EMAIL_BACKEND": EMAIL_SCHEMES["smtp"],
                    "EMAIL_HOST_USER": "user",
                    "EMAIL_HOST_PASSWORD": "pass",
                    "EMAIL_HOST": "host",
                    "EMAIL_PORT": 587,
                }
            ),
        ),
        (
            "smtp+ssl://user:pass@host:465",
            None,
            ConfigDict(
                {
                    "EMAIL_BACKEND": EMAIL_SCHEMES["smtp+ssl"],
                    "EMAIL_HOST_USER": "user",
                    "EMAIL_HOST_PASSWORD": "pass",
                    "EMAIL_HOST": "host",
                    "EMAIL_PORT": 465,
                    "EMAIL_USE_SSL": True,
                }
            ),
        ),
    ],
    ids=["smtp_url", "smtp_ssl_url"],
)
def test_parse_email_url(raw_url, backend, expected):
    # Act
    result = parse_email_url(raw_url, backend)

    # Assert
    assert result == expected


@pytest.mark.parametrize(
    "config, scheme, backend, expected_exception",
    [
        ({"NAME": "test"}, "unknown", None, ValueError),
    ],
)
def test_email_scheme_handler_errors(config, scheme, backend, expected_exception):
    # Act & Assert
    with pytest.raises(expected_exception):
        email_scheme_handler(config, scheme, backend)
