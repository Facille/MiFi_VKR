class UserService:
    def __init__(self, repository):
        self.repository = repository

    def get_names(self):
        users = self.repository.list_users()
        result = []
        for user in users:
            result.append(user.name)
        return result
