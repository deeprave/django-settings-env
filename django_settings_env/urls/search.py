"""
This module provides URL parsing and query string handling for the search functionality.
"""

from typing import Dict, Optional, AnyStr
from urllib.parse import parse_qs

from .url import ConfigDict, parse_url, is_true, dict_to_url, remove_items

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


def search_scheme_handler(config: Dict, scheme: str, backend: Optional[AnyStr] = None):
    if not backend:
        if scheme in SEARCH_SCHEMES:
            backend = SEARCH_SCHEMES[scheme]
        else:
            raise ValueError(f"Unknown search scheme: {scheme}")

    return ConfigDict(config, scheme=scheme, ENGINE=backend)


def search_options_handler(config: Dict, qs: str) -> Dict:  # noqa: C901
    opts = dict(parse_qs(qs).items()) if qs else {}
    params = {key: values[0] for key, values in opts.items()}

    # ensure we have a schema
    config = ConfigDict(config)

    url_scheme = params.get("SCHEME", "https")
    if "EXCLUDED_INDEXES" in params:
        config["EXCLUDED_INDEXES"] = params["EXCLUDED_INDEXES"].split(",")
    if "INCLUDE_SPELLING" in params:
        config["INCLUDE_SPELLING"] = is_true(params["INCLUDE_SPELLING"])
    if "BATCH_SIZE" in params:
        config["BATCH_SIZE"] = int(params["BATCH_SIZE"])

    if config.get("NAME"):
        name = config.get("NAME")
        config["NAME"] = name[:-1] if name.endswith("/") else name

    match config.scheme:
        case "solr":
            if "KWARGS" in params:
                config["KWARGS"] = params["KWARGS"]
            if "TIMEOUT" in params:
                config["TIMEOUT"] = int(params["TIMEOUT"])
        case "elasticsearch+dsl" | "elasticsearch-dsl":
            config = remove_items(config, "NAME")
            config["hosts"] = dict_to_url(config, scheme=url_scheme)
            return remove_items(config, "HOST", "PORT")
        case "elasticsearch" | "elasticsearch2":
            if "KWARGS" in params:
                config["KWARGS"] = params["KWARGS"]
            if "TIMEOUT" in params:
                config["TIMEOUT"] = int(params["TIMEOUT"])
            if "INDEX_NAME" in params:
                config["INDEX_NAME"] = params["INDEX_NAME"]
            elif "NAME" in config:
                # get index from the last segment of config["NAME"]
                config["INDEX_NAME"] = config["NAME"].split("/")[-1]
                # and remove it from config["NAME"]
                config["NAME"] = "/".join(config["NAME"].split("/")[:-1])
            else:
                raise ValueError("Missing index name for Elasticsearch")
        case "whoosh":
            if "STORAGE" in params:
                config["STORAGE"] = params["STORAGE"]
            if "POST_LIMIT" in params:
                config["POST_LIMIT"] = int(params["POST_LIMIT"])
            config["NAME"] = f"/{config['NAME']}"
        case "xapian":
            if "FLAGS" in params:
                config["FLAGS"] = params["FLAGS"]

    config["URL"] = dict_to_url(config, scheme=url_scheme)
    return remove_items(config, "HOST", "PORT", "NAME")


def parse_search_url(raw_url: AnyStr, backend: Optional[AnyStr] = None):
    return parse_url(raw_url, backend, search_scheme_handler, search_options_handler)
