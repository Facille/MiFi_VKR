class Queue:
    def __init__(self):
        self.items = []

    def enqueue(self, item):
        self.items.append(item)
        return len(self.items)

    def dequeue(self):
        if not self.items:
            return None
        return self.items.pop(0)
