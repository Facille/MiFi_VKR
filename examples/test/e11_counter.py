def count_words(words):
    result = {}
    for word in words:
        if word not in result:
            result[word] = 0
        result[word] += 1
    return result
