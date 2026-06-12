def consume_queue(queue):
    result = []
    while queue:
        item = queue.pop(0)
        result.append(item)
    return result
