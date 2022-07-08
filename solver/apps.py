from django.apps import AppConfig


class SolverConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "solver"

    def ready(self):
        from . import signals  # noqa: F401
