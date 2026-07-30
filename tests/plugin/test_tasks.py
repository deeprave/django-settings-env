import pytest

from django_settings_env.plugin.plugin_tasks import TASKS_SCHEMES, TasksPlugin


@pytest.fixture
def tasks_plugin():
    return TasksPlugin()


@pytest.mark.parametrize("scheme", ["redis", "redis-queue"])
def test_tasks_plugin_supports_redis_backends(tasks_plugin, scheme):
    result = tasks_plugin.get_backend(f"{scheme}://localhost:6379/default")

    assert result["BACKEND"] == TASKS_SCHEMES[scheme]
    assert result["URL"] == "redis://localhost:6379/default"


def test_tasks_plugin_supports_redis_unix_sockets(tasks_plugin):
    result = tasks_plugin.get_backend("redis://unix/var/run/redis.sock")

    assert result["URL"] == "unix:///var/run/redis.sock"


@pytest.mark.parametrize("scheme", ["postgres", "postgresql", "mysql", "sqlite"])
def test_tasks_plugin_supports_database_backends(tasks_plugin, scheme):
    result = tasks_plugin.get_backend(f"{scheme}://localhost/application")

    assert result["BACKEND"] == TASKS_SCHEMES[scheme]
    assert result["DATABASE"] == "application"
    assert result["URL"] == f"{scheme}://localhost/application"


@pytest.mark.parametrize("scheme", ["dummy", "immediate"])
def test_tasks_plugin_supports_local_backends(tasks_plugin, scheme):
    result = tasks_plugin.get_backend(f"{scheme}://")

    assert result["BACKEND"] == TASKS_SCHEMES[scheme]
    assert result["URL"] == f"{scheme}://"


def test_tasks_plugin_merges_and_converts_options(tasks_plugin):
    result = tasks_plugin.get_backend(
        "redis://localhost/default?ENQUEUE_ON_COMMIT=true&QUEUES=high,low&timeout=30"
    )

    assert result["ENQUEUE_ON_COMMIT"] == "true"
    assert result["QUEUES"] == "high,low"
    assert result["BACKEND_OPTIONS"] == {"timeout": 30}


@pytest.mark.parametrize("url", ["unknown://localhost", "//localhost"])
def test_tasks_plugin_rejects_unknown_or_missing_schemes(tasks_plugin, url):
    with pytest.raises(ValueError):
        tasks_plugin.get_backend(url)


def test_tasks_plugin_falls_back_to_redis_and_preserves_unknown_qualifiers(
    tasks_plugin,
):
    result = tasks_plugin.get_backend("redis+cluster://localhost:6379/default")

    assert result["BACKEND"] == TASKS_SCHEMES["redis"]
    assert result["URL"] == "redis+cluster://localhost:6379/default"
