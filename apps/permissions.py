LEVEL_COACH = 1
LEVEL_SUPERCOACH = 2
LEVEL_USER = 3


def has_permission(user, level=None):
    if level == LEVEL_COACH:
        return is_coach(user)
    elif level == LEVEL_SUPERCOACH:
        return is_supercoach(user)
    elif level == LEVEL_USER:
        return user.is_authenticated
    else:
        return False


def is_coach(user):
    return user.is_coach or user.is_supercoach or user.is_superuser


def is_supercoach(user):
    return user.is_supercoach or user.is_superuser


class RequiresPermissionDecorator(object):

    def __init__(self):
        pass

    def __call__(self, *args, **kwargs):
        pass

def requires_permission():
    pass
