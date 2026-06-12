def build_index(items):
    result = {}
    for item in items:
        result[item["id"]] = item
    return result
