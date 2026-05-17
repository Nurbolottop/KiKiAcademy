from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

from apps.accounts.utils import normalize_phone


class PhoneBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        phone_raw = username or kwargs.get(UserModel.USERNAME_FIELD) or kwargs.get('phone')
        phone = normalize_phone(phone_raw)
        if not phone:
            return None

        try:
            user = UserModel._default_manager.get(phone=phone)
        except UserModel.DoesNotExist:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
