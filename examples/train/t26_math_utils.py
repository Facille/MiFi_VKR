def factorial(number):
    result = 1
    while number > 1:
        result *= number
        number -= 1
    return result


def power(base, exponent):
    result = 1
    while exponent > 0:
        result *= base
        exponent -= 1
    return result
