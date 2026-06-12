def find_user(users, user_id):
    for user in users:
        if user.get("id") == user_id:
            return user
    return None


def contains_name(users, name):
    for user in users:
        if user.get("name") == name:
            return True
    return False
