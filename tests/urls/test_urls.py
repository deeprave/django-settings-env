import pytest
from urllib.parse import urlparse
from django_settings_env.urls.url import (
    ConfigDict,
    url_to_dict,
    dict_to_url,
    parse_url,
    parse_url_as_url,
)

from django_settings_env.urls.url import is_true


@pytest.mark.parametrize(
    "val, expected",
    [
        ("true", True),
        ("True", True),
        ("yes", True),
        ("1", True),
        ("false", False),
        ("False", False),
        ("no", False),
        ("0", False),
        ("", False),
        (None, False),
        (1, True),
        (0, False),
        ([], False),
        ([1, 2, 3], True),
        (b"true", True),
        (b"false", False),
        ("tru", True),
        ("yesplease", True),
        ("nope", False),
        (" 1", False),
        ("1 ", True),
        (b"yes", True),
        (b"no", False),
        (object(), True),
        (lambda: True, True),
        (lambda: False, True),
    ],
    ids=[
        "string_true",
        "string_True",
        "string_yes",
        "string_1",
        "string_false",
        "string_False",
        "string_no",
        "string_0",
        "empty_string",
        "None_value",
        "integer_1",
        "integer_0",
        "empty_list",
        "non_empty_list",
        "bytes_true",
        "bytes_false",
        # Edge cases
        "string_tru",
        "string_yesplease",
        "string_nope",
        "string_space_1",
        "string_1_space",
        "bytes_yes",
        "bytes_no",
        # Error cases
        "object_instance",
        "lambda_true",
        "lambda_false",
    ],
)
def test_is_true(val, expected):
    # Act
    result = is_true(val)

    # Assert
    assert result == expected


@pytest.mark.parametrize(
    "initial_data, scheme, expected_data, expected_scheme",
    [
        # Happy path tests
        ({"key1": "value1"}, "postgres", {"key1": "value1"}, "postgres"),
        ({"key2": "value2"}, "mysql", {"key2": "value2"}, "mysql"),
        # Edge cases
        ({}, None, {}, None),
        ({"key3": None}, "ftp", {}, "ftp"),
        # Error cases
        ({"key4": "value4"}, None, {"key4": "value4"}, None),
    ],
    ids=[
        "happy_path_postgres",
        "happy_path_mysql",
        "edge_case_empty_dict",
        "edge_case_none_value",
        "error_case_none_scheme",
    ],
)
def test_config_dict_initialization(initial_data, scheme, expected_data, expected_scheme):
    # Act
    config = ConfigDict(**initial_data, scheme=scheme)

    # Assert
    assert dict(config) == expected_data
    assert config.scheme == expected_scheme


@pytest.mark.parametrize(
    "initial_scheme, new_scheme, expected_scheme",
    [
        # Happy path tests
        ("http", "https", "https"),
        ("ftp", "sftp", "sftp"),
        # Edge cases
        (None, "http", "http"),
        ("http", None, None),
        # Error cases
        ("http", "", ""),
    ],
    ids=[
        "happy_path_http_to_https",
        "happy_path_ftp_to_sftp",
        "edge_case_none_to_http",
        "edge_case_http_to_none",
        "error_case_http_to_empty_string",
    ],
)
def test_config_dict_scheme_setter(initial_scheme, new_scheme, expected_scheme):
    # Arrange
    config = ConfigDict(scheme=initial_scheme)

    # Act
    config.scheme = new_scheme

    # Assert
    assert config.scheme == expected_scheme


@pytest.mark.parametrize(
    "parsed_url, expected",
    [
        (
            urlparse("postgresql://user:pass@host:1234/database"),
            ConfigDict(
                USER="user",
                PASSWORD="pass",
                HOST="host",
                PORT="1234",
                NAME="database",
                scheme="postgresql",
            ),
        ),
        (
            urlparse("mysql://host/database"),
            ConfigDict(
                USER=None,
                PASSWORD=None,
                HOST="host",
                PORT=None,
                NAME="database",
                scheme="mysql",
            ),
        ),
        (
            urlparse("http://host"),
            ConfigDict(
                USER=None,
                PASSWORD=None,
                HOST="host",
                PORT=None,
                NAME=None,
                scheme="http",
            ),
        ),
        (
            urlparse("https://user@host"),
            ConfigDict(
                USER="user",
                PASSWORD=None,
                HOST="host",
                PORT=None,
                NAME=None,
                scheme="https",
            ),
        ),
    ],
    ids=["happy_path", "no_user_pass_port", "no_path", "no_password"],
)
def test_url_to_dict(parsed_url, expected):
    # Act
    result = url_to_dict(parsed_url)

    # Assert
    assert result == expected


