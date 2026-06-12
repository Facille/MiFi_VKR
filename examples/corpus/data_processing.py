def filter_active_users(users):
    active = []
    for user in users:
        if user.get("active"):
            active.append(user)
    return active


def count_scores(scores):
    total = 0
    for score in scores:
        total += score
    return total


def normalize_record(record):
    if record is None:
        return {}
    return {key: str(value).strip() for key, value in record.items()}
