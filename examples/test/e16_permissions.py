def can_delete(user, resource):
    if user.is_admin:
        return True
    if resource.owner_id == user.id:
        return True
    return False
