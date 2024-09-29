import pytest
from unittest.mock import MagicMock
from django_settings_env.deferred import DeferredSetting


@pytest.fixture
def mock_env():
    return MagicMock()


@pytest.fixture
def mock_scope():
    class MockScope:
        f_locals = {}

    return MockScope()


@pytest.mark.parametrize(
    "name, env_value, expected",
    [
        ("TEST_VAR", "value1", "value1"),
        ("ANOTHER_VAR", "value2", "value2"),
        ("MISSING_VAR", None, None),  # Edge case: variable not in env
    ],
    ids=["existing_var", "another_existing_var", "missing_var"],
)
def test_setting_happy_path(mock_env, mock_scope, name, env_value, expected):
    # Arrange
    mock_env.get.return_value = env_value
    mock_scope.f_locals[name] = None
    deferred_setting = DeferredSetting(mock_env, scope=mock_scope, kwargs={"name": name})

    # Act
    result = deferred_setting.setting(name)

    # Assert
    assert result == expected


@pytest.mark.parametrize(
    "name, expected",
    [
        (None, ""),  # Edge case: name is None
        ("", ""),  # Edge case: empty string as name
    ],
    ids=["none_name", "empty_name"],
)
def test_setting_edge_cases(mock_env, mock_scope, name, expected):
    # Arrange
    deferred_setting = DeferredSetting(mock_env, scope=mock_scope, kwargs={"name": name})

    # Act
    result = deferred_setting.setting(name)

    # Assert
    assert result == expected


@pytest.mark.parametrize(
    "name, env_value, expected_repr",
    [
        ("TEST_VAR", "value1", "value1"),
        ("ANOTHER_VAR", "value2", "value2"),
        ("MISSING_VAR", None, ""),  # Edge case: variable not in env
    ],
    ids=["repr_existing_var", "repr_another_existing_var", "repr_missing_var"],
)
def test_repr(mock_env, mock_scope, name, env_value, expected_repr):
    # Arrange
    mock_env.get.return_value = env_value
    deferred_setting = DeferredSetting(mock_env, scope=mock_scope, kwargs={"name": name})

    # Act
    result = repr(deferred_setting)

    # Assert
    assert result == expected_repr
