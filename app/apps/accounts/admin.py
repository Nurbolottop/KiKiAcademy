from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth import get_user_model

from apps.lms.models import UserProfile

from apps.accounts.forms import UserCreationForm, UserChangeForm
from apps.accounts.permissions import is_founder


User = get_user_model()


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    extra = 1
    max_num = 1
    filter_horizontal = ('roles',)
    fields = ('roles', 'status', 'fired_at')


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    add_form = UserCreationForm
    form = UserChangeForm
    model = User

    inlines = (UserProfileInline,)

    list_display = ('phone', 'first_name', 'last_name', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active')
    search_fields = ('phone', 'first_name', 'last_name')
    ordering = ('phone',)

    fieldsets = (
        (None, {'fields': ('phone', 'password')}),
        ('Персональные данные', {'fields': ('first_name', 'last_name', 'email')}),
        ('Права', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Важные даты', {'fields': ('last_login',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone', 'full_name', 'default_password'),
        }),
    )

    def has_view_permission(self, request, obj=None):
        return is_founder(request.user)

    def has_add_permission(self, request):
        return is_founder(request.user)

    def has_change_permission(self, request, obj=None):
        return is_founder(request.user)

    def has_delete_permission(self, request, obj=None):
        return is_founder(request.user)
