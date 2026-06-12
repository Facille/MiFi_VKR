from datetime import datetime


def parse_date(value):
    try:
        result = datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return None
    return result


def format_date(value):
    return value.strftime("%Y-%m-%d")
