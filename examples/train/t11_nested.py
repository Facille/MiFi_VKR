def group_by_type(items):
    result = {}
    for item in items:
        kind = item.get("type", "unknown")
        if kind not in result:
            result[kind] = []
        result[kind].append(item)
    return result
