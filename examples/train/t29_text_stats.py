def word_count(text):
    result = {}
    for word in text.split():
        normalized = word.lower()
        if normalized not in result:
            result[normalized] = 0
        result[normalized] += 1
    return result


def line_count(text):
    lines = text.splitlines()
    return len(lines)
