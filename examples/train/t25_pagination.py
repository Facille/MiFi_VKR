def paginate(items, page, size):
    start = (page - 1) * size
    end = start + size
    return items[start:end]


def page_count(items, size):
    total = len(items)
    if total == 0:
        return 0
    return (total + size - 1) // size
