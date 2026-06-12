def safe_float(value):
    try:
        number = float(value)
    except ValueError:
        return 0.0
    return number
