from django.apps import AppConfig


class PincatchConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pincatch'
    verbose_name = 'Pages'

    def ready(self):
        """Import signals when the app is ready"""
        import pincatch.signals  # noqa
