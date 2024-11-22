from django.apps import AppConfig

class SalonConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'salon'
    label = 'salon_app'  # This ensures unique app label
