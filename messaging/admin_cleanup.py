from django.contrib import admin
from django.apps import apps

# List of models to remove from admin
unused_models = [
    'auth.Group',
    'authtoken.TokenProxy',
    'api.UserRoleAssignment',
    'api.UserPermission',
    'ocean.ChatMessage',
    'ocean.Alert',
    'scheduler.Session',
    'scheduler.SessionLog',
    'scheduler.TimeTracker',
    'messaging.Message',
    'token_blacklist.OutstandingToken',
    'token_blacklist.BlacklistedToken',
]

for label in unused_models:
    try:
        app_label, model_name = label.split(".")
        model = apps.get_model(app_label, model_name)
        admin.site.unregister(model)
        print(f"Unregistered {label} from admin.")
    except admin.sites.NotRegistered:
        print(f"{label} was not registered.")
    except LookupError:
        print(f"{label} model not found.")
