def can_edit(user, document):
    if user.is_admin:
        return True
    if document.owner_id == user.id:
        return True
    return False


def should_retry(status_code):
    if status_code >= 500:
        return True
    return False
