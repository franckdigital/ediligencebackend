from django.apps import AppConfig


class ProjetConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'projet'
    verbose_name = 'Gestion de Projets'

    def ready(self):
        import projet.signals  # noqa: F401
