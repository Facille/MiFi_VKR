import math


def circle_area(radius):
    area = math.pi * radius ** 2
    return area


def clamp(value, lower, upper):
    if value < lower:
        return lower
    if value > upper:
        return upper
    return value
