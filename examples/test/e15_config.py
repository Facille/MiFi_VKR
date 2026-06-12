def apply_defaults(config, defaults):
    result = dict(defaults)
    for key, value in config.items():
        result[key] = value
    return result
