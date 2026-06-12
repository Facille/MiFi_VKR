def collect_even(numbers):
    result = []
    for number in numbers:
        if number % 2 == 0:
            result.append(number)
    return result


def double_items(items):
    result = []
    for item in items:
        result.append(item * 2)
    return result
