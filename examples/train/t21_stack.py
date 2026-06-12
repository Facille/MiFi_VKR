class Stack:
    def __init__(self):
        self.items = []

    def push(self, item):
        self.items.append(item)
        return len(self.items)

    def pop(self):
        if not self.items:
            return None
        return self.items.pop()
