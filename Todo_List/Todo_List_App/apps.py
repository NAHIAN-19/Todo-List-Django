from django.apps import AppConfig


class Todo_List_AppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Todo_List_App'
    
    def ready(self):
        from .tokens import import_rest_framework_token
        import_rest_framework_token()