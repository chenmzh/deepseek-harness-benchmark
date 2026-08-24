from __future__ import annotations

from copy import deepcopy
from typing import Any


class ConfigError(ValueError):
    pass


def _validate(value: Any) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if not isinstance(key, str) or not key:
                raise ConfigError("configuration keys must be non-empty strings")
            _validate(child)
        return
    if isinstance(value, list):
        for child in value:
            _validate(child)
        return
    if value is None or isinstance(value, (str, int, float, bool)):
        return
    raise ConfigError(f"unsupported configuration value: {type(value).__name__}")


def _merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(base)
    for key, value in overlay.items():
        if value is None:
            result.pop(key, None)
        elif isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


def resolve(*layers: dict[str, Any]) -> dict[str, Any]:
    for layer in layers:
        if not isinstance(layer, dict):
            raise ConfigError("layers must be dictionaries")
        _validate(layer)
    result: dict[str, Any] = {}
    for layer in layers:
        result = _merge(result, layer)
    return result
