import pytest
from django import VERSION as DJANGO_VERSION

from django_settings_env.plugin import plugin_tasks
from django_settings_env.plugin.plugin_tasks import TASKS_SCHEMES, TasksPlugin


@pytest.fixture
def tasks_plugin():
    return TasksPlugin()


@pytest.mark.skipif(DJANGO_VERSION < (6, 0), reason="Django tasks require Django 6")
@pytest.mark.parametrize("scheme", ["dummy", "immediate"])
def test_tasks_plugin_supports_django_backends(tasks_plugin, scheme):
    result = tasks_plugin.get_backend(f"{scheme}://")

    assert result["BACKEND"] == TASKS_SCHEMES[scheme]
    assert result["URL"] == f"{scheme}://"


@pytest.mark.skipif(DJANGO_VERSION < (6, 0), reason="Django tasks require Django 6")
@pytest.mark.parametrize(
    ("url", "match"),
    [
        ("unknown://localhost", "Unknown tasks scheme: unknown"),
        ("redis://localhost/default", "Unknown tasks scheme: redis"),
        ("://localhost", "Missing tasks scheme or url parse error"),
    ],
)
def test_tasks_plugin_rejects_unknown_or_missing_schemes(tasks_plugin, url, match):
    with pytest.raises(ValueError, match=match):
        tasks_plugin.get_backend(url)


def test_tasks_plugin_requires_django_6(monkeypatch, tasks_plugin):
    if DJANGO_VERSION >= (6, 0):
        monkeypatch.setattr(plugin_tasks, "DJANGO_VERSION", (5, 2))

    with pytest.raises(ValueError, match="tasks_url requires Django 6.0 or later"):
        tasks_plugin.get_backend("immediate://")
