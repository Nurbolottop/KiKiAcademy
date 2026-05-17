from django.apps import AppConfig


class LmsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.lms'

    def ready(self):
        from apps.lms import signals  # noqa: F401
