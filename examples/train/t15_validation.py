def validate_email(email):
    if "@" not in email:
        return False
    if "." not in email:
        return False
    return True


def require_non_empty(value):
    if not value:
        raise ValueError("value must not be empty")
    return value
