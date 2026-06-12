class UserService:
    def __init__(self, repository):
        self.repository = repository

    def find_active(self):
        users = self.repository.list_users()
        return [user for user in users if user.active]


class ReportBuilder:
    def __init__(self):
        self.rows = []

    def add_row(self, row):
        self.rows.append(row)
        return len(self.rows)
