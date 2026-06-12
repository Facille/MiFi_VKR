def countdown(count):
    result = []
    while count > 0:
        result.append(count)
        count -= 1
    return result


def find_first(items, target):
    index = 0
    while index < len(items):
        if items[index] == target:
            return index
        index += 1
    return -1
