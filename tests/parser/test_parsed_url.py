from django_settings_env.parser.__init__ import ParsedUrl


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
