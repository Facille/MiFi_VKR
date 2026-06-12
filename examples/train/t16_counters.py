def count_by_status(records):
    result = {}
    for record in records:
        status = record.get("status", "unknown")
        if status not in result:
            result[status] = 0
        result[status] += 1
    return result


def increment_counter(counter, key):
    if key not in counter:
        counter[key] = 0
    counter[key] += 1
    return counter
