class TaskList:
    def __init__(self):
        self.tasks = []

    def add(self, task):
        self.tasks.append(task)
        return len(self.tasks)
