class History:
    def __init__(self):
        self.items = []

    def add(self, item):
        self.items.append(item)
        return len(self.items)
