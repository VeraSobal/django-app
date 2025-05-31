from django.apps import AppConfig


class OrdertrackAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ordertrack_app'

    def ready(self):
        from . import signals
