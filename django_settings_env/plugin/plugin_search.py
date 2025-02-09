"""
This module provides URL parsing and query string handling for the search functionality.
"""

from typing import Any

from . import EnvPlugin, ConfigDict, register_plugin, convert_values

SEARCH_SCHEMES = {
    "elasticsearch": "haystack.backends.elasticsearch_backend.ElasticsearchSearchEngine",
    "elasticsearch2": "haystack.backends.elasticsearch2_backend.Elasticsearch2SearchEngine",
    "elasticsearch+dsl": None,
    "elasticsearch-dsl": None,
    "solr": "haystack.backends.solr_backend.SolrEngine",
    "whoosh": "haystack.backends.whoosh_backend.WhooshEngine",
    "xapian": "haystack.backends.xapian_backend.XapianEngine",
    "simple": "haystack.backends.simple_backend.SimpleEngine",
}


@register_plugin("search_url")
class SearchPlugin(EnvPlugin):
    """
    Plugin for handling search configuration
    """

    VAR = "SEARCH_URL"
    CONTEXTS = ["search"]

    def get_backend(self, url: str, **kwargs: Any) -> object:  # noqa: C901
        parsed = self.parse_url(url, context=self.CONTEXTS)
        engine = kwargs.get("engine", None)
        options = kwargs.get("options", {})
        config = ConfigDict()

        url_scheme = self.DEFAULT_SCHEME
        if not parsed.scheme:
            raise ValueError("Missing search scheme or url parse error")
        try:
            config["BACKEND"] = engine or SEARCH_SCHEMES[parsed.scheme]
        except KeyError as e:
            raise ValueError(f"Unknown search scheme: {parsed.scheme}") from e

        if parsed.qs:
            options.update(parsed.qs)
            url_scheme = options.pop("SCHEME", url_scheme)
        convert_values(options)
        # do some conversions
        if "EXCLUDED_INDEXES" in options:
            config["EXCLUDED_INDEXES"] = options.pop("EXCLUDED_INDEXES").split(",")
        config["INCLUDE_SPELLING"] = options.pop("INCLUDE_SPELLING", None)
        if "BATCH_SIZE" in options:
            config["BATCH_SIZE"] = options.pop("BATCH_SIZE")

        if parsed.path:
            path = parsed.path[1:]
            if path and path.endswith("/"):
                path = path[:-1]
            config["NAME"] = path

        config["KWARGS"] = options.get("KWARGS", None)
        config["TIMEOUT"] = options.get("TIMEOUT", None)
        config["INDEX_NAME"] = options.get("INDEX_NAME", None)
        match parsed.scheme:
            case "elasticsearch+dsl" | "elasticsearch-dsl":
                config["hosts"] = parsed.to_url(scheme=url_scheme)
            case "elasticsearch" | "elasticsearch2":
                if "NAME" in config:
                    # get index from the last segment of config["NAME"]
                    config["INDEX_NAME"] = config["NAME"].split("/")[-1]
                    # and remove it from config["NAME"]
                    config["NAME"] = "/".join(config["NAME"].split("/")[:-1])
            case "whoosh":
                config["STORAGE"] = options.get("STORAGE", None)
                config["POST_LIMIT"] = options.get("POST_LIMIT", None)
                config["NAME"] = f"/{config['NAME']}"
            case "xapian":
                config["FLAGS"] = options.get("FLAGS", None)
            case _:
                pass
        config["URL"] = parsed.to_url(scheme=url_scheme, name=None)

        return config
