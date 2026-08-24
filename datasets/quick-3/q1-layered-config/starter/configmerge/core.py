class ConfigError(ValueError):
    pass


def resolve(*layers):
    """Combine configuration layers from lowest to highest precedence."""
    result = {}
    for layer in layers:
        if not isinstance(layer, dict):
            raise ConfigError("layers must be dictionaries")
        result.update(layer)
    return result
