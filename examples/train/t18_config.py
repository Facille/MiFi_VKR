def merge_config(defaults, overrides):
    result = dict(defaults)
    for key, value in overrides.items():
        result[key] = value
    return result


def get_config_value(config, key, default=None):
    if key in config:
        return config[key]
    return default
