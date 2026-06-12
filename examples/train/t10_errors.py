def parse_int(value):
    try:
        number = int(value)
    except ValueError:
        return None
    return number


def require_value(value):
    if value is None:
        raise ValueError("value is required")
    return value
