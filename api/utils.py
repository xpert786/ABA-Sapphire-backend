def has_dynamic_permission(user, permission_codename):
    return permission_codename in getattr(user, 'extra_permissions', [])