@pytest.mark.parametrize(
    "config, expected",
    [
        (
            ConfigDict(
                USER="user",
                PASSWORD="pass",
                HOST="host",
                PORT="1234",
                NAME="database",
                scheme="postgresql",
            ),
            "postgresql://user:pass@host:1234/database",
        ),
        (ConfigDict(HOST="host", NAME="path", scheme="http"), "http://host/path"),
        (ConfigDict(HOST="host", scheme="http"), "http://host"),
        (ConfigDict(USER="user", HOST="host", scheme="http"), "http://user@host"),
    ],
    ids=["happy_path", "no_user_pass_port", "no_path", "no_password"],
)
def test_dict_to_url(config, expected):
    # Act
    result = dict_to_url(config)

    # Assert
    assert result == expected


@pytest.mark.parametrize(
    "raw_url, backend, scheme_handler, options_handler, expected",
    [
        (
            "http://user:pass@host:1234/path",
            None,
            None,
            None,
            ConfigDict(
                USER="user",
                PASSWORD="pass",
                HOST="host",
                PORT="1234",
                NAME="path",
                scheme="http",
            ),
        ),
        (
            "http://host/path",
            None,
            None,
            None,
            ConfigDict(
                USER=None,
                PASSWORD=None,
                HOST="host",
                PORT=None,
                NAME="path",
                scheme="http",
            ),
        ),
        (
            "http://host",
            None,
            None,
            None,
            ConfigDict(
                USER=None,
                PASSWORD=None,
                HOST="host",
                PORT=None,
                NAME=None,
                scheme="http",
            ),
        ),
        (
            "http://user@host",
            None,
            None,
            None,
            ConfigDict(
                USER="user",
                PASSWORD=None,
                HOST="host",
                PORT=None,
                NAME=None,
                scheme="http",
            ),
        ),
        (
            "http://host1,http://host2",
            None,
            None,
            None,
            ConfigDict(
                scheme="http",
                BACKEND=None,
                LOCATION=["http://host1", "http://host2"],
            ),
        ),
    ],
    ids=["happy_path", "no_user_pass_port", "no_path", "no_password", "multiple_urls"],
)
def test_parse_url(raw_url, backend, scheme_handler, options_handler, expected):
    # Act
    result = parse_url(raw_url, backend, scheme_handler, options_handler)

    # Assert
    assert result == expected


@pytest.mark.parametrize(
    "raw_url, backend, scheme_handler, options_handler, expected",
    [
        # Happy path tests
        ("http://example.com", None, None, None, "http://example.com"),  # No handlers
        (
            "http://example.com",
            "custom_backend",
            None,
            None,
            "http://example.com",
        ),  # Custom backend
        (
            "http://example.com",
            None,
            lambda d, s: d,
            None,
            "http://example.com",
        ),  # Scheme handler
        (
            "http://example.com",
            None,
            None,
            lambda d, s: d,
            "http://example.com",
        ),  # Options handler
        # Edge cases
        ("", None, None, None, "unknown://"),  # Empty URL
        ("sqlite://:memory:", None, None, None, "sqlite://:memory:"),  # sqlite URL
        (
            "ftp://example.com",
            None,
            None,
            None,
            "ftp://example.com",
        ),  # Different scheme
        (
            "http://example.com:8080",
            None,
            None,
            None,
            "http://example.com:8080",
        ),  # URL with port
        # Error cases
        (None, None, None, None, TypeError),  # None as URL
        (123, None, None, None, TypeError),  # Non-string URL
    ],
    ids=[
        "no_handlers",
        "custom_backend",
        "scheme_handler",
        "options_handler",
        "empty_url",
        "sqlite_url",
        "different_scheme",
        "url_with_port",
        "none_as_url",
        "non_string_url",
    ],
)
def test_parse_url_as_url(raw_url, backend, scheme_handler, options_handler, expected):
    # Act
    # sourcery skip: no-conditionals-in-tests
    if isinstance(expected, type) and issubclass(expected, Exception):
        with pytest.raises(expected):
            parse_url_as_url(raw_url, backend, scheme_handler, options_handler)
    else:
        result = parse_url_as_url(raw_url, backend, scheme_handler, options_handler)

        # Assert
        assert result == expected
