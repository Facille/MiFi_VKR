def normalize_names(names):
    result = []
    for name in names:
        result.append(name.strip().title())
    return result


def join_words(words):
    cleaned = []
    for word in words:
        cleaned.append(word.strip())
    return " ".join(cleaned)
