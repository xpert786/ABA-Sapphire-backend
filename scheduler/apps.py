from django.apps import AppConfig


class SchedulerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'scheduler'
    
    def ready(self):
        # Import signals to ensure they're registered
        import scheduler.models  # This will register the signals