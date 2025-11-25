from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        import core.serializers  # Force l'import au boot
        print("FORCED IMPORT core.serializers in AppConfig.ready()")
        print('APPS.PY: ready() called !')
        import core.signals  # Signaux généraux
        import core.signals_courrier  # Signaux pour les courriers
        import core.serializers  # Force l'import du serializer custom pour logs TOKEN DEBUG