import pytest
from django_settings_env.plugin.plugin_email import EmailPlugin


def test_get_backend_valid_smtp():
    plugin = EmailPlugin()
    url = "smtp://user:pass@localhost:587"
    config = plugin.get_backend(url)
    assert config["EMAIL_BACKEND"] == "django.core.mail.backends.smtp.EmailBackend"
    assert config["EMAIL_HOST"] == "localhost"
    assert config["EMAIL_PORT"] == 587
    assert config["EMAIL_HOST_USER"] == "user"
    assert config["EMAIL_HOST_PASSWORD"] == "pass"


def test_get_backend_smtps():
    plugin = EmailPlugin()
    url = "smtps://user:pass@localhost"
    config = plugin.get_backend(url)
    assert config["EMAIL_BACKEND"] == "django.core.mail.backends.smtp.EmailBackend"
    assert config["EMAIL_HOST"] == "localhost"
    assert config["EMAIL_PORT"] == 587
    assert config["EMAIL_USE_TLS"] is True


def test_get_backend_smtp_ssl():
    plugin = EmailPlugin()
    url = "smtp+ssl://user:pass@localhost"
    config = plugin.get_backend(url)
    assert config["EMAIL_BACKEND"] == "django.core.mail.backends.smtp.EmailBackend"
    assert config["EMAIL_HOST"] == "localhost"
    assert config["EMAIL_PORT"] == 465
    assert config["EMAIL_USE_SSL"] is True


def test_get_backend_custom_port():
    plugin = EmailPlugin()
    url = "smtp://user:pass@localhost:2525"
    config = plugin.get_backend(url)
    assert config["EMAIL_PORT"] == 2525


def test_get_backend_invalid_scheme():
    plugin = EmailPlugin()
    url = "unknown://user:pass@localhost"
    with pytest.raises(ValueError, match="Unknown email scheme: unknown"):
        plugin.get_backend(url)


def test_get_backend_missing_scheme():
    plugin = EmailPlugin()
    url = "://user:pass@localhost"
    with pytest.raises(ValueError, match="Missing email scheme or url parse error"):
        plugin.get_backend(url)


def test_get_backend_with_options():
    plugin = EmailPlugin()
    url = "smtp://user:pass@localhost"
    options = {"EMAIL_TIMEOUT": 30}
    config = plugin.get_backend(url, options=options)
    assert config["EMAIL_TIMEOUT"] == 30


def test_get_backend_with_update_dict():
    plugin = EmailPlugin()
    url = "smtp://user:pass@localhost"
    update_dict = {}
    plugin.get_backend(url, update=update_dict)
    assert update_dict["EMAIL_HOST"] == "localhost"
    assert update_dict["EMAIL_PORT"] == 25
