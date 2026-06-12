def calculate_sum(numbers):
    total = 0
    for number in numbers:
        total += number
    return total


def average(numbers):
    total = calculate_sum(numbers)
    if not numbers:
        return 0
    return total / len(numbers)
