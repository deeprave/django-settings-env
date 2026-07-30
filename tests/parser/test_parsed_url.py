import pytest

from django_settings_env.parser import ParsedUrl, URLParser


def test_parsed_url_basic_attributes():
    parsed = ParsedUrl(
        scheme="https", username="user", password="pass", hostname="example.com", port=443
    )
    assert parsed.scheme == "https"
    assert parsed.username == "user"
    assert parsed.password == "pass"
    assert parsed.hostname == "example.com"
    assert parsed.port == 443


def test_parsed_url_with_path():
    parsed = ParsedUrl(
        scheme="http",
        username="user",
        password="pass",
        hostname="example.com",
        port=80,
        path="/test/path",
    )
    assert parsed.path == "/test/path"
    assert parsed.to_url() == "http://user:pass@example.com:80/test/path"


def test_parsed_url_with_query_string():
    parsed = ParsedUrl(
        scheme="https",
        username="user",
        password="pass",
        hostname="example.com",
        port=443,
        qs={"key1": "value1", "key2": "value2"},
    )
    assert parsed.qs == {"key1": "value1", "key2": "value2"}
    assert (
        parsed.to_url(qs=True)
        == "https://user:pass@example.com:443?key1=value1&key2=value2"
    )


def test_parsed_url_missing_optional_fields():
    parsed = ParsedUrl(scheme="https", hostname="example.com")
    assert parsed.to_url() == "https://example.com"


def test_parsed_url_with_only_required_fields():
    parsed = ParsedUrl(scheme="http", hostname="example.com")
    assert parsed.to_url() == "http://example.com"


def test_parsed_url_with_port_and_without_username_password():
    parsed = ParsedUrl(scheme="https", hostname="example.com", port=8443)
    assert parsed.to_url() == "https://example.com:8443"


def test_parsed_url_with_password_only():
    parsed = ParsedUrl(scheme="https", password="secret", hostname="example.com")

    assert parsed.to_url() == "https://:secret@example.com"
    assert str(parsed) == "<ParsedUrl: https://:secret@example.com"


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        (
            "postgresql+psycopg://user:pass@example.com:5432/app?sslmode=require",
            {
                "scheme": "postgresql+psycopg",
                "username": "user",
                "password": "pass",
                "hostname": "example.com",
                "port": 5432,
                "path": "/app",
                "qs": {"sslmode": "require"},
            },
        ),
        (
            "example.com/path",
            {
                "scheme": "https",
                "hostname": "example.com",
                "path": "/path",
            },
        ),
    ],
)
def test_url_parser_parses_real_urls(url, expected):
    parsed = URLParser()(url)

    for attribute, value in expected.items():
        assert getattr(parsed, attribute) == value


def test_url_parser_rejects_an_empty_url():
    with pytest.raises(ValueError, match="Invalid URL"):
        URLParser()("")


def test_url_parser_uses_its_configured_default_scheme():
    class CustomParser(URLParser):
        DEFAULT_SCHEME = "redis"

    assert CustomParser().default_scheme == "redis"


def test_parsed_url_exposes_qualified_scheme_dispatch_candidates():
    parsed = URLParser()("postgresql+psycopg+binary://example.com/application")

    assert parsed.scheme == "postgresql+psycopg+binary"
    assert parsed.base_scheme == "postgresql"
    assert parsed.scheme_qualifiers == ("psycopg", "binary")
    assert parsed.scheme_candidates == ("postgresql+psycopg+binary", "postgresql")
    assert parsed.to_url() == "postgresql+psycopg+binary://example.com/application"


def test_parsed_url_exposes_unqualified_scheme_dispatch_candidates():
    parsed = URLParser()("https://example.com")

    assert parsed.base_scheme == "https"
    assert parsed.scheme_qualifiers == ()
    assert parsed.scheme_candidates == ("https",)
