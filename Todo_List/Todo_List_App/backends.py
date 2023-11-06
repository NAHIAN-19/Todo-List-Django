from django.contrib.auth.backends import ModelBackend
from .models import CustomUser
from django.contrib.auth.hashers import check_password
class RawPasswordModelBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = CustomUser.objects.get(username=username)
        except user.DoesNotExist:
            return None

        if user.password == password:
            return user
        return None

    def get_user(self, user_id):
        try:
            return CustomUser.objects.get(pk=user_id)
        except CustomUser.DoesNotExist:
            return None
