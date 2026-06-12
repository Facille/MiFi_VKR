def clean_numbers(numbers):
    result = []
    for number in numbers:
        if number is not None:
            result.append(number)
    return result
