class Inventory:
    def __init__(self):
        self.items = {}

    def add_item(self, name, count):
        if name not in self.items:
            self.items[name] = 0
        self.items[name] += count
        return self.items[name]

    def has_item(self, name):
        return self.items.get(name, 0) > 0
