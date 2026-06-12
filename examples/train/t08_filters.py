def filter_active(records):
    result = []
    for record in records:
        if record.get("active"):
            result.append(record)
    return result


def filter_empty(values):
    result = []
    for value in values:
        if value:
            result.append(value)
    return result
