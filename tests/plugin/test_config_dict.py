from django_settings_env.plugin import ConfigDict


def test_assignment_keeps_false_zero_and_empty_string():
    config = ConfigDict()
    config["enabled"] = False
    config["timeout"] = 0
    config["name"] = ""

    assert config["enabled"] is False
    assert config["timeout"] == 0
    assert config["name"] == ""


def test_assignment_omits_none():
    config = ConfigDict()
    config["present"] = "yes"
    config["missing"] = None

    assert "missing" not in config
    assert config["present"] == "yes"


def test_assignment_of_none_removes_existing_key():
    config = ConfigDict()
    config["flag"] = False
    config["flag"] = None

    assert "flag" not in config


def test_update_keeps_false_and_omits_none():
    config = ConfigDict()
    config.update({"keep": False, "drop": None})

    assert config["keep"] is False
    assert "drop" not in config


def test_set_none_stores_explicit_none():
    config = ConfigDict()
    config.set_none("CONN_MAX_AGE")

    assert "CONN_MAX_AGE" in config
    assert config["CONN_MAX_AGE"] is None
