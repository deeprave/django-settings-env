import pytest
from django_settings_env.plugin.plugin_search import SearchPlugin


@pytest.fixture
def search_plugin():
    return SearchPlugin()


def test_get_backend_valid_elasticsearch_dsl(search_plugin):
    url = "elasticsearch+dsl://localhost:9200/index_name"
    result = search_plugin.get_backend(url)
    assert "BACKEND" not in result
    assert result["hosts"] == "https://localhost:9200/index_name"
    assert result["NAME"] == "index_name"


def test_get_backend_valid_whoosh(search_plugin):
    url = "whoosh:///index_path"
    result = search_plugin.get_backend(url)
    assert result["BACKEND"] == "haystack.backends.whoosh_backend.WhooshEngine"
    assert result["NAME"] == "/index_path"


def test_get_backend_invalid_scheme(search_plugin):
    url = "unknown_scheme://invalid"
    with pytest.raises(ValueError) as exc:
        search_plugin.get_backend(url)
    assert "Missing search scheme" in str(exc.value)


def test_get_backend_options_conversion(search_plugin):
    url = "elasticsearch://localhost:9200/index_name"
    options = {
        "INCLUDE_SPELLING": "true",
        "EXCLUDED_INDEXES": "index1,index2",
        "BATCH_SIZE": "100",
    }
    result = search_plugin.get_backend(url, options=options)
    assert result["INCLUDE_SPELLING"] == "true"
    assert result["EXCLUDED_INDEXES"] == ["index1", "index2"]
    assert result["BATCH_SIZE"] == 100


def test_get_backend_elasticsearch_index_name_extraction(search_plugin):
    url = "elasticsearch://localhost:9200/index_name/segment"
    result = search_plugin.get_backend(url)
    assert result["INDEX_NAME"] == "segment"
    assert result["NAME"] == "index_name"


def test_get_backend_xapian(search_plugin):
    url = "xapian:///path_to_index"
    options = {"FLAGS": "some_flags"}
    result = search_plugin.get_backend(url, options=options)
    assert result["BACKEND"] == "haystack.backends.xapian_backend.XapianEngine"
    assert result["FLAGS"] == "some_flags"
    assert result["NAME"] == "path_to_index"


def test_get_backend_with_kwargs(search_plugin):
    url = "elasticsearch://localhost:9200/index_name"
    kwargs = {"backend": "elasticsearch", "options": {"KWARGS": {"key": "value"}}}
    result = search_plugin.get_backend(url, **kwargs)
    assert result["KWARGS"] == {"key": "value"}


def test_get_backend_with_timeout(search_plugin):
    url = "elasticsearch://localhost:9200/index_name"
    options = {"TIMEOUT": "30"}
    result = search_plugin.get_backend(url, options=options)
    assert result["TIMEOUT"] == 30


def test_get_backend_with_no_scheme(search_plugin):
    url = "//localhost:9200/index_name"
    with pytest.raises(ValueError) as exc:
        search_plugin.get_backend(url)
    assert "Unknown search scheme" in str(exc.value)
