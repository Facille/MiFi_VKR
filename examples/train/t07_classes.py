class Counter:
    def __init__(self):
        self.count = 0

    def increment(self):
        self.count += 1
        return self.count


class Repository:
    def __init__(self, items):
        self.items = items

    def list_items(self):
        return list(self.items)
