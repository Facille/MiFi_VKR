def invert_mapping(mapping):
    result = {}
    for key, value in mapping.items():
        result[value] = key
    return result


def select_keys(mapping, keys):
    result = {}
    for key in keys:
        if key in mapping:
            result[key] = mapping[key]
    return result
