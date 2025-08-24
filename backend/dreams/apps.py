from django.apps import AppConfig


class DreamsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "dreams"

    def ready(self) -> None:
        """Import signal handlers when Django starts."""
        import dreams.signals  # noqa: F401
