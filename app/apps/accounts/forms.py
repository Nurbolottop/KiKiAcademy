from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import ReadOnlyPasswordHashField

from apps.base.models import Settings
from apps.accounts.utils import normalize_phone


User = get_user_model()


class UserCreationForm(forms.ModelForm):
    phone = forms.CharField(label='Телефон')
    full_name = forms.CharField(label='ФИО', required=False)
    default_password = forms.CharField(label='Пароль по умолчанию', required=False, disabled=True)

    class Meta:
        model = User
        fields = ('phone',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        settings_obj = Settings.objects.first()
        self.fields['default_password'].initial = (
            settings_obj.default_staff_password
            if settings_obj and settings_obj.default_staff_password
            else getattr(settings, 'DEFAULT_STAFF_PASSWORD', '12345678')
        )

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        phone_norm = normalize_phone(phone)
        if not phone_norm:
            raise forms.ValidationError('Укажите номер телефона')
        if User.objects.filter(phone=phone_norm).exists():
            raise forms.ValidationError('Пользователь с таким телефоном уже существует')
        return phone_norm

    def save(self, commit=True):
        user = super().save(commit=False)
        user.phone = self.cleaned_data['phone']
        full_name = (self.cleaned_data.get('full_name') or '').strip()
        if full_name:
            parts = full_name.split(maxsplit=1)
            user.first_name = parts[0]
            user.last_name = parts[1] if len(parts) > 1 else ''
        settings_obj = Settings.objects.first()
        default_password = (
            settings_obj.default_staff_password
            if settings_obj and settings_obj.default_staff_password
            else getattr(settings, 'DEFAULT_STAFF_PASSWORD', '12345678')
        )
        user.set_password(default_password)
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField(label='Пароль')

    class Meta:
        model = User
        fields = ('phone', 'first_name', 'last_name', 'email', 'password', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        return normalize_phone(phone)
