def sort_by_name(items):
    result = sorted(items, key=lambda item: item["name"])
    return result


def top_scores(scores, limit):
    result = sorted(scores, reverse=True)
    return result[:limit]
