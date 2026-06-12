def names_to_lengths(names):
    result = {}
    for name in names:
        result[name] = len(name)
    return result


def unique_items(items):
    result = set()
    for item in items:
        result.add(item)
    return result
