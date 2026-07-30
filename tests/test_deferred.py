from types import SimpleNamespace

import pytest
from django.conf import LazySettings

from django_settings_env import Env
from django_settings_env.deferred import DeferredSetting


def deferred_setting(env, name=None, **kwargs):
    scope = SimpleNamespace(f_locals={})
    setting = DeferredSetting(env, scope=scope, kwargs={"name": name, **kwargs})
    if name is not None:
        scope.f_locals[name] = setting
    return setting


class TestDeferredSettingRendering:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [("value", "value"), (0, "0"), (False, "False"), (None, "")],
    )
    def test_renders_environment_and_default_values_as_strings(self, value, expected):
        setting = deferred_setting(
            Env(environ={}, readenv=False), "VALUE", default=value
        )

        assert str(setting) == expected
        assert f"{setting}" == expected

    def test_applies_string_formatting_to_the_resolved_value(self):
        setting = deferred_setting(
            Env(environ={"DJANGO_VALUE": "value"}, readenv=False), "VALUE"
        )

        assert f"{setting:>8}" == "   value"


class TestDeferredSettingResolution:
    def test_discovers_the_assigned_name_when_rendered_directly(self):
        env = Env(environ={"DJANGO_VALUE": "resolved"}, readenv=False)
        scope = SimpleNamespace(f_locals={})
        setting = DeferredSetting(env, scope=scope, kwargs={"name": None})
        scope.f_locals["VALUE"] = setting

        assert str(setting) == "resolved"

    def test_preserves_type_conversion_when_the_value_is_deferred(self):
        setting = deferred_setting(
            Env(environ={"DJANGO_RETRIES": "2"}, readenv=False),
            "RETRIES",
            type=int,
        )

        assert setting.setting("RETRIES") == 2
        assert str(setting) == "2"


class TestLazySettingsIntegration:
    def test_resolves_before_string_interpolation(self):
        setting = deferred_setting(
            Env(environ={"DJANGO_VALUE": "resolved"}, readenv=False), "VALUE"
        )
        settings = LazySettings()
        settings.configure(VALUE=setting)

        assert settings.VALUE == "resolved"
        assert f"value={settings.VALUE}" == "value=resolved"

    def test_isolates_same_named_settings_between_lazy_settings_instances(self):
        first = LazySettings()
        first.configure(
            VALUE=deferred_setting(
                Env(environ={"DJANGO_VALUE": "first"}, readenv=False), "VALUE"
            )
        )
        second = LazySettings()
        second.configure(
            VALUE=deferred_setting(
                Env(environ={"DJANGO_VALUE": "second"}, readenv=False), "VALUE"
            )
        )

        assert first.VALUE == "first"
        assert second.VALUE == "second"

    def test_caches_each_setting_once_per_lazy_settings_instance(self):
        class CountingEnv:
            def __init__(self, value):
                self.value = value
                self.calls = 0

            def __call__(self, *_args, **_kwargs):
                self.calls += 1
                return self.value

        first_env = CountingEnv("first")
        first = LazySettings()
        first.configure(VALUE=deferred_setting(first_env, "VALUE"))

        assert first.VALUE == "first"
        assert first.VALUE == "first"
        assert first_env.calls == 1

        second_env = CountingEnv("second")
        second = LazySettings()
        second.configure(VALUE=deferred_setting(second_env, "VALUE"))

        assert second.VALUE == "second"
        assert second_env.calls == 1
